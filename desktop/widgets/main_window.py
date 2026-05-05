from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                                QPushButton, QLabel, QFrame, QStackedWidget, QMessageBox, QApplication,
                                QScrollArea)
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
from widgets.access_denied_widget import AccessDeniedWidget
from widgets.notification_badge import NotificationBadge
from access_control import get_role_label, get_screen_label, has_screen_access, normalize_access_level
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
        self.nivel_acesso = normalize_access_level(usuario.get("nivel_acesso"))
        self.update_widget = None
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
        self.show_home()

    def set_active_menu(self, screen_key=None):
        """Marca o menu como ativo visualmente"""
        for key, btn in self.menu_buttons.items():
            if screen_key and key == screen_key:
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

        menu_container = QWidget()
        menu_layout = QVBoxLayout(menu_container)
        menu_layout.setContentsMargins(12, 12, 12, 0)
        menu_layout.setSpacing(6)

        # Botões do menu
        menus = [
            ("home", "🏠 Home", self.show_home),
            ("materiais", "📦 Materiais", self.show_materiais),
            ("maquinas", "🖥️ Máquinas", self.show_maquinas),
            ("movimentacoes", "📊 Movimentações", self.show_movimentacoes),
            ("manutencoes", "🔧 Manutenções", self.show_manutencoes),
            ("pedidos", "📋 Pedidos", self.show_pedidos),
            ("colaboradores", "👥 Colaboradores", self.show_colaboradores),
            ("demandas", "🎫 Demandas", self.show_demandas),
            ("relatorios", "📈 Relatórios", self.show_relatorios),
            ("usuarios", "👥 Usuários", self.show_usuarios),
            ("parametros", "⚙️ Parâmetros", self.show_parametros),
            ("updates", "🔄 Atualizações", self.show_updates),
        ]

        self.menu_buttons = {}
        for screen_key, text, callback in menus:
            if not has_screen_access(self.usuario, screen_key):
                continue
            btn = QPushButton(text)
            btn.setProperty("class", "menu-button")
            btn.setProperty("active", False)
            btn.setProperty("keyboardNavigationTarget", True)
            btn.clicked.connect(lambda checked=False, cb=callback: cb())
            btn.setFixedHeight(48)
            btn.setFocusPolicy(Qt.NoFocus)
            menu_layout.addWidget(btn)
            self.menu_buttons[screen_key] = btn

        menu_scroll = QScrollArea()
        menu_scroll.setObjectName("sidebarScrollArea")
        menu_scroll.setFrameShape(QFrame.NoFrame)
        menu_scroll.setWidgetResizable(True)
        menu_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        menu_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        menu_scroll.setWidget(menu_container)

        layout.addWidget(menu_scroll, 1)

        bottom_container = QWidget()
        bottom_layout = QVBoxLayout(bottom_container)
        bottom_layout.setContentsMargins(12, 0, 12, 12)
        bottom_layout.setSpacing(6)

        # botão de Notificações
        self.notification_btn = NotificationBadge()
        self.notification_btn.clicked.connect(self.show_notification_center)
        bottom_layout.addWidget(self.notification_btn)

        # Atualizar contador inicial
        self.notification_btn.atualizar_contador()

        # Botão Trocar Usuário
        btn_trocar_usuario = QPushButton("🔄 Trocar Usuário")
        btn_trocar_usuario.setProperty("class", "menu-button-bottom")
        btn_trocar_usuario.setProperty("keyboardNavigationTarget", True)
        btn_trocar_usuario.setFixedHeight(48)
        btn_trocar_usuario.setFocusPolicy(Qt.NoFocus)
        btn_trocar_usuario.clicked.connect(self.trocar_usuario)
        bottom_layout.addWidget(btn_trocar_usuario)

        # Botão Sair
        btn_sair = QPushButton("🚪 Sair")
        btn_sair.setProperty("class", "menu-button-bottom")
        btn_sair.setProperty("keyboardNavigationTarget", True)
        btn_sair.setFixedHeight(48)
        btn_sair.setFocusPolicy(Qt.NoFocus)
        btn_sair.clicked.connect(self.sair)
        bottom_layout.addWidget(btn_sair)

        # Rodapé
        footer = QLabel(f'v{get_version()}')
        footer.setAlignment(Qt.AlignCenter)
        footer.setProperty('class', 'footer')
        bottom_layout.addWidget(footer)

        layout.addWidget(bottom_container)

        return sidebar

    def init_screens_light(self):
        """✅ Inicializa os widgets (sem carregar dados pesados ainda)"""
        self.home_widget = HomeWidget()
        self.home_widget.set_usuario(self.usuario['nome'])
        self.home_widget.set_usuario_context(self.usuario)
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
        self.access_denied_widget = AccessDeniedWidget(on_back_home=self.show_home)
        for widget in (
            self.materiais_widget,
            self.maquinas_widget,
            self.movimentacoes_widget,
            self.manutencoes_widget,
            self.pedidos_widget,
            self.colaboradores_widget,
            self.demandas_widget,
            self.relatorios_widget,
        ):
            if hasattr(widget, "set_usuario"):
                widget.set_usuario(self.usuario)

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
        self.content_stack.addWidget(self.access_denied_widget)

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

    def _show_screen(self, screen_key, widget, on_show=None):
        if not has_screen_access(self.usuario, screen_key):
            self.show_access_denied(screen_key)
            return False

        self.content_stack.setCurrentWidget(widget)
        if callable(on_show):
            on_show()
        self.set_active_menu(screen_key)
        return True

    def show_access_denied(self, screen_key):
        screen_label = get_screen_label(screen_key)
        role_label = get_role_label(self.nivel_acesso)
        self.access_denied_widget.configure(screen_label, role_label)
        self.content_stack.setCurrentWidget(self.access_denied_widget)
        self.set_active_menu()

    def show_home(self):
        self._show_screen("home", self.home_widget, self.home_widget.on_show)

    def refresh_home_dashboard(self):
        """Atualiza os cards da home sem depender de navegacao manual."""
        if hasattr(self, "home_widget"):
            self.home_widget.carregar_dados()

    def show_notification_center(self):
        """Abre a Central de Notificações"""
        if not has_screen_access(self.usuario, "notificacoes"):
            self.show_access_denied("notificacoes")
            return

        from widgets.notification_center import NotificationCenter
        self.notification_center = NotificationCenter(self)
        self.notification_center.show()

    def show_materiais(self):
        self._show_screen("materiais", self.materiais_widget, self.materiais_widget.on_show)

    def show_maquinas(self):
        self._show_screen("maquinas", self.maquinas_widget, self.maquinas_widget.on_show)

    def show_movimentacoes(self):
        self._show_screen("movimentacoes", self.movimentacoes_widget, self.movimentacoes_widget.on_show)

    def show_manutencoes(self):
        self._show_screen("manutencoes", self.manutencoes_widget, self.manutencoes_widget.on_show)

    def show_pedidos(self):
        self._show_screen("pedidos", self.pedidos_widget, self.pedidos_widget.on_show)

    def show_colaboradores(self):
        self._show_screen("colaboradores", self.colaboradores_widget, self.colaboradores_widget.on_show)

    def show_demandas(self):
        self._show_screen("demandas", self.demandas_widget, self.demandas_widget.on_show)

    def show_relatorios(self):
        self._show_screen("relatorios", self.relatorios_widget, self.relatorios_widget.on_show)

    def show_usuarios(self):
        self._show_screen("usuarios", self.usuarios_widget, self.usuarios_widget.on_show)

    def show_parametros(self):
        self._show_screen("parametros", self.parametros_widget, self.parametros_widget.on_show)

    def show_updates(self):
        """Exibe a tela de atualizações"""
        if not has_screen_access(self.usuario, "updates"):
            self.show_access_denied("updates")
            return

        if self.update_widget is None:
            from widgets.update_widget import UpdateWidget
            self.update_widget = UpdateWidget(self)
            self.content_stack.addWidget(self.update_widget)

        self._show_screen("updates", self.update_widget)

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
