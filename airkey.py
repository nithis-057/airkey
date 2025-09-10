import sys
import cv2
import time
import mediapipe as mp
from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtCore import Qt, QTimer, QRect
from PySide6.QtGui import QPainter, QColor, QFont, QImage, QMouseEvent
from pynput.keyboard import Controller
import pygame   

from overlay_native import make_click_through_and_overlay_qt

typed_text = ""
shift_active = False
keyboard = Controller()


pygame.mixer.init()
click_sound = pygame.mixer.Sound("click.wav")

def play_click():
    click_sound.play()


keys = [
    ["Q","W","E","R","T","Y","U","I","O","P"],
    ["A","S","D","F","G","H","J","K","L"],
    ["Z","X","C","V","B","N","M"],
    ["Shift","Space","Backspace","ClearAll"]
]

KEY_WIDTH = 80
KEY_HEIGHT = 80
KEY_SPACING = 15
OFFSET_X = 50
OFFSET_Y = 100

PRESS_THRESHOLD = 0.5
CLEARALL_THRESHOLD = 2.0

highlighted_keys = {}
press_state = {"left": {"key": None, "start": 0}, "right": {"key": None, "start": 0}}

EXIT_RECT = QRect(1100, 30, 150, 50)

#mediapipe_handles 
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7)

def process_key(key):
    global typed_text, shift_active
    play_click()   

    if key == "Space":
        typed_text += " "
        keyboard.press(" ")
        keyboard.release(" ")
    elif key == "Backspace":
        typed_text = typed_text[:-1]
        keyboard.press("\b")
        keyboard.release("\b")
    elif key == "ClearAll":
        typed_text = ""
    elif key == "Shift":
        shift_active = True
    else:
        char = key.upper() if shift_active else key.lower()
        typed_text += char
        keyboard.press(char)
        keyboard.release(char)
        if shift_active:
            shift_active = False

def get_key_at(x, y):
    row_y = OFFSET_Y
    for row in keys:
        row_x = OFFSET_X
        for key in row:
            w = KEY_WIDTH * 3 if key == "Space" else KEY_WIDTH
            if row_x <= x <= row_x + w and row_y <= y <= row_y + KEY_HEIGHT:
                return key
            row_x += w + KEY_SPACING
        row_y += KEY_HEIGHT + KEY_SPACING
    return None

class AirKeyOverlay(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AirKey Overlay")
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setWindowFlag(Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setGeometry(0, 0, 1280, 720)

        # Camera
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            print("Cannot open camera.")
            sys.exit()

        self.frame = None

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

    def update_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return
        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = hands.process(rgb)

        highlighted_keys.clear()

        if result.multi_hand_landmarks and result.multi_handedness:
            for hand_landmarks, handedness in zip(result.multi_hand_landmarks, result.multi_handedness):
                h, w, _ = frame.shape
                x = int(hand_landmarks.landmark[8].x * w)
                y = int(hand_landmarks.landmark[8].y * h)

                label = handedness.classification[0].label.lower()

                key = get_key_at(x, y)
                if key:
                    highlighted_keys[key] = {"start": press_state[label]["start"] or time.time()}
                    threshold = CLEARALL_THRESHOLD if key == "ClearAll" else PRESS_THRESHOLD

                    if press_state[label]["key"] != key:
                        press_state[label]["key"] = key
                        press_state[label]["start"] = time.time()
                    else:
                        if time.time() - press_state[label]["start"] > threshold:
                            process_key(key)
                            press_state[label]["key"] = None
                else:
                    press_state[label]["key"] = None

                mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

        self.frame = frame
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        #umm...I'm pretty sure this is for camera
        if self.frame is not None:
            h, w, ch = self.frame.shape
            img = QImage(self.frame.data, w, h, ch * w, QImage.Format_RGB888)
            painter.drawImage(0, 0, img)

        #the search bar like thing ig
        painter.setBrush(QColor(50, 50, 50, 180))
        painter.drawRect(50, 30, 1000, 50)
        painter.setFont(QFont("Arial", 18))
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(60, 65, typed_text)

        
        painter.setBrush(QColor(200, 0, 0, 180))
        painter.drawRect(EXIT_RECT)
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(EXIT_RECT.x() + 40, EXIT_RECT.y() + 35, "Exit")

        y = OFFSET_Y
        for row in keys:
            x = OFFSET_X
            for key in row:
                w = KEY_WIDTH * 3 if key == "Space" else KEY_WIDTH
                color = QColor(200, 200, 200, 180)
                if key in highlighted_keys:
                    held_time = time.time() - highlighted_keys[key]["start"]
                    threshold = CLEARALL_THRESHOLD if key == "ClearAll" else PRESS_THRESHOLD
                    color = QColor(0, 255, 0, 180) if held_time > threshold else QColor(0, 255, 255, 180)

                painter.setBrush(color)
                painter.drawRect(x, y, w, KEY_HEIGHT)
                painter.setPen(QColor(255, 255, 255))
                painter.drawText(x + 10, y + 50, key)
                x += w + KEY_SPACING
            y += KEY_HEIGHT + KEY_SPACING

    def closeEvent(self, event):
        self.cap.release()

    def mousePressEvent(self, event: QMouseEvent):
        if EXIT_RECT.contains(event.pos()):
            QApplication.quit()
        else:
            event.ignore()  

#finally the MAIN main function
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AirKeyOverlay()
    window.showFullScreen()

    make_click_through_and_overlay_qt(window)

    sys.exit(app.exec())
