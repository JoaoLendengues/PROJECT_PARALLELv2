from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                                QPushButton, QLabel, QFrame, QStackedWidget, QMessageBox, QApplication)
from PySide6.QtCore import Qt, QTimer, QThread, Signal
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
from widgets.notification_badge import NotificationBadge
from api_client import api_client
from core.notification_manager import notification_manager as core_mn
from version import get_version


# =====================================================
# THREAD PARA CARREGAMENTO EM BACKGROUND
# =====================================================

class DataLoaderThread(QThread):
    """Thread para carregar dados em background"""
    finished = Signal(object)

    def __init__(self, loader_func, *args, **kwargs):
        super().__init__()
        self.loader_func = loader_func
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            result = self.loader_func(*self.args, **self.kwargs)
            self.finished.emit(result)
        except Exception as e:
            print(f"Erro no carregamento: {e}")
            self.finished.emit(None)


class MainWindow(QMainWindow):
    def __init__(self, usuario):
        super().__init__()
        self.usuario = usuario
        self.setWindowTitle(f"Project Parallel - Sistema de Controle de Estoque - {usuario['nome']}")

        # Definir tamanho mínimo
        self.setMinimumSize(1200, 700)

        # Definir geometria inicial
        self.setGeometry(100, 100, 1400, 800)

        core_mn.set_parent(self)

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

        # Área de conteúdo
        self.content_stack = QStackedWidget()
        main_layout.addWidget(self.content_stack)

        # ✅ Inicializar telas (sem carregar dados pesados)
        self.init_screens_light()

        # ✅ Carregar dados em background
        self.load_background_data()

        # Selecionar home por padrão
        self.content_stack.setCurrentWidget(self.home_widget)
        self.home_widget.on_show()  # Carregar dados da home

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
            ("👥 Colaboradores", self.show_colaboradores),
            ("🎫 Demandas", self.show_demandas),
            ("📈 Relatórios", self.show_relatorios),
            ("👥 Usuários", self.show_usuarios),
            ("⚙️ Parâmetros", self.show_parametros),
            ("🔄 Atualizações", self.show_updates)
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

        # botão de Notificações
        self.notification_btn = NotificationBadge()
        self.notification_btn.clicked.connect(self.show_notification_center)
        layout.addWidget(self.notification_btn)

        # Atualizar contador inicial
        self.notification_btn.atualizar_contador()

        # Botão Trocar Usuário
        btn_trocar_usuario = QPushButton("🔄 Trocar Usuário")
        btn_trocar_usuario.setProperty("class", "menu-button-bottom")
        btn_trocar_usuario.setFixedHeight(48)
        btn_trocar_usuario.clicked.connect(self.trocar_usuario)
        layout.addWidget(btn_trocar_usuario)

        # Botão Sair
        btn_sair = QPushButton("🚪 Sair")
        btn_sair.setProperty("class", "menu-button-bottom")
        btn_sair.setFixedHeight(48)
        btn_sair.clicked.connect(self.sair)
        layout.addWidget(btn_sair)

        # Rodapé
        footer = QLabel(f'v{get_version()}')
        footer.setAlignment(Qt.AlignCenter)
        footer.setProperty('class', 'footer')
        layout.addWidget(footer)

        return sidebar

    def init_screens_light(self):
        """✅ Inicializa os widgets (sem carregar dados pesados ainda)"""
        self.home_widget = HomeWidget()
        self.home_widget.set_usuario(self.usuario['nome'])
        self.home_widget.set_main_window(self)
        self.materiais_widget = MateriaisWidget()
        self.maquinas_widget = MaquinasWidget()
        self.movimentacoes_widget = MovimentacoesWidget()
        self.manutencoes_widget = ManutencoesWidget()
        self.pedidos_widget = PedidosWidget()
        self.colaboradores_widget = ColaboradoresWidget()
        self.demandas_widget = DemandasWidget()
        self.relatorios_widget = RelatoriosWidget()
        self.usuarios_widget = UsuariosWidget()
        self.parametros_widget = ParametrosWidget()

        self.content_stack.addWidget(self.home_widget)
        self.content_stack.addWidget(self.materiais_widget)
        self.content_stack.addWidget(self.maquinas_widget)
        self.content_stack.addWidget(self.movimentacoes_widget)
        self.content_stack.addWidget(self.manutencoes_widget)
        self.content_stack.addWidget(self.pedidos_widget)
        self.content_stack.addWidget(self.colaboradores_widget)
        self.content_stack.addWidget(self.demandas_widget)
        self.content_stack.addWidget(self.relatorios_widget)
        self.content_stack.addWidget(self.usuarios_widget)
        self.content_stack.addWidget(self.parametros_widget)

    def load_background_data(self):
        """✅ Carrega dados estáticos em segundo plano"""
        def on_dados_carregados(result):
            if result:
                print(f"✅ Dados de fundo carregados: {len(result.get('empresas', []))} empresas")

        def load_all():
            return {
                'empresas': api_client.get_empresas(),
                'departamentos': api_client.get_departamentos(),
                'categorias': api_client.get_categorias(),
                'cargos': api_client.get_cargos_lista(),
            }

        self.loader_thread = DataLoaderThread(load_all)
        self.loader_thread.finished.connect(on_dados_carregados)
        self.loader_thread.start()

    # =====================================================
    # MÉTODOS DE NAVEGAÇÃO - COM CARREGAMENTO SOB DEMANDA
    # =====================================================

    def show_home(self):
        self.content_stack.setCurrentWidget(self.home_widget)
        self.home_widget.on_show()

    def refresh_home_dashboard(self):
        """Atualiza os cards da home sem depender de navegacao manual."""
        if hasattr(self, "home_widget"):
            self.home_widget.carregar_dados()

    def show_notification_center(self):
        """Abre a Central de Notificações"""
        from widgets.notification_center import NotificationCenter
        self.notification_center = NotificationCenter(self)
        self.notification_center.show()

    def show_materiais(self):
        self.content_stack.setCurrentWidget(self.materiais_widget)
        self.materiais_widget.on_show()

    def show_maquinas(self):
        self.content_stack.setCurrentWidget(self.maquinas_widget)
        self.maquinas_widget.on_show()

    def show_movimentacoes(self):
        self.content_stack.setCurrentWidget(self.movimentacoes_widget)
        self.movimentacoes_widget.on_show()

    def show_manutencoes(self):
        self.content_stack.setCurrentWidget(self.manutencoes_widget)
        self.manutencoes_widget.on_show()

    def show_pedidos(self):
        self.content_stack.setCurrentWidget(self.pedidos_widget)
        self.pedidos_widget.on_show()

    def show_colaboradores(self):
        self.content_stack.setCurrentWidget(self.colaboradores_widget)
        self.colaboradores_widget.on_show()

    def show_demandas(self):
        self.content_stack.setCurrentWidget(self.demandas_widget)
        self.demandas_widget.on_show()

    def show_relatorios(self):
        self.content_stack.setCurrentWidget(self.relatorios_widget)
        self.relatorios_widget.on_show()

    def show_usuarios(self):
        self.content_stack.setCurrentWidget(self.usuarios_widget)
        self.usuarios_widget.on_show()

    def show_parametros(self):
        self.content_stack.setCurrentWidget(self.parametros_widget)
        self.parametros_widget.on_show()

    def show_updates(self):
        """Exibe a tela de atualizações"""
        from widgets.update_widget import UpdateWidget
        self.update_widget = UpdateWidget(self)
        self.content_stack.addWidget(self.update_widget)
        self.content_stack.setCurrentWidget(self.update_widget)

    def trocar_usuario(self):
        """Troca o usuário atual (volta para tela de login)"""
        confirm = QMessageBox.question(
            self,
            "Trocar Usuário",
            "Deseja realmente trocar de usuário?\n\nVocê precisará fazer login novamente.",
            QMessageBox.Yes | QMessageBox.No
        )

        if confirm == QMessageBox.Yes:
            # Limpar token
            api_client.set_token(None)

            # Fechar janela atual
            self.close()

            # Abrir tela de login novamente
            from main import show_login
            show_login()

    def sair(self):
        """Sai do sistema"""
        confirm = QMessageBox.question(
            self,
            "Sair",
            "Deseja realmente sair do sistema?",
            QMessageBox.Yes | QMessageBox.No
        )

        if confirm == QMessageBox.Yes:
            # Limpar token
            api_client.set_token(None)

            # Fechar aplicação
            self.close()
            QApplication.quit()

