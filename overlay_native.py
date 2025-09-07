import sys

def make_click_through_and_overlay_qt(qt_window):
    """
    Elevate a PySide6 QWidget to a true overlay and make it click-through
    (so underlying apps receive mouse/trackpad input).
    Works per-platform by calling native APIs on the underlying window.
    """
    if sys.platform.startswith("win"):
        _win_make_layered_clickthrough(qt_window)
    elif sys.platform == "darwin":
        _mac_make_overlay_ignore_mouse(qt_window)
    else:
        print("Overlay: native click-through not implemented for this OS.")

# -------- Windows (pywin32) ----------
def _win_make_layered_clickthrough(qt_window):
    # Get HWND from Qt
    hwnd = qt_window.winId().__int__()

    import win32gui, win32con

    # Current style
    ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)

    # Add layered + transparent (click-through) + toolwindow (no taskbar)
    ex_style |= win32con.WS_EX_LAYERED | win32con.WS_EX_TRANSPARENT | win32con.WS_EX_TOOLWINDOW
    win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, ex_style)

    # Optional: set alpha (255 fully opaque—your painting controls actual visuals)
    # You can keep it opaque; the window has a translucent background from Qt.
    win32gui.SetLayeredWindowAttributes(hwnd, 0, 255, win32con.LWA_ALPHA)

    # Keep it top-most
    win32gui.SetWindowPos(
        hwnd, win32con.HWND_TOPMOST,
        0, 0, 0, 0,
        win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE
    )

# -------- macOS (PyObjC) -------------
def _mac_make_overlay_ignore_mouse(qt_window):
    # Get NSWindow from Qt
    # For PySide6 on macOS this returns an NSView pointer; get the window via valueForKey_.
    from ctypes import c_void_p
    from PySide6.QtGui import QWindow
    from PySide6.QtWidgets import QWidget
    import objc
    from AppKit import NSApp, NSWindow, NSApplication, NSFloatingWindowLevel, NSScreenSaverWindowLevel

    # Ensure we have a native window handle
    qt_window.setWindowFlag(qt_window.windowFlags() | qt_window.windowFlags())
    qt_window.show()  # must be shown to have a native handle

    # Pull NSWindow*
    # Trick: get the QWindow, then its NSWindow using sip/objc bridge from winId.
    # PySide6 returns a cocoa pointer via winId(); convert to NSView then window()
    nsview_ptr = int(qt_window.winId())  # NSView*
    NSView = objc.lookUpClass('NSView')
    nsview = objc.objc_object(c_void_p=nsview_ptr)
    nswindow = nsview.window()

    # Make it ignore mouse so clicks go through
    nswindow.setIgnoresMouseEvents_(True)

    # Transparent + no shadow
    nswindow.setOpaque_(False)
    nswindow.setHasShadow_(False)
    nswindow.setBackgroundColor_(objc.lookUpClass("NSColor").clearColor())

    # Put it above almost everything
    nswindow.setLevel_(NSScreenSaverWindowLevel)  # higher than normal floating windows

    # Also keep on all spaces/desktops
    # NSWindowCollectionBehaviorCanJoinAllSpaces = 1 << 0
    nswindow.setCollectionBehavior_(1 << 0)
