from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QFormLayout, QLineEdit,
                               QComboBox, QSpinBox, QCheckBox, QGroupBox,
                               QTabWidget, QMessageBox, QTableWidget,
                               QTableWidgetItem, QHeaderView, QDialog,
                               QDialogButtonBox, QFrame, QScrollArea, QTextEdit,
                               QTimeEdit, QApplication)
from PySide6.QtCore import Qt, QTimer, QTime
from PySide6.QtGui import QFont, QColor, QCursor
from api_client import api_client
from accessibility_manager import (
    DEFAULT_ACCESSIBILITY_CONFIG,
    apply_accessibility_config,
    build_accessibility_config,
    get_accessibility_options,
    get_screen_resolution_context,
    save_local_accessibility_config,
)
from widgets.toast_notification import notification_manager
from widgets.table_utils import configure_data_table, number_item
from user_preferences import get_widget_preferences, save_widget_preferences
import socket
import requests
from datetime import datetime
import os
import sys
import subprocess
import unicodedata


class ParametrosWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.usuario = {}
        self._restoring_tab_state = False
        # Inicializar listas vazias (serÃƒÂ£o carregadas do backend)
        self.empresas = []
        self.departamentos = []
        self.categorias = []
        self._loaded = False  # Ã¢Å“â€¦ Flag para carregamento sob demanda
        self._loading_configuracoes = False
        self.departamentos_detalhados = []
        self.cargos_detalhados = []
        self.init_ui()
        # Ã¢Å¡Â Ã¯Â¸Â NÃƒÆ’O carregar dados aqui - serÃƒÂ¡ feito no on_show()

    def on_show(self):
        """Ã¢Å“â€¦ Chamado quando a aba ÃƒÂ© selecionada - carrega dados sob demanda"""
        if not self._loaded:
            # Carregar listas de empresas, departamentos, categorias
            self.carregar_listas()
            # Carregar configuraÃƒÂ§ÃƒÂµes salvas
            self.carregar_configuracoes()
            # Carregar informaÃƒÂ§ÃƒÂµes do servidor
            self.carregar_info_servidor()
            # Carregar lista de backups
            self.carregar_lista_backups()
            self._loaded = True

    def set_usuario(self, usuario):
        self.usuario = usuario or {}
        self._restore_saved_tab()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(24, 24, 24, 24)

        titulo = QLabel("Parâmetros do Sistema")
        titulo.setProperty("class", "page-title")
        layout.addWidget(titulo)

        self.tabs = QTabWidget()
        self.tabs.setObjectName("paramTabs")
        self.tabs.currentChanged.connect(self.on_tab_changed)

        tab_geral = self.create_tab_geral()
        self.tabs.addTab(tab_geral, "Configurações Gerais")

        tab_acessibilidade = self.create_tab_acessibilidade()
        self.tabs.addTab(tab_acessibilidade, "Acessibilidade")

        tab_notificacoes = self.create_tab_notificacoes()
        self.tabs.addTab(tab_notificacoes, "Notificações")

        tab_empresas = self.create_tab_empresas()
        self.tabs.addTab(tab_empresas, "Empresas")

        tab_departamentos = self.create_tab_departamentos()
        self.tabs.addTab(tab_departamentos, "Departamentos")

        tab_categorias = self.create_tab_categorias()
        self.tabs.addTab(tab_categorias, "Categorias")

        tab_cargos = self.create_tab_cargos()
        self.tabs.addTab(tab_cargos, "Cargos")

        tab_backup = self.create_tab_backup()
        self.tabs.addTab(tab_backup, "Backup")

        tab_servidor = self.create_tab_servidor()
        self.tabs.addTab(tab_servidor, "Servidor")

        layout.addWidget(self.tabs)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.btn_salvar = QPushButton("Salvar Configurações")
        self.btn_salvar.setObjectName("btnPrimary")
        self.btn_salvar.clicked.connect(self.salvar_configuracoes)
        btn_layout.addWidget(self.btn_salvar)

        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.setObjectName("btnSecondary")
        self.btn_cancelar.clicked.connect(self.cancelar)
        btn_layout.addWidget(self.btn_cancelar)

        layout.addLayout(btn_layout)

    def _restore_saved_tab(self):
        if not hasattr(self, "tabs"):
            return

        preferences = get_widget_preferences(self.usuario, "parametros")
        active_tab = preferences.get("active_tab")
        if not isinstance(active_tab, str):
            return

        for index in range(self.tabs.count()):
            if self.tabs.tabText(index) == active_tab:
                self._restoring_tab_state = True
                try:
                    self.tabs.setCurrentIndex(index)
                finally:
                    self._restoring_tab_state = False
                return

    def _save_active_tab(self):
        if not hasattr(self, "tabs"):
            return

        current_index = self.tabs.currentIndex()
        if current_index < 0:
            return

        preferences = get_widget_preferences(self.usuario, "parametros")
        preferences["active_tab"] = self.tabs.tabText(current_index)
        save_widget_preferences(self.usuario, "parametros", preferences)

    def on_tab_changed(self, index):
        if index < 0:
            return
        if not self._restoring_tab_state:
            self._save_active_tab()

    def create_tab_geral(self):
        """Aba de configuracoes gerais"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(20)

        grupo_sistema = QGroupBox("Configurações do Sistema")
        grupo_sistema.setObjectName("configGroup")
        form_sistema = QFormLayout(grupo_sistema)
        form_sistema.setContentsMargins(20, 20, 20, 20)

        self.nome_sistema = QLineEdit("Project Parallel")
        self.nome_sistema.setReadOnly(True)
        self.nome_sistema.setObjectName("configInputReadonly")
        form_sistema.addRow("Nome do Sistema:", self.nome_sistema)

        self.empresa_padrao = QComboBox()
        self.empresa_padrao.setObjectName("configCombo")
        form_sistema.addRow("Empresa Padrão:", self.empresa_padrao)

        layout.addWidget(grupo_sistema)

        grupo_estoque = QGroupBox("Configurações de Estoque")
        grupo_estoque.setObjectName("configGroup")
        form_estoque = QFormLayout(grupo_estoque)
        form_estoque.setContentsMargins(20, 20, 20, 20)

        self.alerta_estoque = QSpinBox()
        self.alerta_estoque.setObjectName("configSpin")
        self.alerta_estoque.setRange(0, 100)
        self.alerta_estoque.setValue(5)
        self.alerta_estoque.setSuffix(" unidades")
        form_estoque.addRow("Alerta de Estoque Baixo:", self.alerta_estoque)

        self.alerta_estoque_critico = QSpinBox()
        self.alerta_estoque_critico.setObjectName("configSpin")
        self.alerta_estoque_critico.setRange(0, 100)
        self.alerta_estoque_critico.setValue(2)
        self.alerta_estoque_critico.setSuffix(" unidades")
        form_estoque.addRow("Alerta de Estoque Crítico:", self.alerta_estoque_critico)

        layout.addWidget(grupo_estoque)

        grupo_backup = QGroupBox("Configurações de Backup")
        grupo_backup.setObjectName("configGroup")
        form_backup = QFormLayout(grupo_backup)
        form_backup.setContentsMargins(20, 20, 20, 20)

        self.backup_automatico = QCheckBox("Realizar backup automático")
        self.backup_automatico.setObjectName("configCheckbox")
        self.backup_automatico.setChecked(True)
        form_backup.addRow("", self.backup_automatico)

        self.frequencia_backup = QComboBox()
        self.frequencia_backup.setObjectName("configCombo")
        self.frequencia_backup.addItems(["Diário", "Semanal", "Mensal"])
        form_backup.addRow("Frequência:", self.frequencia_backup)

        self.horario_backup = QTimeEdit()
        self.horario_backup.setTime(QTime(2, 0))
        form_backup.addRow("Horário:", self.horario_backup)

        self.dias_retencao = QSpinBox()
        self.dias_retencao.setRange(7, 365)
        self.dias_retencao.setValue(30)
        self.dias_retencao.setSuffix(" dias")
        form_backup.addRow("Reter backups por:", self.dias_retencao)

        layout.addWidget(grupo_backup)
        layout.addStretch()
        return widget

    def _wrap_tab_scroll_area(self, content_widget):
        scroll = QScrollArea()
        scroll.setObjectName("paramTabScrollArea")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setWidget(content_widget)
        return scroll

    def create_tab_acessibilidade(self):
        """Aba de acessibilidade e interface"""
        content = QWidget()
        content.setObjectName("paramTabScrollContent")
        layout = QVBoxLayout(content)
        layout.setSpacing(20)
        layout.setContentsMargins(0, 0, 0, 12)
        options = get_accessibility_options()

        grupo_acessibilidade = QGroupBox("Acessibilidade e Interface")
        grupo_acessibilidade.setObjectName("configGroup")
        form_acessibilidade = QFormLayout(grupo_acessibilidade)
        form_acessibilidade.setContentsMargins(20, 20, 20, 20)
        form_acessibilidade.setVerticalSpacing(14)

        self.tema_interface = QComboBox()
        self.tema_interface.setObjectName("configCombo")
        self.tema_interface.addItems(options["tema"])
        form_acessibilidade.addRow("Tema:", self.tema_interface)

        self.tamanho_fonte = QComboBox()
        self.tamanho_fonte.setObjectName("configCombo")
        self.tamanho_fonte.addItems(options["tamanho_fonte"])
        form_acessibilidade.addRow("Tamanho da fonte:", self.tamanho_fonte)

        self.escala_interface = QComboBox()
        self.escala_interface.setObjectName("configCombo")
        self.escala_interface.addItems(options["escala_interface"])
        form_acessibilidade.addRow("Escala da interface:", self.escala_interface)

        self.navegacao_teclado = QCheckBox("Destacar foco e priorizar navegação por teclado")
        self.navegacao_teclado.setObjectName("configCheckbox")
        layout_navegacao = QHBoxLayout()
        layout_navegacao.setContentsMargins(0, 0, 0, 0)
        layout_navegacao.addWidget(self.navegacao_teclado)
        layout_navegacao.addStretch()
        form_acessibilidade.addRow("Navegação por teclado:", layout_navegacao)

        self.tema_interface.currentTextChanged.connect(self.previsualizar_acessibilidade)
        self.tamanho_fonte.currentTextChanged.connect(self.previsualizar_acessibilidade)
        self.escala_interface.currentTextChanged.connect(self.previsualizar_acessibilidade)
        self.navegacao_teclado.toggled.connect(self.previsualizar_acessibilidade)

        dica = QLabel(
            "As alterações são aplicadas em tempo real. Use 90% e 100% para telas compactas, e 150% ou 175% para monitores maiores. Salve para manter após reiniciar o sistema."
        )
        dica.setWordWrap(True)
        dica.setStyleSheet("color: #64748b;")

        self.resolucao_detectada_label = QLabel("")
        self.resolucao_detectada_label.setWordWrap(True)
        self.resolucao_detectada_label.setStyleSheet("color: #64748b;")

        botoes_layout = QHBoxLayout()
        botoes_layout.addStretch()
        btn_automatico = QPushButton("Usar recomendação da máquina")
        btn_automatico.setObjectName("btnSecondary")
        btn_automatico.clicked.connect(self.aplicar_escala_automatica)
        botoes_layout.addWidget(btn_automatico)
        btn_restaurar = QPushButton("Restaurar padrão")
        btn_restaurar.setObjectName("btnSecondary")
        btn_restaurar.clicked.connect(self.restaurar_acessibilidade_padrao)
        botoes_layout.addWidget(btn_restaurar)

        layout.addWidget(grupo_acessibilidade)
        layout.addWidget(dica)
        layout.addWidget(self.resolucao_detectada_label)
        layout.addWidget(self._create_accessibility_context_group())
        layout.addWidget(self._create_accessibility_preview_group())
        layout.addLayout(botoes_layout)
        layout.addStretch()
        self._refresh_resolution_hint()
        return self._wrap_tab_scroll_area(content)

    def _create_accessibility_context_group(self):
        grupo_contexto = QGroupBox("Leitura da máquina")
        grupo_contexto.setObjectName("configGroup")
        layout = QFormLayout(grupo_contexto)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        self.resolucao_valor = QLabel("-")
        self.escala_aplicada_valor = QLabel("-")
        self.dpi_valor = QLabel("-")
        self.recomendacao_tela_valor = QLabel("-")
        self.recomendacao_tela_valor.setWordWrap(True)

        layout.addRow("Resolução detectada:", self.resolucao_valor)
        layout.addRow("Escala aplicada:", self.escala_aplicada_valor)
        layout.addRow("DPI lógico:", self.dpi_valor)
        layout.addRow("Leitura sugerida:", self.recomendacao_tela_valor)

        return grupo_contexto

    def _create_accessibility_preview_group(self):
        grupo_preview = QGroupBox("Pré-visualização")
        grupo_preview.setObjectName("configGroup")
        layout = QVBoxLayout(grupo_preview)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        titulo = QLabel("Visualização das configurações")
        titulo.setStyleSheet("font-size: 18px; font-weight: 600; margin-bottom: 0px;")
        layout.addWidget(titulo)

        descricao = QLabel(
            "Use esta área para validar contraste, leitura e foco antes de salvar."
        )
        descricao.setWordWrap(True)
        layout.addWidget(descricao)

        linha_campos = QHBoxLayout()
        linha_campos.setSpacing(12)

        self.preview_busca = QLineEdit()
        self.preview_busca.setPlaceholderText("Campo de exemplo")
        linha_campos.addWidget(self.preview_busca)

        self.preview_combo = QComboBox()
        self.preview_combo.addItems(["Opção A", "Opção B", "Opção C"])
        linha_campos.addWidget(self.preview_combo)

        layout.addLayout(linha_campos)

        self.preview_checkbox = QCheckBox("Exibir indicador de foco no teclado")
        self.preview_checkbox.setObjectName("configCheckbox")
        layout.addWidget(self.preview_checkbox)

        self.preview_tabela = QTableWidget(2, 2)
        self.preview_tabela.setHorizontalHeaderLabels(["Campo", "Valor exibido"])
        self.preview_tabela.verticalHeader().setVisible(False)
        self.preview_tabela.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.preview_tabela.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.preview_tabela.setEditTriggers(QTableWidget.NoEditTriggers)
        self.preview_tabela.setSelectionMode(QTableWidget.NoSelection)
        self.preview_tabela.setFocusPolicy(Qt.NoFocus)
        self.preview_tabela.setMinimumHeight(110)
        self.preview_tabela.setItem(0, 0, QTableWidgetItem("Departamento"))
        self.preview_tabela.setItem(0, 1, QTableWidgetItem("Administrativo e Operações"))
        self.preview_tabela.setItem(1, 0, QTableWidgetItem("Observação"))
        self.preview_tabela.setItem(1, 1, QTableWidgetItem("Texto de referência para validar leitura, espaço e contraste."))
        self.preview_tabela.resizeRowsToContents()
        layout.addWidget(self.preview_tabela)

        linha_botoes = QHBoxLayout()
        linha_botoes.setSpacing(12)

        self.preview_btn_primary = QPushButton("Acao principal")
        self.preview_btn_primary.setObjectName("btnPrimary")
        linha_botoes.addWidget(self.preview_btn_primary)

        self.preview_btn_secondary = QPushButton("Acao secundaria")
        self.preview_btn_secondary.setObjectName("btnSecondary")
        linha_botoes.addWidget(self.preview_btn_secondary)

        linha_botoes.addStretch()
        layout.addLayout(linha_botoes)

        return grupo_preview

    def aplicar_escala_automatica(self):
        self._loading_configuracoes = True
        try:
            self._set_combo_value(self.escala_interface, "Automatica")
        finally:
            self._loading_configuracoes = False

        self.previsualizar_acessibilidade()
        notification_manager.info("Escala automática aplicada para esta máquina.", self.window(), 2500)

    def restaurar_acessibilidade_padrao(self):
        self._loading_configuracoes = True
        try:
            self._set_combo_value(self.tema_interface, DEFAULT_ACCESSIBILITY_CONFIG["tema"])
            self._set_combo_value(self.tamanho_fonte, DEFAULT_ACCESSIBILITY_CONFIG["tamanho_fonte"])
            self._set_combo_value(self.escala_interface, DEFAULT_ACCESSIBILITY_CONFIG["escala_interface"])
            self.navegacao_teclado.setChecked(DEFAULT_ACCESSIBILITY_CONFIG["navegacao_teclado"])
        finally:
            self._loading_configuracoes = False

        self.previsualizar_acessibilidade()
        self._refresh_resolution_hint()
        notification_manager.info("Acessibilidade restaurada para o padrão.", self.window(), 2500)

    def create_tab_backup(self):
        """Aba de gerenciamento de backup"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)

        grupo_manual = QGroupBox("Backup Manual")
        grupo_manual.setObjectName("configGroup")
        manual_layout = QVBoxLayout(grupo_manual)
        manual_layout.setContentsMargins(20, 20, 20, 20)

        btn_executar_backup = QPushButton("Executar Backup Agora")
        btn_executar_backup.setObjectName("btnPrimary")
        btn_executar_backup.setMinimumHeight(40)
        btn_executar_backup.clicked.connect(self.executar_backup_manual)
        manual_layout.addWidget(btn_executar_backup)

        lbl_info = QLabel("O backup será salvo na pasta 'backups' do servidor e compactado em formato .gz")
        lbl_info.setStyleSheet("color: #64748b; font-size: 11px; margin-top: 10px;")
        manual_layout.addWidget(lbl_info)

        layout.addWidget(grupo_manual)

        grupo_lista = QGroupBox("Backups Disponiveis")
        grupo_lista.setObjectName("configGroup")
        lista_layout = QVBoxLayout(grupo_lista)
        lista_layout.setContentsMargins(20, 20, 20, 20)

        # Tabela de backups
        self.tabela_backups = QTableWidget()
        self.tabela_backups.setColumnCount(3)
        self.tabela_backups.setHorizontalHeaderLabels(["Nome do Arquivo", "Data", "Tamanho"])
        self.tabela_backups.verticalHeader().setVisible(False)
        self.tabela_backups.setAlternatingRowColors(True)
        configure_data_table(self.tabela_backups, stretch_columns=(0,))

        self.tabela_backups.setStyleSheet("""
            QTableWidget::item {
                padding: 10px 8px;
            }
            QHeaderView::section {
                padding: 10px 12px;
            }
        """)

        lista_layout.addWidget(self.tabela_backups)

        btn_layout = QHBoxLayout()

        btn_atualizar_lista = QPushButton("Atualizar Lista")
        btn_atualizar_lista.clicked.connect(self.carregar_lista_backups)
        btn_layout.addWidget(btn_atualizar_lista)

        btn_restaurar = QPushButton("Restaurar Backup")
        btn_restaurar.setObjectName("btnWarning")
        btn_restaurar.clicked.connect(self.restaurar_backup_selecionado)
        btn_layout.addWidget(btn_restaurar)

        btn_layout.addStretch()
        lista_layout.addLayout(btn_layout)

        layout.addWidget(grupo_lista)

        return widget

    def executar_backup_manual(self):
        """Executa backup manual"""
        try:
            QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
            success, result = api_client.executar_backup()
            QApplication.restoreOverrideCursor()

            if success:
                notification_manager.success(f"Backup realizado com sucesso!\nArquivo: {result.get('arquivo', 'desconhecido')}", self.window(), 5000)
                self.carregar_lista_backups()
            else:
                notification_manager.error("Erro ao realizar backup", self.window(), 4000)

        except Exception as e:
            QApplication.restoreOverrideCursor()
            notification_manager.error(f"Erro: {e}", self.window(), 4000)

    def carregar_lista_backups(self):
        """Carrega a lista de backups disponíveis"""
        try:
            backups = api_client.listar_backups()
            self.tabela_backups.setRowCount(len(backups))

            for row, backup in enumerate(backups):
                self.tabela_backups.setItem(row, 0, QTableWidgetItem(backup.get("nome", "-")))
                self.tabela_backups.setItem(row, 1, QTableWidgetItem(backup.get("data", "-")))
                self.tabela_backups.setItem(row, 2, QTableWidgetItem(f"{backup.get('tamanho_mb', 0)} MB"))

            self.tabela_backups.resizeColumnsToContents()

        except Exception as e:
            print(f"Erro ao carregar lista de backups: {e}")

    def restaurar_backup_selecionado(self):
        """Restaura o backup selecionado"""
        current_row = self.tabela_backups.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Atenção", "Selecione um backup para restaurar")
            return

        backup_nome = self.tabela_backups.item(current_row, 0).text()
        backup_data = self.tabela_backups.item(current_row, 1).text()

        confirm = QMessageBox.question(
            self,
            "Confirmar restauração",
            f"Tem certeza que deseja restaurar o backup '{backup_nome}'?\n\n"
            f"Data: {backup_data}\n\n"
            f"ATENÇÃO: Esta ação irá SUBSTITUIR todos os dados atuais pelos dados do backup.\n"
            f"Esta ação não pode ser desfeita!",
            QMessageBox.Yes | QMessageBox.No
        )

        if confirm == QMessageBox.Yes:
            try:
                QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
                success, result = api_client.restaurar_backup(backup_nome)
                QApplication.restoreOverrideCursor()

                if success:
                    notification_manager.success("Backup restaurado com sucesso! O sistema será reiniciado.", self.window(), 5000)
                    QTimer.singleShot(2000, self.reiniciar_aplicacao)
                else:
                    notification_manager.error(f"Erro ao restaurar backup: {result.get('detail', 'Erro desconhecido') if result else 'Erro'}", self.window(), 5000)
            except Exception as e:
                QApplication.restoreOverrideCursor()
                notification_manager.error(f"Erro: {e}", self.window(), 4000)

    def reiniciar_aplicacao(self):
        """Reinicia a aplicação após restauração"""
        QMessageBox.information(self, "Reiniciando", "O sistema será reiniciado para aplicar as alterações.")
        if getattr(sys, "frozen", False):
            subprocess.Popen([sys.executable])
        else:
            python = sys.executable
            script = os.path.abspath(sys.argv[0])
            subprocess.Popen([python, script])
        sys.exit(0)

    def create_tab_notificacoes(self):
        """Aba de configuracoes de notificacoes"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(20)

        grupo_notificacoes = QGroupBox("Configurações de Notificações")
        grupo_notificacoes.setObjectName("configGroup")
        form_notificacoes = QFormLayout(grupo_notificacoes)
        form_notificacoes.setContentsMargins(20, 20, 20, 20)

        self.notif_estoque_baixo = QCheckBox("Notificar quando estoque estiver baixo")
        self.notif_estoque_baixo.setObjectName("configCheckbox")
        self.notif_estoque_baixo.setChecked(True)
        form_notificacoes.addRow("Estoque:", self.notif_estoque_baixo)

        self.notif_estoque_critico = QCheckBox("Notificar quando estoque estiver critico")
        self.notif_estoque_critico.setObjectName("configCheckbox")
        self.notif_estoque_critico.setChecked(True)
        form_notificacoes.addRow("Crítico:", self.notif_estoque_critico)

        self.notif_manutencao = QCheckBox("Notificar sobre manutencoes pendentes")
        self.notif_manutencao.setObjectName("configCheckbox")
        self.notif_manutencao.setChecked(True)
        form_notificacoes.addRow("Manutenções:", self.notif_manutencao)

        self.notif_pedidos = QCheckBox("Notificar sobre pedidos pendentes de aprovação")
        self.notif_pedidos.setObjectName("configCheckbox")
        self.notif_pedidos.setChecked(True)
        form_notificacoes.addRow("Pedidos:", self.notif_pedidos)

        self.notif_demandas = QCheckBox("Notificar sobre novas demandas de TI")
        self.notif_demandas.setObjectName("configCheckbox")
        self.notif_demandas.setChecked(True)
        form_notificacoes.addRow("Demandas:", self.notif_demandas)

        self.notif_movimentacoes = QCheckBox("Notificar sobre movimentacoes de alto valor")
        self.notif_movimentacoes.setObjectName("configCheckbox")
        self.notif_movimentacoes.setChecked(False)
        form_notificacoes.addRow("Movimentações:", self.notif_movimentacoes)

        self.valor_alto = QSpinBox()
        self.valor_alto.setRange(0, 100000)
        self.valor_alto.setValue(5000)
        self.valor_alto.setSuffix(" R$")
        form_notificacoes.addRow("Valor mínimo para notificação:", self.valor_alto)

        layout.addWidget(grupo_notificacoes)

        grupo_alertas = QGroupBox("Configurações de Alerta")
        grupo_alertas.setObjectName("configGroup")
        form_alertas = QFormLayout(grupo_alertas)
        form_alertas.setContentsMargins(20, 20, 20, 20)

        self.verificar_alertas_auto = QCheckBox("Verificar alertas automaticamente")
        self.verificar_alertas_auto.setObjectName("configCheckbox")
        self.verificar_alertas_auto.setChecked(True)
        form_alertas.addRow("", self.verificar_alertas_auto)

        self.intervalo_verificacao = QComboBox()
        self.intervalo_verificacao.addItems(["1 minuto", "5 minutos", "15 minutos", "30 minutos", "1 hora"])
        form_alertas.addRow("Intervalo de verificacao:", self.intervalo_verificacao)

        self.tempo_notificacao = QComboBox()
        self.tempo_notificacao.addItems(["3 segundos", "5 segundos", "10 segundos", "30 segundos"])
        form_alertas.addRow("Duração da notificação:", self.tempo_notificacao)

        layout.addWidget(grupo_alertas)

        grupo_silencio = QGroupBox("Modo Não Perturbe")
        grupo_silencio.setObjectName("configGroup")
        form_silencio = QFormLayout(grupo_silencio)
        form_silencio.setContentsMargins(20, 20, 20, 20)

        self.modo_nao_perturbe = QCheckBox("Silenciar notificações visuais e sonoras não críticas")
        self.modo_nao_perturbe.setObjectName("configCheckbox")
        self.modo_nao_perturbe.setChecked(False)
        form_silencio.addRow("", self.modo_nao_perturbe)

        layout.addWidget(grupo_silencio)

        btn_testar = QPushButton("Testar Notificacao")
        btn_testar.clicked.connect(self.testar_notificacao)
        layout.addWidget(btn_testar)

        layout.addStretch()
        return widget


    def create_tab_empresas(self):
        """Aba de gerenciamento de empresas"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        self.tabela_empresas = QTableWidget()
        self.tabela_empresas.setColumnCount(2)
        self.tabela_empresas.setHorizontalHeaderLabels(["ID", "Nome da Empresa"])
        self.tabela_empresas.verticalHeader().setVisible(False)
        configure_data_table(self.tabela_empresas, stretch_columns=(1,))

        self.tabela_empresas.setStyleSheet("""
            QTableWidget::item {
                padding: 10px 8px;
            }
            QHeaderView::section {
                padding: 10px 12px;
            }
        """)
        self.tabela_empresas.itemDoubleClicked.connect(lambda _: self.editar_empresa())

        # Ã¢Å¡Â Ã¯Â¸Â NÃƒÆ’O carregar dados aqui - serÃƒÂ¡ feito no carregar_listas()

        layout.addWidget(self.tabela_empresas)

        btn_layout = QHBoxLayout()
        btn_adicionar = QPushButton("+ Adicionar Empresa")
        btn_adicionar.clicked.connect(self.adicionar_empresa)
        btn_layout.addWidget(btn_adicionar)

        btn_editar = QPushButton("Editar Empresa")
        btn_editar.clicked.connect(self.editar_empresa)
        btn_layout.addWidget(btn_editar)

        btn_remover = QPushButton("- Remover Empresa")
        btn_remover.clicked.connect(self.remover_empresa)
        btn_layout.addWidget(btn_remover)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        return widget

    def create_tab_departamentos(self):
        """Aba de gerenciamento de departamentos"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        self.tabela_departamentos = QTableWidget()
        self.tabela_departamentos.setColumnCount(3)
        self.tabela_departamentos.setHorizontalHeaderLabels(["ID", "Departamento", "Status"])
        configure_data_table(self.tabela_departamentos, stretch_columns=(1,))
        self.tabela_departamentos.verticalHeader().setVisible(False)

        self.tabela_departamentos.setStyleSheet("""
            QTableWidget::item {
                padding: 10px 8px;
            }
            QHeaderView::section {
                padding: 10px 12px;
            }
        """)
        self.tabela_departamentos.itemDoubleClicked.connect(lambda _: self.editar_departamento())

        # Ã¢Å¡Â Ã¯Â¸Â NÃƒÆ’O carregar dados aqui - serÃƒÂ¡ feito no carregar_listas()

        layout.addWidget(self.tabela_departamentos)

        btn_layout = QHBoxLayout()
        btn_adicionar = QPushButton("+ Adicionar Departamento")
        btn_adicionar.clicked.connect(self.adicionar_departamento)
        btn_layout.addWidget(btn_adicionar)

        btn_editar = QPushButton("Editar Departamento")
        btn_editar.clicked.connect(self.editar_departamento)
        btn_layout.addWidget(btn_editar)

        btn_remover = QPushButton("- Remover Departamento")
        btn_remover.clicked.connect(self.remover_departamento)
        btn_layout.addWidget(btn_remover)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        return widget

    def create_tab_categorias(self):
        """Aba de gerenciamento de categorias"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        self.tabela_categorias = QTableWidget()
        self.tabela_categorias.setColumnCount(2)
        self.tabela_categorias.setHorizontalHeaderLabels(["ID", "Categoria"])
        configure_data_table(self.tabela_categorias, stretch_columns=(1,))
        self.tabela_categorias.verticalHeader().setVisible(False)

        self.tabela_categorias.setStyleSheet("""
            QTableWidget::item {
                padding: 10px 8px;
            }
            QHeaderView::section {
                padding: 10px 12px;
            }
        """)
        self.tabela_categorias.itemDoubleClicked.connect(lambda _: self.editar_categoria())

        # Ã¢Å¡Â Ã¯Â¸Â NÃƒÆ’O carregar dados aqui - serÃƒÂ¡ feito no carregar_listas()

        layout.addWidget(self.tabela_categorias)

        btn_layout = QHBoxLayout()
        btn_adicionar = QPushButton("+ Adicionar Categoria")
        btn_adicionar.clicked.connect(self.adicionar_categoria)
        btn_layout.addWidget(btn_adicionar)

        btn_editar = QPushButton("Editar Categoria")
        btn_editar.clicked.connect(self.editar_categoria)
        btn_layout.addWidget(btn_editar)

        btn_remover = QPushButton("- Remover Categoria")
        btn_remover.clicked.connect(self.remover_categoria)
        btn_layout.addWidget(btn_remover)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        return widget

    def create_tab_cargos(self):
        """Aba de gerenciamento de cargos"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        self.tabela_cargos = QTableWidget()
        self.tabela_cargos.setColumnCount(3)
        self.tabela_cargos.setHorizontalHeaderLabels(['ID', 'Cargo', 'Status'])
        configure_data_table(self.tabela_cargos, stretch_columns=(1,))
        self.tabela_cargos.verticalHeader().setVisible(False)

        self.tabela_cargos.setStyleSheet("""
            QTableWidget::item {
                padding: 10px 8px;
            }
            QHeaderView::section {
                padding: 10px 12px;
            }
        """)
        self.tabela_cargos.itemDoubleClicked.connect(lambda _: self.editar_cargo())

        layout.addWidget(self.tabela_cargos)

        btn_layout = QHBoxLayout()
        btn_adicionar = QPushButton('+ Adicionar Cargo')
        btn_adicionar.clicked.connect(self.adicionar_cargo)
        btn_layout.addWidget(btn_adicionar)

        btn_editar = QPushButton('Editar Cargo')
        btn_editar.clicked.connect(self.editar_cargo)
        btn_layout.addWidget(btn_editar)

        btn_remover = QPushButton('- Remover Cargo')
        btn_remover.clicked.connect(self.remover_cargo)
        btn_layout.addWidget(btn_remover)

        btn_refresh = QPushButton('Atualizar')
        btn_refresh.clicked.connect(self.carregar_tabela_cargos)
        btn_layout.addWidget(btn_refresh)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # Ã¢Å¡Â Ã¯Â¸Â NÃƒÆ’O carregar dados aqui - serÃƒÂ¡ feito no carregar_listas()

        return widget

    def create_tab_servidor(self):
        """Aba de informacoes do servidor"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)

        info_frame = QFrame()
        info_frame.setObjectName("infoCard")
        info_frame.setStyleSheet("""
            QFrame#infoCard {
                background-color: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 16px;
                padding: 20px;
            }
        """)
        info_layout = QVBoxLayout(info_frame)

        titulo_servidor = QLabel("Informacoes do Servidor")
        titulo_servidor.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        info_layout.addWidget(titulo_servidor)

        info_layout.addSpacing(10)

        self.status_api = QLabel("Status da API: Verificando...")
        info_layout.addWidget(self.status_api)

        self.endereco_server = QLabel(f"Endereco Local: {self.get_ip_local()}")
        info_layout.addWidget(self.endereco_server)

        self.porta_server = QLabel("Porta: 8000")
        info_layout.addWidget(self.porta_server)

        self.status_banco = QLabel("Banco de Dados: Verificando...")
        info_layout.addWidget(self.status_banco)

        self.api_versao = QLabel("Versão da API: Verificando...")
        info_layout.addWidget(self.api_versao)

        layout.addWidget(info_frame)

        btn_testar = QPushButton("Testar Conexão")
        btn_testar.clicked.connect(self.carregar_info_servidor)
        layout.addWidget(btn_testar)

        layout.addStretch()

        self.timer_servidor = QTimer()
        self.timer_servidor.timeout.connect(self.carregar_info_servidor)
        self.timer_servidor.start(30000)

        return widget

    # =====================================================
    # CARREGAMENTO DE LISTAS DO BACKEND
    # =====================================================

    def carregar_listas(self):
        """Carrega empresas, departamentos e categorias do backend"""
        try:
            QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))

            self.empresas = api_client.get_empresas()
            self.departamentos = api_client.get_departamentos()
            self.categorias = api_client.get_categorias()

            if not self.empresas:
                self.empresas = ["Matriz", "Filial 1", "Filial 2", "Filial 3"]
            if not self.departamentos:
                self.departamentos = ["TI", "Administrativo", "Financeiro", "RH", "Comercial", "Marketing", "Logística"]
            if not self.categorias:
                self.categorias = ["Periféricos", "Hardware", "Armazenamento", "Monitores", "Cabos", "Redes", "Consumíveis", "Softwares"]

            self.carregar_tabela_empresas()
            self.carregar_tabela_departamentos()
            self.carregar_tabela_categorias()
            self.carregar_tabela_cargos()
            self.atualizar_combos()

            QApplication.restoreOverrideCursor()

        except Exception as e:
            QApplication.restoreOverrideCursor()
            print(f"Ã¢ÂÅ’ Erro ao carregar listas: {e}")
            notification_manager.error(f"Erro ao carregar listas: {e}", self.window(), 3000)

    def atualizar_combos(self):
        """Atualiza todos os comboboxes com as listas carregadas"""
        if hasattr(self, 'empresa_padrao'):
            current = self.empresa_padrao.currentText()
            self.empresa_padrao.clear()
            self.empresa_padrao.addItems(self.empresas)
            if current in self.empresas:
                self.empresa_padrao.setCurrentText(current)

    # =====================================================
    # CARREGAMENTO DE TABELAS
    # =====================================================

    def carregar_tabela_empresas(self):
        sorting_enabled = self.tabela_empresas.isSortingEnabled()
        self.tabela_empresas.setSortingEnabled(False)
        self.tabela_empresas.setRowCount(len(self.empresas))
        for i, empresa in enumerate(self.empresas):
            self.tabela_empresas.setItem(i, 0, number_item(i + 1))
            self.tabela_empresas.setItem(i, 1, QTableWidgetItem(empresa))
        self.tabela_empresas.setSortingEnabled(sorting_enabled)

    def carregar_tabela_departamentos(self):
        """Carrega a tabela de departamentos do backend"""
        try:
            departamentos = api_client.get_departamentos_completo()
            self.departamentos_detalhados = departamentos or []
            sorting_enabled = self.tabela_departamentos.isSortingEnabled()
            self.tabela_departamentos.setSortingEnabled(False)
            self.tabela_departamentos.setRowCount(len(self.departamentos_detalhados))
            for i, dept in enumerate(self.departamentos_detalhados):
                self.tabela_departamentos.setItem(i, 0, number_item(dept.get("id", "")))
                self.tabela_departamentos.setItem(i, 1, QTableWidgetItem(dept.get("nome", "")))
                self.tabela_departamentos.setItem(i, 2, QTableWidgetItem("Ativo" if dept.get("ativo", True) else "Inativo"))
            self.tabela_departamentos.setSortingEnabled(sorting_enabled)
        except Exception as e:
            print(f"Ã¢ÂÅ’ Erro ao carregar departamentos: {e}")

    def carregar_tabela_categorias(self):
        sorting_enabled = self.tabela_categorias.isSortingEnabled()
        self.tabela_categorias.setSortingEnabled(False)
        self.tabela_categorias.setRowCount(len(self.categorias))
        for i, cat in enumerate(self.categorias):
            self.tabela_categorias.setItem(i, 0, number_item(i + 1))
            self.tabela_categorias.setItem(i, 1, QTableWidgetItem(cat))
        self.tabela_categorias.setSortingEnabled(sorting_enabled)

    def carregar_tabela_cargos(self):
        """Carrega a tabela de cargos do backend"""
        try:
            print("Carregando cargos...")
            cargos = api_client.get_cargos_completo()
            self.cargos_detalhados = cargos or []
            print(f"Cargos recebidos: {len(cargos) if cargos else 0}")

            if not self.cargos_detalhados:
                self.tabela_cargos.setRowCount(0)
                return

            sorting_enabled = self.tabela_cargos.isSortingEnabled()
            self.tabela_cargos.setSortingEnabled(False)
            self.tabela_cargos.setRowCount(len(self.cargos_detalhados))
            for i, cargo in enumerate(self.cargos_detalhados):
                self.tabela_cargos.setItem(i, 0, number_item(cargo.get("id", "")))
                self.tabela_cargos.setItem(i, 1, QTableWidgetItem(cargo.get("nome", "")))
                self.tabela_cargos.setItem(i, 2, QTableWidgetItem("Ativo" if cargo.get("ativo", True) else "Inativo"))
            self.tabela_cargos.setSortingEnabled(sorting_enabled)

            self.tabela_cargos.resizeColumnsToContents()
            print(f"Cargos carregados: {len(cargos)}")
        except Exception as e:
            print(f"Erro ao carregar cargos: {e}")
            import traceback
            traceback.print_exc()

    def _abrir_dialogo_nome(self, titulo, placeholder, valor_inicial=""):
        dialog = QDialog(self)
        dialog.setWindowTitle(titulo)
        dialog.setModal(True)
        dialog.setMinimumWidth(320)

        dialog.setStyleSheet("""
            QDialog {
                background-color: #f5f7fa;
            }
            QDialog QPushButton {
                min-width: 100px;
            }
        """)

        layout = QVBoxLayout(dialog)
        nome_edit = QLineEdit(valor_inicial)
        nome_edit.setPlaceholderText(placeholder)
        nome_edit.setObjectName("configInput")
        layout.addWidget(nome_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec():
            return nome_edit.text().strip()
        return None

    def _abrir_dialogo_parametro_detalhado(
        self,
        titulo,
        placeholder_nome,
        nome_inicial="",
        descricao_inicial="",
        ativo=True,
    ):
        dialog = QDialog(self)
        dialog.setWindowTitle(titulo)
        dialog.setModal(True)
        dialog.setMinimumWidth(420)

        dialog.setStyleSheet("""
            QDialog {
                background-color: #f5f7fa;
            }
            QDialog QPushButton {
                min-width: 100px;
            }
        """)

        layout = QVBoxLayout(dialog)
        form_layout = QFormLayout()

        nome_edit = QLineEdit(nome_inicial)
        nome_edit.setPlaceholderText(placeholder_nome)
        form_layout.addRow("Nome:", nome_edit)

        descricao_edit = QTextEdit()
        descricao_edit.setMaximumHeight(80)
        descricao_edit.setPlaceholderText("Descrição do item (opcional)")
        descricao_edit.setPlainText(descricao_inicial or "")
        form_layout.addRow("Descrição:", descricao_edit)

        ativo_check = QCheckBox("Manter item ativo")
        ativo_check.setChecked(ativo)
        form_layout.addRow("", ativo_check)

        layout.addLayout(form_layout)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec():
            return {
                "nome": nome_edit.text().strip(),
                "descricao": descricao_edit.toPlainText().strip() or None,
                "ativo": ativo_check.isChecked(),
            }
        return None

    def _obter_texto_coluna(self, tabela, coluna, mensagem_vazia):
        row = tabela.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Atenção", mensagem_vazia)
            return None

        item = tabela.item(row, coluna)
        if item is None:
            QMessageBox.warning(self, "Erro", "Não foi possível identificar o item selecionado.")
            return None

        return item.text().strip()

    def _obter_detalhe_por_id(self, detalhes, item_id):
        for detalhe in detalhes:
            try:
                if int(detalhe.get("id", 0)) == int(item_id):
                    return detalhe
            except (TypeError, ValueError):
                continue
        return None

    # =====================================================
    # CRUD EMPRESAS
    # =====================================================

    def adicionar_empresa(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Adicionar Empresa")
        dialog.setModal(True)
        dialog.setMinimumWidth(300)

        dialog.setStyleSheet("""
            QDialog {
                background-color: #f5f7fa;
            }
            QDialog QPushButton {
                min-width: 100px;
            }
        """)

        layout = QVBoxLayout(dialog)
        nome_edit = QLineEdit()
        nome_edit.setPlaceholderText("Nome da empresa")
        nome_edit.setObjectName("configInput")
        layout.addWidget(nome_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec():
            nome = nome_edit.text().strip()
            if not nome:
                QMessageBox.warning(self, "Atenção", "Digite o nome da empresa!")
                return

            if nome in self.empresas:
                QMessageBox.warning(self, "Atenção", f"Empresa '{nome}' já existe!")
                return

            QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
            success = api_client.add_empresa(nome)
            QApplication.restoreOverrideCursor()

            if success:
                notification_manager.success(f"Empresa '{nome}' adicionada com sucesso!", self.window(), 3000)
                self.carregar_listas()
            else:
                QMessageBox.warning(self, "Erro", "Erro ao adicionar empresa")

    def editar_empresa(self):
        empresa_atual = self._obter_texto_coluna(
            self.tabela_empresas,
            1,
            "Selecione uma empresa para editar",
        )
        if not empresa_atual:
            return

        novo_nome = self._abrir_dialogo_nome("Editar Empresa", "Nome da empresa", empresa_atual)
        if novo_nome is None:
            return

        if not novo_nome:
            QMessageBox.warning(self, "Atenção", "Digite o nome da empresa!")
            return

        if novo_nome != empresa_atual and novo_nome in self.empresas:
            QMessageBox.warning(self, "Atenção", f"Empresa '{novo_nome}' já existe!")
            return

        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        success = api_client.update_empresa(empresa_atual, novo_nome)
        QApplication.restoreOverrideCursor()

        if success:
            notification_manager.success(
                f"Empresa '{empresa_atual}' atualizada com sucesso!",
                self.window(),
                3000,
            )
            self.carregar_listas()
        else:
            QMessageBox.warning(self, "Erro", "Erro ao atualizar empresa")

    def remover_empresa(self):
        empresa = self._obter_texto_coluna(
            self.tabela_empresas,
            1,
            "Selecione uma empresa para remover",
        )
        if not empresa:
            return


        confirm = QMessageBox.question(
            self,
            "Confirmar exclusão",
            f"Tem certeza que deseja remover a empresa '{empresa}'?\n\n"
            f"Esta ação não poderá ser desfeita e só será permitida se nenhum material ou máquina estiver usando esta empresa.",
            QMessageBox.Yes | QMessageBox.No
        )

        if confirm == QMessageBox.Yes:
            QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
            success = api_client.delete_empresa(empresa)
            QApplication.restoreOverrideCursor()

            if success:
                notification_manager.success(f"Empresa '{empresa}' removida com sucesso!", self.window(), 3000)
                self.carregar_listas()
            else:
                QMessageBox.warning(self, "Erro", "Erro ao remover empresa. Verifique se não está sendo usada.")

    # =====================================================
    # CRUD DEPARTAMENTOS
    # =====================================================

    def adicionar_departamento(self):
        """Adiciona um novo departamento via backend"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Adicionar Departamento")
        dialog.setModal(True)
        dialog.setMinimumWidth(400)

        dialog.setStyleSheet("""
            QDialog {
                background-color: #f5f7fa;
            }
            QDialog QPushButton {
                min-width: 100px;
            }
        """)

        layout = QVBoxLayout(dialog)

        form_layout = QFormLayout()

        nome_edit = QLineEdit()
        nome_edit.setPlaceholderText("Ex: Departamento de TI")
        form_layout.addRow("Nome:", nome_edit)

        descricao_edit = QTextEdit()
        descricao_edit.setMaximumHeight(80)
        descricao_edit.setPlaceholderText("Descrição do departamento (opcional)")
        form_layout.addRow("Descrição:", descricao_edit)

        layout.addLayout(form_layout)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec():
            nome = nome_edit.text().strip()
            if not nome:
                QMessageBox.warning(self, "Atenção", "Digite o nome do departamento!")
                return

            descricao = descricao_edit.toPlainText().strip() or None

            QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
            success = api_client.criar_departamento(nome, descricao)
            QApplication.restoreOverrideCursor()

            if success:
                notification_manager.success(f"Departamento '{nome}' adicionado com sucesso!", self.window(), 3000)
                self.carregar_tabela_departamentos()
                self.carregar_listas()
            else:
                QMessageBox.warning(self, "Erro", "Erro ao adicionar departamento")

    def editar_departamento(self):
        dept_id = self._obter_texto_coluna(
            self.tabela_departamentos,
            0,
            "Selecione um departamento para editar",
        )
        if not dept_id:
            return

        detalhe = self._obter_detalhe_por_id(self.departamentos_detalhados, dept_id)
        if detalhe is None:
            detalhe = {
                "id": dept_id,
                "nome": self._obter_texto_coluna(self.tabela_departamentos, 1, "Selecione um departamento para editar") or "",
                "descricao": "",
                "ativo": (self._obter_texto_coluna(self.tabela_departamentos, 2, "Selecione um departamento para editar") or "") == "Ativo",
            }

        dados = self._abrir_dialogo_parametro_detalhado(
            "Editar Departamento",
            "Ex: Departamento de TI",
            detalhe.get("nome", ""),
            detalhe.get("descricao") or "",
            detalhe.get("ativo", True),
        )
        if dados is None:
            return

        if not dados["nome"]:
            QMessageBox.warning(self, "Atenção", "Digite o nome do departamento!")
            return

        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        success = api_client.atualizar_departamento(
            int(dept_id),
            dados["nome"],
            dados["descricao"],
            dados["ativo"],
        )
        QApplication.restoreOverrideCursor()

        if success:
            notification_manager.success(
                f"Departamento '{dados['nome']}' atualizado com sucesso!",
                self.window(),
                3000,
            )
            self.carregar_tabela_departamentos()
            self.carregar_listas()
        else:
            QMessageBox.warning(self, "Erro", "Erro ao atualizar departamento")

    def remover_departamento(self):
        """Remove o departamento selecionado via backend"""
        row = self.tabela_departamentos.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Atenção", "Selecione um departamento para remover")
            return

        dept_id = int(self.tabela_departamentos.item(row, 0).text())
        dept_nome = self.tabela_departamentos.item(row, 1).text()

        confirm = QMessageBox.question(
            self,
            "Confirmar exclusão",
            f"Tem certeza que deseja remover o departamento '{dept_nome}'?\n\n"
            f"Esta ação não poderá ser desfeita e só será permitida se nenhuma máquina ou colaborador estiver usando este departamento.",
            QMessageBox.Yes | QMessageBox.No
        )

        if confirm == QMessageBox.Yes:
            QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
            success = api_client.deletar_departamento(dept_id)
            QApplication.restoreOverrideCursor()

            if success:
                notification_manager.success(f"Departamento '{dept_nome}' removido com sucesso!", self.window(), 3000)
                self.carregar_tabela_departamentos()
                self.carregar_listas()
            else:
                QMessageBox.warning(self, "Erro", "Erro ao remover departamento. Verifique se não está sendo usado.")

    # =====================================================
    # CRUD CATEGORIAS
    # =====================================================

    def adicionar_categoria(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Adicionar Categoria")
        dialog.setModal(True)
        dialog.setMinimumWidth(300)

        dialog.setStyleSheet("""
            QDialog {
                background-color: #f5f7fa;
            }
            QDialog QPushButton {
                min-width: 100px;
            }
        """)

        layout = QVBoxLayout(dialog)
        nome_edit = QLineEdit()
        nome_edit.setPlaceholderText("Nome da categoria")
        nome_edit.setObjectName("configInput")
        layout.addWidget(nome_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec():
            nome = nome_edit.text().strip()
            if not nome:
                QMessageBox.warning(self, "Atenção", "Digite o nome da categoria!")
                return

            if nome in self.categorias:
                QMessageBox.warning(self, "Atenção", f"Categoria '{nome}' já existe!")
                return

            QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
            success = api_client.add_categoria(nome)
            QApplication.restoreOverrideCursor()

            if success:
                notification_manager.success(f"Categoria '{nome}' adicionada com sucesso!", self.window(), 3000)
                self.carregar_listas()
            else:
                QMessageBox.warning(self, "Erro", "Erro ao adicionar categoria")

    def editar_categoria(self):
        categoria_atual = self._obter_texto_coluna(
            self.tabela_categorias,
            1,
            "Selecione uma categoria para editar",
        )
        if not categoria_atual:
            return

        novo_nome = self._abrir_dialogo_nome("Editar Categoria", "Nome da categoria", categoria_atual)
        if novo_nome is None:
            return

        if not novo_nome:
            QMessageBox.warning(self, "Atenção", "Digite o nome da categoria!")
            return

        if novo_nome != categoria_atual and novo_nome in self.categorias:
            QMessageBox.warning(self, "Atenção", f"Categoria '{novo_nome}' já existe!")
            return

        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        success = api_client.update_categoria(categoria_atual, novo_nome)
        QApplication.restoreOverrideCursor()

        if success:
            notification_manager.success(
                f"Categoria '{categoria_atual}' atualizada com sucesso!",
                self.window(),
                3000,
            )
            self.carregar_listas()
        else:
            QMessageBox.warning(self, "Erro", "Erro ao atualizar categoria")

    def remover_categoria(self):
        categoria = self._obter_texto_coluna(
            self.tabela_categorias,
            1,
            "Selecione uma categoria para remover",
        )
        if not categoria:
            return


        confirm = QMessageBox.question(
            self,
            "Confirmar exclusão",
            f"Tem certeza que deseja remover a categoria '{categoria}'?\n\n"
            f"Esta ação não poderá ser desfeita e só será permitida se nenhum material estiver usando esta categoria.",
            QMessageBox.Yes | QMessageBox.No
        )

        if confirm == QMessageBox.Yes:
            QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
            success = api_client.delete_categoria(categoria)
            QApplication.restoreOverrideCursor()

            if success:
                notification_manager.success(f"Categoria '{categoria}' removida com sucesso!", self.window(), 3000)
                self.carregar_listas()
            else:
                QMessageBox.warning(self, "Erro", "Erro ao remover categoria. Verifique se não está sendo usada.")

    # =====================================================
    # CRUD CARGOS
    # =====================================================


    def adicionar_cargo(self):
        """Adiciona um novo cargo via backend"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Adicionar Cargo")
        dialog.setModal(True)
        dialog.setMinimumWidth(400)

        dialog.setStyleSheet("""
            QDialog {
                background-color: #f5f7fa;
            }
            QDialog QPushButton {
                min-width: 100px;
            }
        """)

        layout = QVBoxLayout(dialog)

        form_layout = QFormLayout()

        nome_edit = QLineEdit()
        nome_edit.setPlaceholderText("Ex: Analista de Sistemas")
        form_layout.addRow("Nome:", nome_edit)

        descricao_edit = QTextEdit()
        descricao_edit.setMaximumHeight(80)
        descricao_edit.setPlaceholderText("Descrição do cargo (opcional)")
        form_layout.addRow("Descrição:", descricao_edit)

        layout.addLayout(form_layout)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec():
            nome = nome_edit.text().strip()
            if not nome:
                QMessageBox.warning(self, "Atenção", "Digite o nome do cargo!")
                return

            descricao = descricao_edit.toPlainText().strip() or None

            QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
            success = api_client.criar_cargo(nome, descricao)
            QApplication.restoreOverrideCursor()

            if success:
                notification_manager.success(f"Cargo '{nome}' adicionado com sucesso!", self.window(), 3000)
                self.carregar_tabela_cargos()
            else:
                QMessageBox.warning(self, "Erro", "Erro ao adicionar cargo")

    def editar_cargo(self):
        cargo_id = self._obter_texto_coluna(
            self.tabela_cargos,
            0,
            "Selecione um cargo para editar",
        )
        if not cargo_id:
            return

        detalhe = self._obter_detalhe_por_id(self.cargos_detalhados, cargo_id)
        if detalhe is None:
            detalhe = {
                "id": cargo_id,
                "nome": self._obter_texto_coluna(self.tabela_cargos, 1, "Selecione um cargo para editar") or "",
                "descricao": "",
                "ativo": (self._obter_texto_coluna(self.tabela_cargos, 2, "Selecione um cargo para editar") or "") == "Ativo",
            }

        dados = self._abrir_dialogo_parametro_detalhado(
            "Editar Cargo",
            "Ex: Analista de Sistemas",
            detalhe.get("nome", ""),
            detalhe.get("descricao") or "",
            detalhe.get("ativo", True),
        )
        if dados is None:
            return

        if not dados["nome"]:
            QMessageBox.warning(self, "Atenção", "Digite o nome do cargo!")
            return

        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        success = api_client.atualizar_cargo(
            int(cargo_id),
            dados["nome"],
            dados["descricao"],
            dados["ativo"],
        )
        QApplication.restoreOverrideCursor()

        if success:
            notification_manager.success(
                f"Cargo '{dados['nome']}' atualizado com sucesso!",
                self.window(),
                3000,
            )
            self.carregar_tabela_cargos()
        else:
            QMessageBox.warning(self, "Erro", "Erro ao atualizar cargo")

    def remover_cargo(self):
        """Remove o cargo selecionado via backend"""
        row = self.tabela_cargos.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Atenção", "Selecione um cargo para remover")
            return

        cargo_id = int(self.tabela_cargos.item(row, 0).text())
        cargo_nome = self.tabela_cargos.item(row, 1).text()

        confirm = QMessageBox.question(
            self,
            "Confirmar exclusão",
            f"Tem certeza que deseja remover o cargo '{cargo_nome}'?\n\n"
            f"Esta ação não poderá ser desfeita e só será permitida se nenhum colaborador ou usuário estiver usando este cargo.",
            QMessageBox.Yes | QMessageBox.No
        )

        if confirm == QMessageBox.Yes:
            QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
            success = api_client.deletar_cargo(cargo_id)
            QApplication.restoreOverrideCursor()

            if success:
                notification_manager.success(f"Cargo '{cargo_nome}' removido com sucesso!", self.window(), 3000)
                self.carregar_tabela_cargos()
            else:
                QMessageBox.warning(self, "Erro", "Erro ao remover cargo. Verifique se não está sendo usado.")

    # =====================================================
    # MÃƒâ€°TODOS EXISTENTES
    # =====================================================

    def get_ip_local(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"

    def carregar_info_servidor(self):
        health_url = f"{api_client.base_url}/health"

        try:
            response = requests.get(health_url, timeout=5)
            if response.status_code == 200:
                self.status_api.setText("Status da API: Online")
                self.status_api.setStyleSheet("color: #2a9d8f;")
                data = response.json()
                self.api_versao.setText(f"Versão da API: {data.get('status', 'Desconhecido')}")
            else:
                self.status_api.setText("Status da API: Offline")
                self.status_api.setStyleSheet("color: #e76f51;")
                self.api_versao.setText("Versão da API: Não disponível")
        except:
            self.status_api.setText("Status da API: Offline")
            self.status_api.setStyleSheet("color: #e76f51;")
            self.api_versao.setText("Versão da API: Não disponível")

        try:
            response = requests.get(health_url, timeout=5)
            if response.status_code == 200:
                self.status_banco.setText("Banco de Dados: Conectado")
                self.status_banco.setStyleSheet("color: #2a9d8f;")
            else:
                self.status_banco.setText("Banco de Dados: Desconectado")
                self.status_banco.setStyleSheet("color: #e76f51;")
        except:
            self.status_banco.setText("Banco de Dados: Desconectado")
            self.status_banco.setStyleSheet("color: #e76f51;")

    def testar_notificacao(self):
        """Testa a notificação"""
        notification_manager.info(
            "Esta é uma notificação de teste!\n\n"
            "Se você está vendo isso, as notificações estão funcionando.",
            self.window(),
            5000
        )

    def _normalize_text(self, value):
        return unicodedata.normalize("NFKD", str(value or "")).encode("ascii", "ignore").decode("ascii").strip().lower()

    def _set_combo_value(self, combo, value):
        alvo = self._normalize_text(value)
        if not alvo:
            return False

        for index in range(combo.count()):
            if self._normalize_text(combo.itemText(index)) == alvo:
                combo.setCurrentIndex(index)
                return True
        return False

    def _collect_accessibility_config(self):
        return build_accessibility_config(
            self.tema_interface.currentText(),
            self.tamanho_fonte.currentText(),
            self.escala_interface.currentText(),
            self.navegacao_teclado.isChecked(),
        )

    def _refresh_resolution_hint(self):
        if not hasattr(self, "resolucao_detectada_label"):
            return

        context = get_screen_resolution_context(self._collect_accessibility_config())
        width = context["width"]
        height = context["height"]
        dpi = context["dpi"]
        mode = context["scale_mode"]
        applied = context["scale_aplicada"]
        if mode == "Automatica":
            texto = (
                f"Resolução detectada nesta máquina: {width}x{height}. "
                f"Escala automática sugerida e aplicada: {applied}."
            )
        else:
            texto = (
                f"Resolução detectada nesta máquina: {width}x{height}. "
                f"Escala manual selecionada: {mode}."
            )
        self.resolucao_detectada_label.setText(texto)
        self.resolucao_valor.setText(f"{width}x{height}")
        self.escala_aplicada_valor.setText(f"{applied} ({mode})" if mode == "Automatica" else mode)
        self.dpi_valor.setText(str(dpi))

        if applied in {"90%", "100%"}:
            recomendacao = "Layout mais compacto, indicado para telas menores ou com menos altura útil."
        elif applied in {"110%", "125%"}:
            recomendacao = "Equilíbrio entre leitura e densidade de informação para a maioria das máquinas."
        else:
            recomendacao = "Leitura mais confortável, indicada para monitores grandes ou uso mais distante da tela."
        self.recomendacao_tela_valor.setText(recomendacao)

    def previsualizar_acessibilidade(self, *_args):
        if self._loading_configuracoes:
            return
        config = self._collect_accessibility_config()
        self._refresh_resolution_hint()
        apply_accessibility_config(config)

    def carregar_configuracoes(self):
        """Carrega as configuracoes salvas do backend"""
        print("Carregando configuracoes...")
        try:
            self._loading_configuracoes = True
            config = api_client.get_configuracoes()

            if config:
                if "empresa_padrao" in config:
                    self._set_combo_value(self.empresa_padrao, config["empresa_padrao"])

                if "tema" in config:
                    self._set_combo_value(self.tema_interface, config["tema"])

                if "tamanho_fonte" in config:
                    self._set_combo_value(self.tamanho_fonte, config["tamanho_fonte"])

                if "escala_interface" in config:
                    self._set_combo_value(self.escala_interface, config["escala_interface"])

                if "navegacao_teclado" in config:
                    self.navegacao_teclado.setChecked(
                        config["navegacao_teclado"] == True or config["navegacao_teclado"] == "true"
                    )

                if "alerta_estoque" in config:
                    self.alerta_estoque.setValue(int(config["alerta_estoque"]))

                if "alerta_estoque_critico" in config:
                    self.alerta_estoque_critico.setValue(int(config["alerta_estoque_critico"]))

                if "backup_automatico" in config:
                    self.backup_automatico.setChecked(config["backup_automatico"] == True or config["backup_automatico"] == "true")

                if "frequencia_backup" in config:
                    self._set_combo_value(self.frequencia_backup, config["frequencia_backup"])

                if "horario_backup" in config:
                    self.horario_backup.setTime(QTime.fromString(config["horario_backup"], "HH:mm"))

                if "dias_retencao" in config:
                    self.dias_retencao.setValue(int(config["dias_retencao"]))

                if "notif_estoque_baixo" in config:
                    self.notif_estoque_baixo.setChecked(config["notif_estoque_baixo"] == True or config["notif_estoque_baixo"] == "true")

                if "notif_estoque_critico" in config:
                    self.notif_estoque_critico.setChecked(config["notif_estoque_critico"] == True or config["notif_estoque_critico"] == "true")

                if "notif_manutencao" in config:
                    self.notif_manutencao.setChecked(config["notif_manutencao"] == True or config["notif_manutencao"] == "true")

                if "notif_pedidos" in config:
                    self.notif_pedidos.setChecked(config["notif_pedidos"] == True or config["notif_pedidos"] == "true")

                if "notif_demandas" in config:
                    self.notif_demandas.setChecked(config["notif_demandas"] == True or config["notif_demandas"] == "true")

                if "notif_movimentacoes" in config:
                    self.notif_movimentacoes.setChecked(config["notif_movimentacoes"] == True or config["notif_movimentacoes"] == "true")

                if "valor_alto" in config:
                    self.valor_alto.setValue(int(config["valor_alto"]))

                if "verificar_alertas_auto" in config:
                    self.verificar_alertas_auto.setChecked(config["verificar_alertas_auto"] == True or config["verificar_alertas_auto"] == "true")

                if "intervalo_verificacao" in config:
                    self._set_combo_value(self.intervalo_verificacao, config["intervalo_verificacao"])

                if "tempo_notificacao" in config:
                    self._set_combo_value(self.tempo_notificacao, config["tempo_notificacao"])

                if "modo_nao_perturbe" in config:
                    self.modo_nao_perturbe.setChecked(config["modo_nao_perturbe"] == True or config["modo_nao_perturbe"] == "true")

                self._refresh_resolution_hint()
                apply_accessibility_config(config)
                print("Configurações carregadas com sucesso")

        except Exception as e:
            print(f"Erro ao carregar configuracoes: {e}")
        finally:
            self._loading_configuracoes = False

    def salvar_configuracoes(self):
        """Salva as configuracoes no backend"""

        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))

        accessibility_config = self._collect_accessibility_config()
        config = {
            "empresa_padrao": self.empresa_padrao.currentText(),
            "tema": accessibility_config["tema"],
            "tamanho_fonte": accessibility_config["tamanho_fonte"],
            "escala_interface": accessibility_config["escala_interface"],
            "navegacao_teclado": accessibility_config["navegacao_teclado"],
            "alerta_estoque": self.alerta_estoque.value(),
            "alerta_estoque_critico": self.alerta_estoque_critico.value(),
            "backup_automatico": self.backup_automatico.isChecked(),
            "frequencia_backup": self.frequencia_backup.currentText(),
            "horario_backup": self.horario_backup.time().toString("HH:mm"),
            "dias_retencao": self.dias_retencao.value(),
            "notif_estoque_baixo": self.notif_estoque_baixo.isChecked(),
            "notif_estoque_critico": self.notif_estoque_critico.isChecked(),
            "notif_manutencao": self.notif_manutencao.isChecked(),
            "notif_pedidos": self.notif_pedidos.isChecked(),
            "notif_demandas": self.notif_demandas.isChecked(),
            "notif_movimentacoes": self.notif_movimentacoes.isChecked(),
            "valor_alto": self.valor_alto.value(),
            "verificar_alertas_auto": self.verificar_alertas_auto.isChecked(),
            "intervalo_verificacao": self.intervalo_verificacao.currentText(),
            "tempo_notificacao": self.tempo_notificacao.currentText(),
            "modo_nao_perturbe": self.modo_nao_perturbe.isChecked()
        }

        try:
            success = api_client.salvar_configuracoes(config)

            QApplication.restoreOverrideCursor()

            if success:
                apply_accessibility_config(accessibility_config)
                save_local_accessibility_config(accessibility_config)
                notification_manager.success("Configurações salvas com sucesso!", self.window(), 3000)
                api_client.reconfigurar_backup()
                from core.notification_manager import notification_manager as core_notification_manager
                core_notification_manager.carregar_configuracoes()
            else:
                notification_manager.error("Erro ao salvar configuracoes", self.window(), 3000)
        except Exception as e:
            QApplication.restoreOverrideCursor()
            notification_manager.error(f"Erro ao salvar: {e}", self.window(), 3000)

    def cancelar(self):
        self.carregar_configuracoes()
        notification_manager.info("Alteracoes canceladas.", self.window(), 2000)

    def carregar_dados(self):
        self.carregar_configuracoes()
        self.carregar_info_servidor()
