import sys
import keyboard
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QSlider,
    QPushButton, QLabel, QColorDialog, QComboBox,
    QSystemTrayIcon, QMenu, QHBoxLayout, QFrame
)
from PyQt5.QtGui import QPainter, QColor, QIcon, QPainterPath, QCursor, QRadialGradient, QBrush, QFont
from PyQt5.QtCore import Qt, QRect, QTimer, QPoint, QRectF, QPointF

class Spotlight(QWidget):
    def __init__(self):
        super().__init__()

        # ---------- Settings ----------
        self.shape = "Circle"
        self.spot_size = 250
        self.feather_amount = 50
        self.follow_speed = 0.15
        self.overlay_color = QColor(10, 10, 15, 230) # Deeper, midnight blue-black
        self.is_visible = True
        
        # ---------- State ----------
        self.locked = False
        self.current_pos = QPointF(0, 0)
        self.target_pos = QPointF(0, 0)

        self.init_window()
        self.init_ui_panel()
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_spotlight_pos)
        self.timer.start(10)

        self.init_tray()
        self.init_hotkeys()

    def init_window(self):
        self.setWindowIcon(QIcon("icon.png")) # Make sure icon.png is in your folder
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool | Qt.WindowTransparentForInput)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.showFullScreen()

    def init_ui_panel(self):
        self.panel = QWidget()
        self.panel.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)
        self.panel.setFixedSize(320, 600)
        
        # --- MODERN STYLING (QSS) ---
        self.panel.setStyleSheet("""
            QWidget {
                background-color: #1a1a24;
                color: #e0e0e0;
                font-family: 'Segoe UI', sans-serif;
                font-size: 14px;
                border-radius: 15px;
            }
            QLabel {
                color: #94a3b8;
                font-weight: bold;
                margin-top: 10px;
            }
            QPushButton {
                background-color: #2d2d3d;
                border: 1px solid #3f3f5f;
                border-radius: 8px;
                padding: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3f3f5f;
                border: 1px solid #5f5f7f;
            }
            QSlider::groove:horizontal {
                border: 1px solid #3f3f5f;
                height: 6px;
                background: #0f172a;
                margin: 2px 0;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #38bdf8;
                border: 1px solid #0ea5e9;
                width: 16px;
                height: 16px;
                margin: -6px 0;
                border-radius: 8px;
            }
            QComboBox {
                background-color: #0f172a;
                border: 1px solid #3f3f5f;
                border-radius: 5px;
                padding: 5px;
                color: white;
            }
            #quit_btn {
                background-color: #7f1d1d;
                color: #fecaca;
                border: none;
            }
            #quit_btn:hover {
                background-color: #991b1b;
            }
            #title {
                font-size: 18px;
                color: #38bdf8;
                margin-bottom: 10px;
            }
        """)

        layout = QVBoxLayout(self.panel)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        # Header
        title = QLabel("SPOTLIGHT PRO")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Divider
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background-color: #3f3f5f;")
        layout.addWidget(line)

        # Controls
        self.lock_btn = QPushButton("🔓 UNLOCK MODE")
        self.lock_btn.clicked.connect(self.toggle_lock)
        layout.addWidget(self.lock_btn)
        
        layout.addWidget(QLabel("SIZE"))
        self.size_slider = QSlider(Qt.Horizontal)
        self.size_slider.setRange(50, 800); self.size_slider.setValue(self.spot_size)
        self.size_slider.valueChanged.connect(self.set_size)
        layout.addWidget(self.size_slider)

        layout.addWidget(QLabel("SOFTNESS (FEATHER)"))
        self.feather_slider = QSlider(Qt.Horizontal)
        self.feather_slider.setRange(1, 200); self.feather_slider.setValue(self.feather_amount)
        self.feather_slider.valueChanged.connect(self.set_feather)
        layout.addWidget(self.feather_slider)

        layout.addWidget(QLabel("FOLLOW SMOOTHNESS"))
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(1, 100); self.speed_slider.setValue(int(self.follow_speed * 100))
        self.speed_slider.valueChanged.connect(self.set_speed)
        layout.addWidget(self.speed_slider)

        layout.addWidget(QLabel("OPACITY"))
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(0, 255); self.opacity_slider.setValue(self.overlay_color.alpha())
        self.opacity_slider.valueChanged.connect(self.set_opacity)
        layout.addWidget(self.opacity_slider)

        layout.addWidget(QLabel("SHAPE"))
        self.shape_box = QComboBox()
        self.shape_box.addItems(["Circle", "Rectangle"])
        self.shape_box.currentTextChanged.connect(self.set_shape)
        layout.addWidget(self.shape_box)

        layout.addStretch() # Push quit button to bottom

        self.quit_btn = QPushButton("QUIT APP")
        self.quit_btn.setObjectName("quit_btn")
        self.quit_btn.clicked.connect(self.quit_app)
        layout.addWidget(self.quit_btn)

        self.panel.show()
        self.panel.move(100, 100)

    # ... [Keep logic for update_spotlight_pos, paintEvent, and toggle_lock from previous message] ...
    
    def update_spotlight_pos(self):
        if not self.locked:
            mouse_pos = self.mapFromGlobal(QCursor.pos())
            self.target_pos = QPointF(mouse_pos)
        
        dx = (self.target_pos.x() - self.current_pos.x()) * self.follow_speed
        dy = (self.target_pos.y() - self.current_pos.y()) * self.follow_speed
        self.current_pos.setX(self.current_pos.x() + dx)
        self.current_pos.setY(self.current_pos.y() + dy)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rx, ry = self.current_pos.x(), self.current_pos.y()
        radius = self.spot_size / 2

        if self.shape == "Circle":
            gradient = QRadialGradient(QPointF(rx, ry), radius)
            gradient.setColorAt(0.0, Qt.transparent)
            fade_start = max(0, (radius - self.feather_amount) / radius)
            if fade_start < 1.0: gradient.setColorAt(fade_start, Qt.transparent)
            gradient.setColorAt(1.0, self.overlay_color)
            painter.setBrush(QBrush(gradient)); painter.setPen(Qt.NoPen)
            painter.drawRect(self.rect())
        else:
            path = QPainterPath(); path.addRect(QRectF(self.rect()))
            hole = QPainterPath(); hole.addRect(QRectF(rx - radius, ry - radius, self.spot_size, self.spot_size))
            painter.fillPath(path.subtracted(hole), self.overlay_color)

    def toggle_lock(self):
        self.locked = not self.locked
        self.lock_btn.setText("🔒 LOCKED MODE" if self.locked else "🔓 UNLOCK MODE")
        style = "background-color: #7f1d1d; border: 1px solid #f87171;" if self.locked else "background-color: #2d2d3d;"
        self.lock_btn.setStyleSheet(style)
        self.setWindowFlag(Qt.WindowTransparentForInput, not self.locked)
        self.showFullScreen()

    def mouseDoubleClickEvent(self, event):
        if self.locked: self.target_pos = QPointF(event.pos())

    def set_size(self, value): self.spot_size = value
    def set_feather(self, value): self.feather_amount = value
    def set_opacity(self, value): self.overlay_color.setAlpha(value)
    def set_shape(self, value): self.shape = value
    def set_speed(self, value): self.follow_speed = value / 100.0

    def init_tray(self):
        self.tray = QSystemTrayIcon(QIcon(), self)
        menu = QMenu(); menu.addAction("Toggle", self.toggle_visibility); menu.addAction("Quit", self.quit_app)
        self.tray.setContextMenu(menu); self.tray.show()

    def init_hotkeys(self):
        keyboard.add_hotkey("ctrl+alt+s", self.toggle_visibility)
        keyboard.add_hotkey("ctrl+alt+l", self.toggle_lock)

    def toggle_visibility(self):
        self.is_visible = not self.is_visible
        self.setVisible(self.is_visible); self.panel.setVisible(self.is_visible)

    def quit_app(self):
        keyboard.unhook_all(); QApplication.quit()

if __name__ == "__main__":
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    app = QApplication(sys.argv)
    window = Spotlight()
    sys.exit(app.exec_())