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

text = ""
shift = False
kb = Controller()

pygame.mixer.init()
click = pygame.mixer.Sound("click.wav")

def play_click():
    click.play()

layout = [
    ["Q","W","E","R","T","Y","U","I","O","P"],
    ["A","S","D","F","G","H","J","K","L"],
    ["Z","X","C","V","B","N","M"],
    ["Shift","Space","Backspace","ClearAll"]
]

KW, KH, SP = 80, 80, 15
OX, OY = 50, 100

THRESH, CLEAR_THRESH = 0.5, 2.0

highlights = {}
press = {"left": {"key": None, "start": 0}, "right": {"key": None, "start": 0}}

EXIT = QRect(1100, 30, 150, 50)

mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils
hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7)

def handle_key(k):
    global text, shift
    play_click()
    if k == "Space":
        text += " "
        kb.press(" "); kb.release(" ")
    elif k == "Backspace":
        text = text[:-1]
        kb.press("\b"); kb.release("\b")
    elif k == "ClearAll":
        text = ""
    elif k == "Shift":
        shift = True
    else:
        c = k.upper() if shift else k.lower()
        text += c
        kb.press(c); kb.release(c)
        if shift: shift = False

def key_at(x, y):
    ry = OY
    for row in layout:
        rx = OX
        for k in row:
            w = KW * 3 if k == "Space" else KW
            if rx <= x <= rx + w and ry <= y <= ry + KH:
                return k
            rx += w + SP
        ry += KH + SP
    return None

class Overlay(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AirKey Overlay")
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setWindowFlag(Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setGeometry(0, 0, 1280, 720)
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            print("No camera."); sys.exit()
        self.frame = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

    def update_frame(self):
        ok, frame = self.cap.read()
        if not ok: return
        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        res = hands.process(rgb)
        highlights.clear()
        if res.multi_hand_landmarks and res.multi_handedness:
            for lm, hd in zip(res.multi_hand_landmarks, res.multi_handedness):
                h, w, _ = frame.shape
                x, y = int(lm.landmark[8].x * w), int(lm.landmark[8].y * h)
                label = hd.classification[0].label.lower()
                k = key_at(x, y)
                if k:
                    highlights[k] = {"start": press[label]["start"] or time.time()}
                    th = CLEAR_THRESH if k == "ClearAll" else THRESH
                    if press[label]["key"] != k:
                        press[label]["key"] = k
                        press[label]["start"] = time.time()
                    else:
                        if time.time() - press[label]["start"] > th:
                            handle_key(k)
                            press[label]["key"] = None
                else:
                    press[label]["key"] = None
                mp_draw.draw_landmarks(frame, lm, mp_hands.HAND_CONNECTIONS)
        self.frame = frame
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        if self.frame is not None:
            h, w, ch = self.frame.shape
            img = QImage(self.frame.data, w, h, ch * w, QImage.Format_RGB888)
            p.drawImage(0, 0, img)
        p.setBrush(QColor(50, 50, 50, 180))
        p.drawRect(50, 30, 1000, 50)
        p.setFont(QFont("Arial", 18))
        p.setPen(QColor(255, 255, 255))
        p.drawText(60, 65, text)
        p.setBrush(QColor(200, 0, 0, 180))
        p.drawRect(EXIT)
        p.setPen(QColor(255, 255, 255))
        p.drawText(EXIT.x() + 40, EXIT.y() + 35, "Exit")
        y = OY
        for row in layout:
            x = OX
            for k in row:
                w = KW * 3 if k == "Space" else KW
                color = QColor(200, 200, 200, 180)
                if k in highlights:
                    held = time.time() - highlights[k]["start"]
                    th = CLEAR_THRESH if k == "ClearAll" else THRESH
                    color = QColor(0, 255, 0, 180) if held > th else QColor(0, 255, 255, 180)
                p.setBrush(color)
                p.drawRect(x, y, w, KH)
                p.setPen(QColor(255, 255, 255))
                p.drawText(x + 10, y + 50, k)
                x += w + SP
            y += KH + SP

    def closeEvent(self, e):
        self.cap.release()

    def mousePressEvent(self, e: QMouseEvent):
        if EXIT.contains(e.pos()):
            QApplication.quit()
        else:
            e.ignore()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = Overlay()
    win.showFullScreen()
    make_click_through_and_overlay_qt(win)
    sys.exit(app.exec())
