import sys
import keyboard
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QSlider,
    QPushButton, QLabel, QColorDialog, QComboBox,
    QSystemTrayIcon, QMenu
)
from PyQt5.QtGui import QPainter, QColor, QIcon, QPainterPath, QCursor, QRadialGradient, QBrush
from PyQt5.QtCore import Qt, QRect, QTimer, QPoint, QRectF, QPointF

class Spotlight(QWidget):
    def __init__(self):
        super().__init__()

        # ---------- Settings ----------
        self.shape = "Circle"
        self.spot_size = 250
        self.feather_amount = 50
        self.follow_speed = 0.15  # Default speed (0.01 to 1.0)
        self.overlay_color = QColor(0, 0, 0, 220)
        self.is_visible = True
        
        # ---------- State Variables ----------
        self.locked = False
        # current_pos is where the light is DRAWN, target_pos is where the MOUSE is
        self.current_pos = QPointF(0, 0)
        self.target_pos = QPointF(0, 0)

        self.init_window()
        self.init_ui_panel()
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_spotlight_pos)
        self.timer.start(10) # 100 FPS update rate

        self.init_tray()
        self.init_hotkeys()

    def init_window(self):
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool |
            Qt.WindowTransparentForInput 
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.showFullScreen()

    def init_ui_panel(self):
        self.panel = QWidget()
        self.panel.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)
        self.panel.setFixedSize(300, 540) # Slightly wider and taller for more controls
        self.panel.setStyleSheet("background-color: #222; color: white; border-radius: 12px; padding: 15px;")

        layout = QVBoxLayout(self.panel)

        # Lock Toggle
        self.lock_btn = QPushButton("🔓 Unlock (Follow Mouse)")
        self.lock_btn.clicked.connect(self.toggle_lock)
        self.lock_btn.setStyleSheet("background-color: #444; font-weight: bold; padding: 10px; border-radius: 5px;")
        layout.addWidget(self.lock_btn)
        
        layout.addWidget(QLabel("Double-click screen in 'Locked' mode to move."))

        # Size Slider
        layout.addWidget(QLabel("Spotlight Size"))
        self.size_slider = QSlider(Qt.Horizontal)
        self.size_slider.setRange(50, 800)
        self.size_slider.setValue(self.spot_size)
        self.size_slider.valueChanged.connect(self.set_size)
        layout.addWidget(self.size_slider)

        # Feather Slider
        layout.addWidget(QLabel("Edge Softness (Feather)"))
        self.feather_slider = QSlider(Qt.Horizontal)
        self.feather_slider.setRange(1, 200)
        self.feather_slider.setValue(self.feather_amount)
        self.feather_slider.valueChanged.connect(self.set_feather)
        layout.addWidget(self.feather_slider)

        # NEW: Follow Speed Slider
        layout.addWidget(QLabel("Follow Speed (Smoothness)"))
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(1, 100)
        self.speed_slider.setValue(int(self.follow_speed * 100))
        self.speed_slider.valueChanged.connect(self.set_speed)
        layout.addWidget(self.speed_slider)

        # Opacity Slider
        layout.addWidget(QLabel("Overlay Opacity"))
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(0, 255)
        self.opacity_slider.setValue(self.overlay_color.alpha())
        self.opacity_slider.valueChanged.connect(self.set_opacity)
        layout.addWidget(self.opacity_slider)

        # Shape Selector
        layout.addWidget(QLabel("Shape"))
        self.shape_box = QComboBox()
        self.shape_box.addItems(["Circle", "Rectangle"])
        self.shape_box.currentTextChanged.connect(self.set_shape)
        layout.addWidget(self.shape_box)

        # Quit Button
        quit_btn = QPushButton("Quit Application")
        quit_btn.clicked.connect(self.quit_app)
        quit_btn.setStyleSheet("background-color: #721c24; color: #f8d7da; font-weight: bold; padding: 10px; margin-top: 15px; border-radius: 5px;")
        layout.addWidget(quit_btn)

        self.panel.show()
        self.panel.move(50, 50)

    def update_spotlight_pos(self):
        # 1. Determine where we WANT to go
        if not self.locked:
            mouse_pos = self.mapFromGlobal(QCursor.pos())
            self.target_pos = QPointF(mouse_pos)
        
        # 2. Smoothly interpolate current position toward target
        # Formula: current = current + (target - current) * speed
        dx = (self.target_pos.x() - self.current_pos.x()) * self.follow_speed
        dy = (self.target_pos.y() - self.current_pos.y()) * self.follow_speed
        
        self.current_pos.setX(self.current_pos.x() + dx)
        self.current_pos.setY(self.current_pos.y() + dy)

        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rx = self.current_pos.x()
        ry = self.current_pos.y()
        radius = self.spot_size / 2

        if self.shape == "Circle":
            # Radial gradient for feathered circle
            gradient = QRadialGradient(QPointF(rx, ry), radius)
            gradient.setColorAt(0.0, Qt.transparent)
            fade_start = max(0, (radius - self.feather_amount) / radius)
            if fade_start < 1.0:
                gradient.setColorAt(fade_start, Qt.transparent)
            gradient.setColorAt(1.0, self.overlay_color)
            
            painter.setBrush(QBrush(gradient))
            painter.setPen(Qt.NoPen)
            painter.drawRect(self.rect())
        else:
            # Subtracted path for hard rectangle
            path = QPainterPath()
            path.addRect(QRectF(self.rect()))
            hole = QPainterPath()
            hole.addRect(QRectF(rx - radius, ry - radius, self.spot_size, self.spot_size))
            main_shape = path.subtracted(hole)
            painter.fillPath(main_shape, self.overlay_color)

    def toggle_lock(self):
        self.locked = not self.locked
        self.lock_btn.setText("🔒 Locked" if self.locked else "🔓 Unlock")
        self.lock_btn.setStyleSheet(f"background-color: {'#b33' if self.locked else '#444'}; font-weight: bold; padding: 10px; border-radius: 5px;")
        self.setWindowFlag(Qt.WindowTransparentForInput, not self.locked)
        self.showFullScreen()

    def mouseDoubleClickEvent(self, event):
        if self.locked:
            # When locked, double-clicking sets a new target position
            # The spotlight will glide smoothly to this new double-clicked spot
            self.target_pos = QPointF(event.pos())

    # --- Control Setters ---
    def set_size(self, value): self.spot_size = value
    def set_feather(self, value): self.feather_amount = value
    def set_opacity(self, value): self.overlay_color.setAlpha(value)
    def set_shape(self, value): self.shape = value
    def set_speed(self, value): self.follow_speed = value / 100.0

    def init_tray(self):
        self.tray = QSystemTrayIcon(QIcon(), self)
        menu = QMenu()
        menu.addAction("Toggle", self.toggle_visibility)
        menu.addAction("Quit", self.quit_app)
        self.tray.setContextMenu(menu)
        self.tray.show()

    def init_hotkeys(self):
        keyboard.add_hotkey("ctrl+alt+s", self.toggle_visibility)
        keyboard.add_hotkey("ctrl+alt+l", self.toggle_lock)

    def toggle_visibility(self):
        self.is_visible = not self.is_visible
        self.setVisible(self.is_visible)
        self.panel.setVisible(self.is_visible)

    def quit_app(self):
        keyboard.unhook_all()
        QApplication.quit()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Spotlight()
    sys.exit(app.exec_())