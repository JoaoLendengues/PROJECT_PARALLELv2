from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                                QTabWidget, QPushButton, QLabel, QFrame, QStackedWidget)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont
from datetime import datetime
import os

from widgets.home_widget import HomeWidget
from widgets.materiais_widget import MateriaisWidget
from widgets.maquinas_widget import MaquinasWidget
from widgets.movimentacoes_widget import MovimentacoesWidget
from widgets.manutencoes_widget import ManutencoesWidget
from widgets.pedidos_widget import PedidosWidget
from widgets.usuarios_widget import UsuariosWidget
from widgets.parametros_widget import ParametrosWidget
from widgets.colaboradores_widget import ColaboradoresWidget
from widgets.demandas_widget import DemandasWidget
from widgets.relatorios_widget import RelatoriosWidget
from widgets.toast_notification import notification_manager

class MainWindow(QMainWindow):
    def __init__(self, usuario):
        super().__init__()
        self.usuario = usuario
        self.setWindowTitle(f"Project Parallel - Sistema de Controle de Estoque - {usuario['nome']}")
        self.setGeometry(100, 100, 1400, 800)

        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Layout principal
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar esquerda
        sidebar = self.create_sidebar()
        sidebar.setFixedWidth(250)
        main_layout.addWidget(sidebar)

        # Área de conteúdo (stacked widget)
        self.content_stack = QStackedWidget()
        main_layout.addWidget(self.content_stack)

        # Inicializar telas
        self.init_screens()

        # Selecionar home por padrão
        self.content_stack.setCurrentWidget(self.home_widget)

        # Configurar o gerenciador de notificações
        notification_manager.set_parent(self)
    
    def set_active_menu(self, button_index):
        """Marca o menu como ativo visualmente"""
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
        logo = QLabel('📦 Project Parallel')
        logo_font = QFont('Segoe UI', 16, QFont.Weight.Bold)
        logo.setFont(logo_font)
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
            ("🎫 Demandas", self.show_demandas),
            ("👥 Usuários", self.show_usuarios),
            ("👥 Colaboradores", self.show_colaboradores),
            ("📈 Relatórios", self.show_relatorios),
            ("⚙️ Parâmetros", self.show_parametros)
        ]

        self.menu_buttons = []
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
        self.home_widget.set_usuario(self.usuario['nome'])  # Passa o nome do usuário
        self.materiais_widget = MateriaisWidget()
        self.maquinas_widget = MaquinasWidget()
        self.movimentacoes_widget = MovimentacoesWidget()
        self.manutencoes_widget = ManutencoesWidget()
        self.pedidos_widget = PedidosWidget()
        self.usuarios_widget = UsuariosWidget()
        self.parametros_widget = ParametrosWidget()
        self.colaboradores_widget = ColaboradoresWidget()
        self.demandas_widget = DemandasWidget()
        self.relatorios_widget = RelatoriosWidget()

        self.content_stack.addWidget(self.home_widget)
        self.content_stack.addWidget(self.materiais_widget)
        self.content_stack.addWidget(self.maquinas_widget)
        self.content_stack.addWidget(self.movimentacoes_widget)
        self.content_stack.addWidget(self.manutencoes_widget)
        self.content_stack.addWidget(self.pedidos_widget)
        self.content_stack.addWidget(self.usuarios_widget)
        self.content_stack.addWidget(self.parametros_widget)
        self.content_stack.addWidget(self.colaboradores_widget)
        self.content_stack.addWidget(self.demandas_widget)
        self.content_stack.addWidget(self.relatorios_widget)

    def show_home(self):
        self.content_stack.setCurrentWidget(self.home_widget)
        self.home_widget.carregar_dados()

    def show_materiais(self):
        self.content_stack.setCurrentWidget(self.materiais_widget)
        self.materiais_widget.carregar_materiais()

    def show_maquinas(self):
        self.content_stack.setCurrentWidget(self.maquinas_widget)
        self.maquinas_widget.carregar_maquinas()

    def show_movimentacoes(self):
        self.content_stack.setCurrentWidget(self.movimentacoes_widget)
        self.movimentacoes_widget.carregar_movimentacoes()

    def show_manutencoes(self):
        self.content_stack.setCurrentWidget(self.manutencoes_widget)
        self.manutencoes_widget.carregar_manutencoes()

    def show_pedidos(self):
        self.content_stack.setCurrentWidget(self.pedidos_widget)
        self.pedidos_widget.carregar_pedidos()

    def show_usuarios(self):
        self.content_stack.setCurrentWidget(self.usuarios_widget)
        self.usuarios_widget.carregar_usuarios()

    def show_parametros(self):
        self.content_stack.setCurrentWidget(self.parametros_widget)

    def show_colaboradores(self):
        self.content_stack.setCurrentWidget(self.colaboradores_widget)
        self.colaboradores_widget.carregar_colaboradores()   

    def show_demandas(self):
        self.content_stack.setCurrentWidget(self.demandas_widget)
        self.demandas_widget.carregar_demandas()

    def show_relatorios(self):
        self.content_stack.setCurrentWidget(self.relatorios_widget)
        