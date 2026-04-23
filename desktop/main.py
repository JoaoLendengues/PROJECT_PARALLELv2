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

    if _current_window:
        _current_window.close()

    _current_window = MainWindow(usuario)
    _current_window.showMaximized()

    # Iniciar seviço de alertas
    try:
        from core.alert_service import alert_service
        alert_service.iniciar()
        print('✅ Serviço de alertas iniciado')
    except Exception as e:
        print(f'⚠️ Erro ao iniciar serviço de alertas: {e}')

    # Verificar atualizações em segundo plano
    verificar_atualizacoes()


def verificar_atualizacoes():
    """Verifica atualizações em segundo plano e exibe notificação"""
    checker = UpdateChecker()
    
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
    
    QTimer.singleShot(5000, checker.start)


def main():
    global _app
    
    _app = QApplication(sys.argv)
    _app.setStyle('Windows')
    
    # Configurar o notification_manager com a janela principal (será atualizado depois)
    from core.notification_manager import notification_manager as core_nm
    # O parent será definido quando a MainWindow for criada
    
    global_style = """
        /* Força estilo para TODOS os combobox */
        QComboBox {
            background-color: #ffffff;
            border: 1px solid #cbd5e1;
            border-radius: 6px;
            padding: 6px 10px;
            color: #1e293b;
            font-size: 13px;
            min-height: 30px;
        }
        
        QComboBox::drop-down {
            border: none;
            width: 20px;
        }
        
        QComboBox::down-arrow {
            image: none;
        }
        
        QComboBox QAbstractItemView {
            background-color: #ffffff;
            border: 1px solid #cbd5e1;
            border-radius: 6px;
            padding: 4px;
        }
        
        QComboBox QAbstractItemView::item {
            padding: 6px 10px;
            border: none;
            color: #1e293b;
        }
        
        QComboBox QAbstractItemView::item:selected {
            background-color: #e6f0ff;
        }
        
        QComboBox QAbstractItemView::item:hover {
            background-color: #f1f5f9;
        }
        
        /* Força estilo para QDateEdit */
        QDateEdit {
            background-color: #ffffff;
            border: 1px solid #cbd5e1;
            border-radius: 6px;
            padding: 6px 10px;
            color: #1e293b;
            min-height: 30px;
        }
        
        QDateEdit::drop-down {
            border: none;
            width: 20px;
        }
        
        QDateEdit::down-arrow {
            image: none;
        }
    """
    
    style_path = os.path.join(os.path.dirname(__file__), 'styles', 'style.qss')
    if os.path.exists(style_path):
        with open(style_path, 'r', encoding='utf-8') as f:
            base_style = f.read()
        _app.setStyleSheet(base_style + global_style)
    else:
        _app.setStyleSheet(global_style)
    
    show_login()
    
    sys.exit(_app.exec())


if __name__ == '__main__':
    main()
    