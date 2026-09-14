from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

class WindowEngine:
    @staticmethod
    def apply_window_flags(widget):
        widget.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.X11BypassWindowManagerHint |
            Qt.WindowType.Tool |
            Qt.WindowType.WindowDoesNotAcceptFocus
        )
        widget.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        widget.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)

    @staticmethod
    def center_top_geometry(widget, width, height):
        screen = QApplication.primaryScreen()
        if screen:
            screen_geo = screen.geometry()
            x = (screen_geo.width() - width) // 2
            widget.setGeometry(x, 0, width, height)
