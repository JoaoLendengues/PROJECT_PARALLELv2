import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from dotenv import load_dotenv

from widgets.main_window import MainWindow
from widgets.login_widget import LoginWidget
from api_client import api_client

load_dotenv()

# Variáveis globais
_app = None
_current_window = None


def show_login():
    """Exibe a tela de login"""
    global _current_window
    
    if _current_window:
        _current_window.close()
    
    _current_window = LoginWidget(on_login_success)
    _current_window.show()


def on_login_success(usuario):
    """Callback quando o login é bem sucedido"""
    global _current_window
    
    _current_window.close()
    _current_window = MainWindow(usuario)
    _current_window.show()


def main():
    global _app
    
    _app = QApplication(sys.argv)
    _app.setStyle('Fusion')
    
    # Carregar estilo
    style_path = os.path.join(os.path.dirname(__file__), 'styles', 'style.qss')
    if os.path.exists(style_path):
        with open(style_path, 'r', encoding='utf-8') as f:
            _app.setStyleSheet(f.read())
    
    # Mostrar tela de login
    show_login()
    
    sys.exit(_app.exec())


if __name__ == '__main__':
    main()
    