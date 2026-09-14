import subprocess
from PyQt6.QtCore import Qt, QTimer, QRect, QVariantAnimation, QEasingCurve
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QFrame, QProgressBar, QPushButton, QApplication
from PyQt6.QtGui import QFont
from src.core.i18n import i18n

class DynamicIslandWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_hovered = False

        self.init_ui()
        self.setup_animation()

        self.hud_timer = QTimer(self)
        self.hud_timer.setSingleShot(True)
        self.hud_timer.timeout.connect(self.on_hud_timeout)

    def init_ui(self):
        self.container = QFrame(self)
        self.update_container_style(28)

        self.main_layout = QVBoxLayout(self.container)
        self.main_layout.setContentsMargins(10, 4, 10, 4)
        self.main_layout.setSpacing(4)

        # Üst Başlık
        self.header_layout = QHBoxLayout()
        self.header_layout.setContentsMargins(0, 0, 0, 0)
        self.header_layout.setSpacing(8)
        self.header_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        self.red_dot = QLabel()
        self.red_dot.setFixedSize(8, 8)
        self.red_dot.setStyleSheet("background-color: #FF3B30; border-radius: 4px;")

        self.icon_label = QLabel("")
        self.icon_label.setFont(QFont("Sans", 10))
        self.icon_label.setVisible(False)

        self.title_label = QLabel("")
        self.title_label.setFont(QFont("Sans", 9, QFont.Weight.Bold))
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.title_label.setVisible(False)

        self.status_label = QLabel("")
        self.status_label.setFont(QFont("Sans", 8))
        self.status_label.setStyleSheet("color: #0A84FF;")
        self.status_label.setVisible(False)

        self.header_layout.addWidget(self.red_dot, 0, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.header_layout.addWidget(self.icon_label, 0, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.header_layout.addWidget(self.title_label, 1, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.header_layout.addWidget(self.status_label, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        # HUD İlerleme Çubuğu
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(3)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #2C2C2E;
                border: none;
                border-radius: 1px;
            }
            QProgressBar::chunk {
                background-color: #0A84FF;
                border-radius: 1px;
            }
        """)
        self.progress_bar.setVisible(False)

        # Medya Oynatıcı Kontrolleri
        self.media_container = QWidget()
        media_layout = QVBoxLayout(self.media_container)
        media_layout.setContentsMargins(0, 2, 0, 2)
        media_layout.setSpacing(4)
        
        self.media_title = QLabel("")
        self.media_title.setFont(QFont("Sans", 9, QFont.Weight.Bold))
        self.media_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.media_artist = QLabel("")
        self.media_artist.setFont(QFont("Sans", 8))
        self.media_artist.setStyleSheet("color: #8E8E93;")
        self.media_artist.setAlignment(Qt.AlignmentFlag.AlignCenter)

        controls_layout = QHBoxLayout()
        controls_layout.setContentsMargins(10, 2, 10, 2)
        controls_layout.setSpacing(12)

        self.btn_prev = QPushButton("⏮")
        self.btn_prev.setFixedSize(32, 26)
        self.btn_prev.clicked.connect(lambda: self.run_playerctl("previous"))

        self.btn_play = QPushButton("⏯")
        self.btn_play.setFixedSize(40, 26)
        self.btn_play.clicked.connect(lambda: self.run_playerctl("play-pause"))

        self.btn_next = QPushButton("⏭")
        self.btn_next.setFixedSize(32, 26)
        self.btn_next.clicked.connect(lambda: self.run_playerctl("next"))

        controls_layout.addWidget(self.btn_prev)
        controls_layout.addWidget(self.btn_play)
        controls_layout.addWidget(self.btn_next)

        media_layout.addWidget(self.media_title)
        media_layout.addWidget(self.media_artist)
        media_layout.addLayout(controls_layout)
        self.media_container.setVisible(False)

        # Son Dosya Bilgisi
        self.recent_file_label = QLabel("")
        self.recent_file_label.setFont(QFont("Sans", 8))
        self.recent_file_label.setStyleSheet("color: #98989D; padding-top: 2px;")
        self.recent_file_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.recent_file_label.setVisible(False)

        self.main_layout.addLayout(self.header_layout)
        self.main_layout.addWidget(self.progress_bar)
        self.main_layout.addWidget(self.media_container)
        self.main_layout.addWidget(self.recent_file_label)

        self.set_idle_state(animated=False)

    def update_container_style(self, height):
        radius = min(20, height // 2)
        self.container.setStyleSheet(f"""
            QFrame {{
                background-color: #000000;
                border: 1px solid #1C1C1E;
                border-radius: {radius}px;
            }}
            QLabel {{
                color: #FFFFFF;
                font-family: 'Inter', 'Segoe UI', sans-serif;
            }}
            QPushButton {{
                background-color: #1C1C1E;
                color: #FFFFFF;
                border: none;
                border-radius: 10px;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: #2C2C2E;
            }}
        """)

    def setup_animation(self):
        self.anim = QVariantAnimation(self)
        self.anim.setDuration(320)
        self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.anim.valueChanged.connect(self.on_anim_step)

    def animate_to(self, target_w, target_h):
        self.anim.stop()
        start_rect = QRect(0, 0, self.width(), self.height())
        end_rect = QRect(0, 0, target_w, target_h)
        self.anim.setStartValue(start_rect)
        self.anim.setEndValue(end_rect)
        self.anim.start()

    def on_anim_step(self, rect):
        w = rect.width()
        h = rect.height()
        screen = QApplication.primaryScreen()
        if screen:
            screen_w = screen.geometry().width()
            x = (screen_w - w) // 2
            self.setGeometry(x, 0, w, h)
            self.container.setGeometry(0, 0, w, h)
            self.update_container_style(h)

    def run_playerctl(self, command):
        try:
            subprocess.Popen(["playerctl", command])
        except Exception:
            pass

    def set_idle_state(self, animated=True):
        self.red_dot.setVisible(True)
        self.icon_label.setVisible(False)
        self.title_label.setVisible(False)
        self.status_label.setVisible(False)
        self.progress_bar.setVisible(False)
        self.media_container.setVisible(False)
        self.recent_file_label.setVisible(False)

        if animated:
            self.animate_to(110, 28)
        else:
            self.on_anim_step(QRect(0, 0, 110, 28))

    def enterEvent(self, event):
        self.is_hovered = True
        self.expand_on_hover()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.is_hovered = False
        if not self.hud_timer.isActive():
            self.set_idle_state(animated=True)
        super().leaveEvent(event)

    def expand_on_hover(self):
        has_media = bool(self.media_title.text().strip())
        has_recent = bool(self.recent_file_label.text().strip())

        self.red_dot.setVisible(True)
        self.title_label.setText(i18n.t("media_player") if has_media else i18n.t("app_title"))
        self.title_label.setVisible(True)
        self.status_label.setVisible(True)

        if has_media:
            self.media_container.setVisible(True)
        if has_recent:
            self.recent_file_label.setVisible(True)

        w = 340
        h = 42
        if has_media:
            h += 80
        if has_recent:
            h += 24

        self.animate_to(w, h)

    def trigger_hud_toast(self, icon, text, value=-1):
        self.hud_timer.stop()
        self.red_dot.setVisible(True)
        self.icon_label.setText(icon)
        self.icon_label.setVisible(True)
        self.title_label.setText(text)
        self.title_label.setVisible(True)

        if value >= 0:
            self.progress_bar.setValue(value)
            self.progress_bar.setVisible(True)
            h = 48
        else:
            self.progress_bar.setVisible(False)
            h = 38

        w = max(260, len(text) * 9 + 60)
        self.animate_to(w, h)
        self.hud_timer.start(2500)

    def on_hud_timeout(self):
        if not self.is_hovered:
            self.set_idle_state(animated=True)

    def update_media(self, data):
        title = data.get("title", "")
        artist = data.get("artist", "")
        if title:
            self.media_title.setText(title)
            self.media_artist.setText(artist)
        else:
            self.media_title.setText("")
            self.media_artist.setText("")
            self.media_container.setVisible(False)
