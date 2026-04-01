import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from dotenv import load_dotenv

# Adicionar o diretório atual ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from widgets.main_window import MainWindow

# Carregar variáveis de ambiente
load_dotenv()

def main(): 
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    # Configurar estilo global
    style_path = os.path.join(os.path.dirname(__file__), 'styles', 'style.qss')
    if os.path.exists(style_path):
        with open(style_path, 'r', encoding='utf-8') as f:
            app.setStyleSheet(f.read())

    # Criar e mostrar janela principal
    window = MainWindow()
    window.show()

    sys.exit(app.exec())

if __name__ == '__main__':
    main()
    