import sys
import threading
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPainter, QColor, QPen

class JarvisHUD(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(140, 140)
        screen = QApplication.primaryScreen().geometry()
        self.move(screen.width() - 160, screen.height() - 200)
        self.state = "idle"
        self.pulse = 0
        self.timer = QTimer(); self.timer.timeout.connect(self._tick); self.timer.start(50)

    def set_state(self, s):
        self.state = s

    def _tick(self):
        self.pulse = (self.pulse + 5) % 360
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        colors = {"idle": QColor(0,180,255,120), "listen": QColor(0,255,100,200),
                  "think": QColor(255,180,0,200), "speak": QColor(255,0,180,200)}
        c = colors.get(self.state, colors["idle"])
        pen = QPen(c, 4); p.setPen(pen)
        import math
        r = 50 + int(10 * math.sin(math.radians(self.pulse)))
        p.drawEllipse(70 - r, 70 - r, r*2, r*2)

_hud = None

def start_hud():
    def run():
        global _hud
        app = QApplication(sys.argv)
        _hud = JarvisHUD()
        _hud.show()
        app.exec()
    threading.Thread(target=run, daemon=True).start()

def set_hud(state):
    global _hud
    if _hud: _hud.set_state(state)