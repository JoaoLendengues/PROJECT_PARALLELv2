from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                                QTabWidget, QPushButton, QLabel, QFrame, QStackedWidget)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QIcon, QAction
import os

from widgets.home_widget import HomeWidget
from widgets.materiais_widget import MateriaisWidget
from widgets.maquinas_widget import MaquinasWidget
from widgets.movimentacoes_widget import MovimentacoesWidget
from widgets.pedidos_widget import PedidosWidget
from widgets.usuarios_widget import UsuariosWidget
from widgets.parametros_widget import ParametrosWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Project Parallel - Sistema de Controle de Estoque')
        self.setGeometry(100, 100, 1400, 800)

        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Layout principal
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # sidebar esquerda
        sidebar = self.create_sidebar()
        sidebar.setFixedWidth(250)
        main_layout.addWidget(sidebar)

        # Área de conteúdo
        self.content_stack = QStackedWidget()
        main_layout.addWidget(self.content_stack)

        # Inicializar telas
        self.init_screens()

        # Selecionar home por padrão
        self.content_stack.setCurrentWidget(self.home_widget)
    """Marca o menu como ativo visualmente"""
    def set_active_menu(self, button_index):
        for i, btn in enumerate(self.menu_buttons):
            if i == button_index:
                btn.setProperty("active", True)
            else:
                btn.setProperty("active", False)
            btn.style().unpolish(btn)
            btn.style().polish(btn)
    
    def create_sidebar(self):
        """Cria a barra lateral com os menus"""
        sidebar = QFrame()
        sidebar.setProperty('class', 'sidebar')
        
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Logo
        logo = QLabel('📦Project Parallel')
        logo_font = QFont('Segoe Ui', 16, QFont.Weight.Bold)
        logo_font.setWeight(QFont.Weight.Bold)
        logo.setAlignment(Qt.AlignCenter)
        logo.setProperty('class', 'logo')
        layout.addWidget(logo)


        # Botões do menu
        menus = [
            ("🏠 Home", self.show_home),
            ("📦 Materiais", self.show_materiais),
            ("🖥️ Máquinas", self.show_maquinas),
            ("📊 Movimentações", self.show_movimentacoes),
            ("🔧 Manutenções", self.show_manutencoes),
            ("📋 Pedidos", self.show_pedidos),
            ("👥 Usuários", self.show_usuarios),
            ("⚙️ Parâmetros", self.show_parametros)
        ]

        self.menu_buttons = [] # Guardar referências dos botões
        for idx, (text, callback) in enumerate(menus):
            btn = QPushButton(text)
            btn.setProperty("class", "menu-button")
            btn.setProperty("active", False)
            btn.clicked.connect(lambda checked, i=idx, cb=callback: [cb(), self.set_active_menu(i)])
            btn.setFixedHeight(48)
            layout.addWidget(btn)
            self.menu_buttons.append(btn)
    
        layout.addStretch()

        # Rodapé com informações
        footer = QLabel('v1.0.0')
        footer.setAlignment(Qt.AlignCenter)
        footer.setProperty('class', 'footer')
        layout.addWidget(footer)

        return sidebar
    
    def init_screens(self):
        """Inicializa todas as telas do sistema"""
        self.home_widget = HomeWidget()
        self.materiais_widget = MateriaisWidget()
        self.maquinas_widget = MaquinasWidget()
        self.movimentacoes_widget = MovimentacoesWidget()
        self.manutencoes_widget = MaquinasWidget()
        self.pedidos_widget = PedidosWidget()
        self.usuarios_widget = UsuariosWidget()
        self.parametros_widget = ParametrosWidget()

        self.content_stack.addWidget(self.home_widget)
        self.content_stack.addWidget(self.materiais_widget)
        self.content_stack.addWidget(self.maquinas_widget)
        self.content_stack.addWidget(self.movimentacoes_widget)
        self.content_stack.addWidget(self.manutencoes_widget)
        self.content_stack.addWidget(self.pedidos_widget)
        self.content_stack.addWidget(self.usuarios_widget)
        self.content_stack.addWidget(self.parametros_widget)

    def show_home(self):
        self.content_stack.setCurrentWidget(self.home_widget)

    def show_materiais(self):
        self.content_stack.setCurrentWidget(self.materiais_widget)
        self.materiais_widget.carregar_dados()

    def show_maquinas(self):
        self.content_stack.setCurrentWidget(self.maquinas_widget)
        self.maquinas_widget.carregar_dados()

    def show_movimentacoes(self):
        self.content_stack.setCurrentWidget(self.movimentacoes_widget)
        self.movimentacoes_widget.carregar_dados()

    def show_manutencoes(self):
        self.content_stack.setCurrentWidget(self.manutencoes_widget)
        self.manutencoes_widget.carregar_dados()

    def show_pedidos(self):
        self.content_stack.setCurrentWidget(self.pedidos_widget)
        self.pedidos_widget.carregar_dados()

    def show_usuarios(self):
        self.content_stack.setCurrentWidget(self.usuarios_widget)
        self.usuarios_widget.carregar_dados()

    def show_parametros(self):
        self.content_stack.setCurrentWidget(self.parametros_widget)
