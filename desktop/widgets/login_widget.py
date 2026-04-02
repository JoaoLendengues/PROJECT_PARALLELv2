from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, Qlabel, QLineEdit, QPushButton, QFrame, QMessageBox)
from PySide6.QtCore import Qt, Qtimer 
from PySide6.QtGui import QFont, QPixmap 


class LoginWidget(QWidget):
    def __init__(self, on_login_success):
        super().__init__()
        self.on_login_success = on_login_success
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        # Card de Login
        card = QFrame()
        card.setProperty("class", "login-card")
        card.setFixedSize(400,450)

        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(20)
        card_layout.setContentsMargins(40, 40, 40, 40)

        # Logo
        logo = Qlabel("📦 Project Parallel")
        logo.setFont(Qfont("Segoe UI", 20, QFont.Weight.Bold))
        logo.setAlignment(Qt.AlignCenter)
        logo.setStyleSheet("color: #2c7da0;")
        card_layout.addWidget(logo)

        card_layout.addSpacing(20)

        # Título
        title = Qlabel("Acesso ao Sistema")
        title.setFont(Qfont("Segoe Ui", 14))
        title.setAlignment("color: #1e293b;")
        card_layout.addWidget(title)

        card_layout.addSpacing(10)

        # Campo Código
        label_codigo = Qlabel("Código")
        label_codigo.setFont(Qfont("Segoe Ui", 12))
        card_layout.addWidget(label_codigo)

        self.codigo_input = QLineEdit()
        self.codigo_input.setPlaceholderText("Digite seu código")
        self.codigo_input.setFixedHeight(40)
        card_layout.addWidget(self.codigo_input)

        # Campo Senha
        label_senha = QLabel("Senha")
        label_senha.setFont(QFont("Segoe UI", 12))
        card_layout.addWidget(label_senha)
        
        self.senha_input = QLineEdit()
        self.senha_input.setPlaceholderText("Digite sua senha")
        self.senha_input.setEchoMode(QLineEdit.Password)
        self.senha_input.setFixedHeight(40)
        card_layout.addWidget(self.senha_input)

        card_layout.addSpacing(20)

        # Botão Login
        self.login_btn = QPushButton("Entrar")
        self.login_btn.setFixedHeight(45)
        self.login_btn.clicked.connect(self.fazer_login)
        card_layout.addWidget(self.login_btn)
        
        # Mensagem de status
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #e76f51;")
        card_layout.addWidget(self.status_label)

        layout.addWidget(card)

    def fazer_login(self):
        codigo = self.codigo_input.text().strip()
        senha = self.senha_input.text()

        if not codigo or not senha:
            self.status_label.setText("Preencha todos os campos")
            return
        
        self.login_btn.setEnabled(False)
        self.login_btn.setText("Entrando...")
        self.status_label.setText("")
        
        from api_client import api_client

        result = api_client.login(codigo, senha)

        if result["success"]:
            self.status_label.setStyleSheet("color: #2a9d8f;")
            self.status_label.setText("Login realizado com sucesso!")
            QTimer.singleShot(500, lambda: self.on_login_success(result["usuario"]))
        else:
            self.login_btn.setEnabled(True)
            self.login_btn.setText("Entrar")
            self.status_label.setStyleSheet("color: #e76f51;")
            self.status_label.setText(result["error"])

