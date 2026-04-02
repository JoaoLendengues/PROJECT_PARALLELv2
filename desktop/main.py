import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from dotenv import load_dotenv

# Adicionar o diretório atual ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from widgets.main_window import MainWindow
from widgets.login_widget import LoginWidget
from api_client import api_client

# Carregar variáveis de ambiente
load_dotenv()


class AppLauncher:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setStyle('Fusion')
        self.load_styles()
        
        self.login_widget = None
        self.main_window = None
        
        self.show_login()
    
    def load_styles(self):
        """Carrega o arquivo de estilos"""
        style_path = os.path.join(os.path.dirname(__file__), 'styles', 'style.qss')
        if os.path.exists(style_path):
            with open(style_path, 'r', encoding='utf-8') as f:
                self.app.setStyleSheet(f.read())
    
    def show_login(self):
        """Exibe a tela de login"""
        self.login_widget = LoginWidget(self.on_login_success)
        self.login_widget.show()
    
    def on_login_success(self, usuario):
        """Callback quando o login é bem sucedido"""
        # Fecha a tela de login
        self.login_widget.close()
        
        # Abre a janela principal
        self.main_window = MainWindow(usuario)
        self.main_window.show()
    
    def run(self):
        """Executa a aplicação"""
        sys.exit(self.app.exec())


def main():
    launcher = AppLauncher()
    launcher.run()


if __name__ == '__main__':
    main()
    