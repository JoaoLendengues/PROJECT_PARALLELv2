from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QLineEdit, QPushButton, QFrame, QMessageBox)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QPixmap


class LoginWidget(QWidget):
    def __init__(self, on_login_success):
        super().__init__()
        self.on_login_success = on_login_success
        self.init_ui()
    
    def init_ui(self):
        # Fundo da janela (cor original)
        self.setStyleSheet("background-color: #eef2f6;")
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        
        # Card de login (cor original)
        card = QFrame()
        card.setFixedSize(450, 520)  # Tamanho ajustado
        card.setStyleSheet("""
            QFrame {
                background-color:#ffffff;
                border-radius: 16px;
                border: 1px solid #f7f9fc;
            }
        """)
        
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(20)
        card_layout.setContentsMargins(40, 40, 40, 40)
        
        # Logo (texto ajustado para não cortar)
        logo = QLabel("📦 Project Parallel")
        logo.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        logo.setAlignment(Qt.AlignCenter)
        logo.setStyleSheet("""
            color: #2c7da0;
            font-size: 28px;
            font-weight: bold;
            margin-bottom: 0px;
        """)
        logo.setWordWrap(True)  # Quebrar linha se necessário
        card_layout.addWidget(logo)
        
        card_layout.addSpacing(15)
        
        # Título
        title = QLabel("Acesso ao Sistema")
        title.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            color: #1e293b;
            font-size: 20px;
            margin-bottom: 10px;
        """)
        card_layout.addWidget(title)
        
        card_layout.addSpacing(10)
        
        # Campo Código
        label_codigo = QLabel("Código")
        label_codigo.setFont(QFont("Segoe UI", 13))
        label_codigo.setStyleSheet("color: #334155;")
        card_layout.addWidget(label_codigo)
        
        self.codigo_input = QLineEdit()
        self.codigo_input.setPlaceholderText("Digite seu código")
        self.codigo_input.setFixedHeight(45)
        self.codigo_input.setFont(QFont("Segoe UI", 13))
        self.codigo_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #cbd5e1;
                border-radius: 10px;
                padding: 10px 14px;
                background-color: white;
            }
            QLineEdit:focus {
                border-color: #2c7da0;
            }
        """)
        card_layout.addWidget(self.codigo_input)
        
        card_layout.addSpacing(10)
        
        # Campo Senha
        label_senha = QLabel("Senha")
        label_senha.setFont(QFont("Segoe UI", 13))
        label_senha.setStyleSheet("color: #334155;")
        card_layout.addWidget(label_senha)
        
        self.senha_input = QLineEdit()
        self.senha_input.setPlaceholderText("Digite sua senha")
        self.senha_input.setEchoMode(QLineEdit.Password)
        self.senha_input.setFixedHeight(45)
        self.senha_input.setFont(QFont("Segoe UI", 13))
        self.senha_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #cbd5e1;
                border-radius: 10px;
                padding: 10px 14px;
                background-color: white;
            }
            QLineEdit:focus {
                border-color: #2c7da0;
            }
        """)
        card_layout.addWidget(self.senha_input)
        
        card_layout.addSpacing(20)
        
        # Botão Login
        self.login_btn = QPushButton("Entrar")
        self.login_btn.setFixedHeight(48)
        self.login_btn.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        self.login_btn.setStyleSheet("""
            QPushButton {
                background-color: #2c7da0;
                color: white;
                border: none;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: #1f5e7a;
            }
            QPushButton:pressed {
                background-color: #164a60;
            }
        """)
        self.login_btn.clicked.connect(self.fazer_login)
        card_layout.addWidget(self.login_btn)
        
        # Mensagem de status
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setFont(QFont("Segoe UI", 11))
        self.status_label.setStyleSheet("color: #e76f51; margin-top: 10px;")
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
            self.status_label.setStyleSheet("color: #2a9d8f; margin-top: 10px;")
            self.status_label.setText("Login realizado com sucesso!")
            QTimer.singleShot(500, lambda: self.on_login_success(result["usuario"]))
        else:
            self.login_btn.setEnabled(True)
            self.login_btn.setText("Entrar")
            self.status_label.setStyleSheet("color: #e76f51; margin-top: 10px;")
            error_msg = result["error"]
            if isinstance(error_msg, list):
                error_msg = ", ".join(error_msg)
            elif isinstance(error_msg, dict):
                error_msg = str(error_msg)
            self.status_label.setText(error_msg)
