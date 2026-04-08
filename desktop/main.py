import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QTimer
from dotenv import load_dotenv

from widgets.main_window import MainWindow
from widgets.login_widget import LoginWidget
from api_client import api_client
from updater import UpdateChecker
from widgets.toast_notification import notification_manager

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
    
    # Verificar atualizações em segundo plano após o login
    verificar_atualizacoes_background()


def verificar_atualizacoes_background():
    """Verifica atualizações em segundo plano e exibe notificação"""
    current_version = "1.0.0"  # Atualize conforme a versão atual
    
    checker = UpdateChecker(current_version)
    
    def on_update_available(update_info):
        notification_manager.info(
            f"📢 Nova versão {update_info['version']} disponível!\n\n"
            f"Clique em 'Atualizações' no menu para instalar.",
            _current_window,
            10000
        )
    
    def on_no_update():
        print("✅ Sistema já está atualizado")
    
    def on_error(error_msg):
        print(f"❌ Erro ao verificar atualizações: {error_msg}")
    
    checker.update_available.connect(on_update_available)
    checker.no_update.connect(on_no_update)
    checker.error.connect(on_error)
    
    # Aguardar 5 segundos após login para verificar
    QTimer.singleShot(5000, checker.start)


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
    