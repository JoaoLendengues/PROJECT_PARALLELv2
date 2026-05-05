from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QFrame, QLabel, QPushButton, QVBoxLayout, QWidget


class AccessDeniedWidget(QWidget):
    def __init__(self, on_back_home=None):
        super().__init__()
        self.on_back_home = on_back_home
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignCenter)

        card = QFrame()
        card.setObjectName("infoCard")
        card.setMinimumWidth(460)
        card.setMaximumWidth(640)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(36, 36, 36, 36)
        card_layout.setSpacing(14)
        card_layout.setAlignment(Qt.AlignCenter)

        icon = QLabel("🔒")
        icon.setAlignment(Qt.AlignCenter)
        icon.setFont(QFont("Segoe UI", 34))
        card_layout.addWidget(icon)

        self.title_label = QLabel("Acesso não permitido")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        self.title_label.setStyleSheet("color: #0f172a;")
        card_layout.addWidget(self.title_label)

        self.message_label = QLabel("")
        self.message_label.setAlignment(Qt.AlignCenter)
        self.message_label.setWordWrap(True)
        self.message_label.setStyleSheet("color: #475569; font-size: 14px;")
        card_layout.addWidget(self.message_label)

        self.back_button = QPushButton("Ir para a tela inicial")
        self.back_button.setFixedHeight(42)
        self.back_button.clicked.connect(self._go_back_home)
        card_layout.addWidget(self.back_button)

        layout.addWidget(card)

    def configure(self, screen_label, role_label):
        self.message_label.setText(
            f"Você não tem permissão para acessar {screen_label}.\n\n"
            f"Perfil atual: {role_label}."
        )

    def _go_back_home(self):
        if callable(self.on_back_home):
            self.on_back_home()
