import sys
import keyboard
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QSlider,
    QPushButton, QLabel, QColorDialog, QComboBox,
    QSystemTrayIcon, QMenu
)
from PyQt5.QtGui import QPainter, QColor, QIcon, QPainterPath, QCursor
from PyQt5.QtCore import Qt, QRect, QTimer, QPoint, QRectF

class Spotlight(QWidget):
    def __init__(self):
        super().__init__()

        # ---------- Settings ----------
        self.shape = "Circle"
        self.spot_size = 250
        self.overlay_color = QColor(0, 0, 0, 200)
        self.is_visible = True
        
        # ---------- State Variables ----------
        self.locked = False
        self.target_pos = QPoint(0, 0) # Where the hole is pinned

        self.init_window()
        self.init_ui_panel()
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_spotlight_pos)
        self.timer.start(10)

        self.init_tray()
        self.init_hotkeys()

    def init_window(self):
        # Start in "Click-Through" mode
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
        self.panel.setFixedSize(280, 380)
        self.panel.setStyleSheet("background-color: #222; color: white; border-radius: 10px; padding: 10px;")

        layout = QVBoxLayout(self.panel)

        # Lock Button
        self.lock_btn = QPushButton("🔓 Unlock (Follow Mouse)")
        self.lock_btn.clicked.connect(self.toggle_lock)
        self.lock_btn.setStyleSheet("background-color: #444; font-weight: bold; padding: 10px;")
        layout.addWidget(self.lock_btn)
        
        layout.addWidget(QLabel("Double-click screen in 'Locked' mode to move hole."))

        # Size Slider
        layout.addWidget(QLabel("Spotlight Size"))
        self.size_slider = QSlider(Qt.Horizontal)
        self.size_slider.setRange(50, 800)
        self.size_slider.setValue(self.spot_size)
        self.size_slider.valueChanged.connect(self.set_size)
        layout.addWidget(self.size_slider)

        # Opacity Slider
        layout.addWidget(QLabel("Overlay Opacity"))
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(0, 255)
        self.opacity_slider.setValue(self.overlay_color.alpha())
        self.opacity_slider.valueChanged.connect(self.set_opacity)
        layout.addWidget(self.opacity_slider)

        # Shape Selector
        self.shape_box = QComboBox()
        self.shape_box.addItems(["Circle", "Rectangle"])
        self.shape_box.currentTextChanged.connect(self.set_shape)
        layout.addWidget(self.shape_box)

        self.panel.show()
        self.panel.move(50, 50)

    def toggle_lock(self):
        self.locked = not self.locked
        if self.locked:
            self.lock_btn.setText("🔒 Locked (Double-click screen to move)")
            self.lock_btn.setStyleSheet("background-color: #b33;")
            # REMOVE Transparent flag so we can detect double-clicks
            self.setWindowFlag(Qt.WindowTransparentForInput, False)
        else:
            self.lock_btn.setText("🔓 Unlock (Follow Mouse)")
            self.lock_btn.setStyleSheet("background-color: #444;")
            # ADD Transparent flag so we can click through to desktop
            self.setWindowFlag(Qt.WindowTransparentForInput, True)
        
        # We must call show() after changing flags to refresh the window
        self.showFullScreen()

    def mouseDoubleClickEvent(self, event):
        """ This only triggers if self.locked is True (because of window flags) """
        if self.locked:
            self.target_pos = event.pos()
            self.update()

    def update_spotlight_pos(self):
        if not self.locked:
            self.target_pos = self.mapFromGlobal(QCursor.pos())
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        path = QPainterPath()
        path.addRect(QRectF(self.rect())) # FIXED: Uses QRectF

        hole_path = QPainterPath()
        rx = self.target_pos.x() - self.spot_size / 2
        ry = self.target_pos.y() - self.spot_size / 2
        hole_rect = QRectF(rx, ry, self.spot_size, self.spot_size) # FIXED: Uses QRectF

        if self.shape == "Circle":
            hole_path.addEllipse(hole_rect)
        else:
            hole_path.addRect(hole_rect)

        main_shape = path.subtracted(hole_path)
        painter.fillPath(main_shape, self.overlay_color)

    def set_size(self, value): self.spot_size = value
    def set_opacity(self, value): self.overlay_color.setAlpha(value)
    def set_shape(self, value): self.shape = value

    def init_tray(self):
        self.tray = QSystemTrayIcon(QIcon(), self)
        menu = QMenu()
        menu.addAction("Toggle", self.toggle_visibility)
        menu.addAction("Quit", self.quit_app)
        self.tray.setContextMenu(menu)
        self.tray.show()

    def init_hotkeys(self):
        keyboard.add_hotkey("ctrl+alt+s", self.toggle_visibility)
        keyboard.add_hotkey("ctrl+alt+l", self.toggle_lock) # Hotkey to lock/unlock

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