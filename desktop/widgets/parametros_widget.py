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
from widgets.toast_notification import notification_manager
from widgets.table_utils import configure_data_table, number_item
import socket
import requests
from datetime import datetime
import os
import sys
import subprocess


class ParametrosWidget(QWidget):
    def __init__(self):
        super().__init__()
        # Inicializar listas vazias (serÃƒÂ£o carregadas do backend)
        self.empresas = []
        self.departamentos = []
        self.categorias = []
        self._loaded = False  # Ã¢Å“â€¦ Flag para carregamento sob demanda
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

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(24, 24, 24, 24)

        # TÃƒÂ­tulo
        titulo = QLabel("Ã¢Å¡â„¢Ã¯Â¸Â ParÃƒÂ¢metros do Sistema")
        titulo.setProperty("class", "page-title")
        layout.addWidget(titulo)

        # Tabs
        tabs = QTabWidget()
        tabs.setObjectName("paramTabs")

        # Abas
        tab_geral = self.create_tab_geral()
        tabs.addTab(tab_geral, "Ã¢Å¡â„¢Ã¯Â¸Â ConfiguraÃƒÂ§ÃƒÂµes Gerais")

        tab_notificacoes = self.create_tab_notificacoes()
        tabs.addTab(tab_notificacoes, "Ã°Å¸â€â€ NotificaÃƒÂ§ÃƒÂµes")

        tab_empresas = self.create_tab_empresas()
        tabs.addTab(tab_empresas, "Ã°Å¸ÂÂ¢ Empresas")

        tab_departamentos = self.create_tab_departamentos()
        tabs.addTab(tab_departamentos, "Ã°Å¸â€œÂ Departamentos")

        tab_categorias = self.create_tab_categorias()
        tabs.addTab(tab_categorias, "Ã°Å¸â€œâ€š Categorias")

        tab_cargos = self.create_tab_cargos()
        tabs.addTab(tab_cargos, 'Ã°Å¸â€œâ€¹ Cargos')

        tab_backup = self.create_tab_backup()
        tabs.addTab(tab_backup, 'Ã°Å¸â€™Â¾ Backup')

        tab_servidor = self.create_tab_servidor()
        tabs.addTab(tab_servidor, "Ã°Å¸â€“Â¥Ã¯Â¸Â Servidor")

        layout.addWidget(tabs)

        # BotÃƒÂµes
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.btn_salvar = QPushButton("Ã°Å¸â€™Â¾ Salvar ConfiguraÃƒÂ§ÃƒÂµes")
        self.btn_salvar.setObjectName("btnPrimary")
        self.btn_salvar.clicked.connect(self.salvar_configuracoes)
        btn_layout.addWidget(self.btn_salvar)

        self.btn_cancelar = QPushButton("Ã¢ÂÅ’ Cancelar")
        self.btn_cancelar.setObjectName("btnSecondary")
        self.btn_cancelar.clicked.connect(self.cancelar)
        btn_layout.addWidget(self.btn_cancelar)

        layout.addLayout(btn_layout)

    def create_tab_geral(self):
        """Aba de ConfiguraÃƒÂ§ÃƒÂµes Gerais"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(20)

        # Grupo: ConfiguraÃƒÂ§ÃƒÂµes do Sistema
        grupo_sistema = QGroupBox("ConfiguraÃƒÂ§ÃƒÂµes do Sistema")
        grupo_sistema.setObjectName("configGroup")
        form_sistema = QFormLayout(grupo_sistema)
        form_sistema.setContentsMargins(20, 20, 20, 20)

        self.nome_sistema = QLineEdit("Project Parallel")
        self.nome_sistema.setReadOnly(True)
        self.nome_sistema.setObjectName("configInputOnly")
        form_sistema.addRow("Ã°Å¸â€œÅ’ Nome do Sistema:", self.nome_sistema)

        self.empresa_padrao = QComboBox()
        self.empresa_padrao.setObjectName("configCombo")
        form_sistema.addRow("Ã°Å¸ÂÂ¢ Empresa PadrÃƒÂ£o:", self.empresa_padrao)

        layout.addWidget(grupo_sistema)

        # Grupo: ConfiguraÃƒÂ§ÃƒÂµes de Estoque
        grupo_estoque = QGroupBox("ConfiguraÃƒÂ§ÃƒÂµes de Estoque")
        grupo_estoque.setObjectName("configGroup")
        form_estoque = QFormLayout(grupo_estoque)
        form_estoque.setContentsMargins(20, 20, 20, 20)

        self.alerta_estoque = QSpinBox()
        self.alerta_estoque.setObjectName("configSpin")
        self.alerta_estoque.setRange(0, 100)
        self.alerta_estoque.setValue(5)
        self.alerta_estoque.setSuffix(" unidades")
        form_estoque.addRow("Ã¢Å¡Â Ã¯Â¸Â Alerta de Estoque Baixo:", self.alerta_estoque)

        self.alerta_estoque_critico = QSpinBox()
        self.alerta_estoque_critico.setObjectName("configSpin")
        self.alerta_estoque_critico.setRange(0, 100)
        self.alerta_estoque_critico.setValue(2)
        self.alerta_estoque_critico.setSuffix(" unidades")
        form_estoque.addRow("Ã°Å¸â€Â´ Alerta de Estoque CrÃƒÂ­tico:", self.alerta_estoque_critico)

        layout.addWidget(grupo_estoque)

        # Grupo: ConfiguraÃƒÂ§ÃƒÂµes de Backup
        grupo_backup = QGroupBox("ConfiguraÃƒÂ§ÃƒÂµes de Backup")
        grupo_backup.setObjectName("configGroup")
        form_backup = QFormLayout(grupo_backup)
        form_backup.setContentsMargins(20, 20, 20, 20)

        self.backup_automatico = QCheckBox("Realizar backup automÃƒÂ¡tico")
        self.backup_automatico.setObjectName("configCheckbox")
        self.backup_automatico.setChecked(True)
        form_backup.addRow("", self.backup_automatico)

        self.frequencia_backup = QComboBox()
        self.frequencia_backup.setObjectName("configCombo")
        self.frequencia_backup.addItems(["DiÃƒÂ¡rio", "Semanal", "Mensal"])
        form_backup.addRow("Ã°Å¸â€œâ€¦ FrequÃƒÂªncia:", self.frequencia_backup)

        self.horario_backup = QTimeEdit()
        self.horario_backup.setTime(QTime(2, 0))
        form_backup.addRow("Ã¢ÂÂ° HorÃƒÂ¡rio:", self.horario_backup)

        self.dias_retencao = QSpinBox()
        self.dias_retencao.setRange(7, 365)
        self.dias_retencao.setValue(30)
        self.dias_retencao.setSuffix(" dias")
        form_backup.addRow("Ã°Å¸â€œÂ Reter backups por:", self.dias_retencao)

        layout.addWidget(grupo_backup)

        layout.addStretch()
        return widget

    def create_tab_backup(self):
        """Aba de gerenciamento de backup"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)

        # SeÃƒÂ§ÃƒÂ£o: Backup Manual
        grupo_manual = QGroupBox("Backup Manual")
        grupo_manual.setObjectName("configGroup")
        manual_layout = QVBoxLayout(grupo_manual)
        manual_layout.setContentsMargins(20, 20, 20, 20)

        btn_executar_backup = QPushButton("Ã°Å¸â€â€ž Executar Backup Agora")
        btn_executar_backup.setObjectName("btnPrimary")
        btn_executar_backup.setMinimumHeight(40)
        btn_executar_backup.clicked.connect(self.executar_backup_manual)
        manual_layout.addWidget(btn_executar_backup)

        lbl_info = QLabel("Ã¢Å¡Â Ã¯Â¸Â O backup serÃƒÂ¡ salvo na pasta 'backups' do servidor e compactado em formato .gz")
        lbl_info.setStyleSheet("color: #64748b; font-size: 11px; margin-top: 10px;")
        manual_layout.addWidget(lbl_info)

        layout.addWidget(grupo_manual)

        # SeÃƒÂ§ÃƒÂ£o: Lista de Backups
        grupo_lista = QGroupBox("Backups DisponÃƒÂ­veis")
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

        # BotÃƒÂµes de aÃƒÂ§ÃƒÂ£o
        btn_layout = QHBoxLayout()

        btn_atualizar_lista = QPushButton("Ã°Å¸â€â€ž Atualizar Lista")
        btn_atualizar_lista.clicked.connect(self.carregar_lista_backups)
        btn_layout.addWidget(btn_atualizar_lista)

        btn_restaurar = QPushButton("Ã°Å¸â€œÂ¥ Restaurar Backup")
        btn_restaurar.setObjectName("btnWarning")
        btn_restaurar.clicked.connect(self.restaurar_backup_selecionado)
        btn_layout.addWidget(btn_restaurar)

        btn_layout.addStretch()
        lista_layout.addLayout(btn_layout)

        layout.addWidget(grupo_lista)

        # Ã¢Å¡Â Ã¯Â¸Â NÃƒÆ’O carregar lista de backups aqui - serÃƒÂ¡ feito no on_show()

        return widget

    def executar_backup_manual(self):
        """Executa backup manual"""
        try:
            QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
            success, result = api_client.executar_backup()
            QApplication.restoreOverrideCursor()

            if success:
                notification_manager.success(f"Ã¢Å“â€¦ Backup realizado com sucesso!\nArquivo: {result.get('arquivo', 'desconhecido')}", self.window(), 5000)
                self.carregar_lista_backups()
            else:
                notification_manager.error("Ã¢ÂÅ’ Erro ao realizar backup", self.window(), 4000)

        except Exception as e:
            QApplication.restoreOverrideCursor()
            notification_manager.error(f"Erro: {e}", self.window(), 4000)

    def carregar_lista_backups(self):
        """Carrega a lista de backups disponÃƒÂ­veis"""
        try:
            backups = api_client.listar_backups()
            self.tabela_backups.setRowCount(len(backups))

            for row, backup in enumerate(backups):
                self.tabela_backups.setItem(row, 0, QTableWidgetItem(backup.get("nome", "-")))
                self.tabela_backups.setItem(row, 1, QTableWidgetItem(backup.get("data", "-")))
                self.tabela_backups.setItem(row, 2, QTableWidgetItem(f"{backup.get('tamanho_mb', 0)} MB"))

            self.tabela_backups.resizeColumnsToContents()

        except Exception as e:
            print(f"Ã¢ÂÅ’ Erro ao carregar lista de backups: {e}")

    def restaurar_backup_selecionado(self):
        """Restaura o backup selecionado"""
        current_row = self.tabela_backups.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Atencao", "Selecione um backup para restaurar")
            return

        backup_nome = self.tabela_backups.item(current_row, 0).text()
        backup_data = self.tabela_backups.item(current_row, 1).text()

        confirm = QMessageBox.question(
            self,
            "Confirmar restauraÃƒÂ§ÃƒÂ£o",
            f"Tem certeza que deseja restaurar o backup '{backup_nome}'?\n\n"
            f"Ã°Å¸â€œâ€¦ Data: {backup_data}\n\n"
            f"Ã¢Å¡Â Ã¯Â¸Â ATENÃƒâ€¡ÃƒÆ’O: Esta aÃƒÂ§ÃƒÂ£o irÃƒÂ¡ SUBSTITUIR todos os dados atuais pelos dados do backup.\n"
            f"Ã¢Å¡Â Ã¯Â¸Â Esta aÃƒÂ§ÃƒÂ£o nÃƒÂ£o pode ser desfeita!",
            QMessageBox.Yes | QMessageBox.No
        )

        if confirm == QMessageBox.Yes:
            try:
                QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
                success, result = api_client.restaurar_backup(backup_nome)
                QApplication.restoreOverrideCursor()

                if success:
                    notification_manager.success("Ã¢Å“â€¦ Backup restaurado com sucesso! O sistema serÃƒÂ¡ reiniciado.", self.window(), 5000)
                    QTimer.singleShot(2000, self.reiniciar_aplicacao)
                else:
                    notification_manager.error(f"Ã¢ÂÅ’ Erro ao restaurar backup: {result.get('detail', 'Erro desconhecido') if result else 'Erro'}", self.window(), 5000)
            except Exception as e:
                QApplication.restoreOverrideCursor()
                notification_manager.error(f"Erro: {e}", self.window(), 4000)

    def reiniciar_aplicacao(self):
        """Reinicia a aplicaÃƒÂ§ÃƒÂ£o apÃƒÂ³s restauraÃƒÂ§ÃƒÂ£o"""
        QMessageBox.information(self, "Reiniciando", "O sistema serÃƒÂ¡ reiniciado para aplicar as alteraÃƒÂ§ÃƒÂµes.")
        if getattr(sys, "frozen", False):
            subprocess.Popen([sys.executable])
        else:
            python = sys.executable
            script = os.path.abspath(sys.argv[0])
            subprocess.Popen([python, script])
        sys.exit(0)

    def create_tab_notificacoes(self):
        """Aba de configuraÃƒÂ§ÃƒÂµes de notificaÃƒÂ§ÃƒÂµes"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(20)

        # Grupo: NotificaÃƒÂ§ÃƒÂµes do Sistema
        grupo_notificacoes = QGroupBox("ConfiguraÃƒÂ§ÃƒÂµes de NotificaÃƒÂ§ÃƒÂµes")
        grupo_notificacoes.setObjectName("configGroup")
        form_notificacoes = QFormLayout(grupo_notificacoes)
        form_notificacoes.setContentsMargins(20, 20, 20, 20)

        self.notif_estoque_baixo = QCheckBox("Notificar quando estoque estiver baixo")
        self.notif_estoque_baixo.setObjectName("configCheckbox")
        self.notif_estoque_baixo.setChecked(True)
        form_notificacoes.addRow("Ã°Å¸â€œÂ¦", self.notif_estoque_baixo)

        self.notif_estoque_critico = QCheckBox("Notificar quando estoque estiver crÃƒÂ­tico")
        self.notif_estoque_critico.setObjectName("configCheckbox")
        self.notif_estoque_critico.setChecked(True)
        form_notificacoes.addRow("Ã°Å¸â€Â´", self.notif_estoque_critico)

        self.notif_manutencao = QCheckBox("Notificar sobre manutenÃƒÂ§ÃƒÂµes pendentes")
        self.notif_manutencao.setObjectName("configCheckbox")
        self.notif_manutencao.setChecked(True)
        form_notificacoes.addRow("Ã°Å¸â€Â§", self.notif_manutencao)

        self.notif_pedidos = QCheckBox("Notificar sobre pedidos pendentes de aprovaÃƒÂ§ÃƒÂ£o")
        self.notif_pedidos.setObjectName("configCheckbox")
        self.notif_pedidos.setChecked(True)
        form_notificacoes.addRow("Ã°Å¸â€œâ€¹", self.notif_pedidos)

        self.notif_demandas = QCheckBox("Notificar sobre novas demandas de TI")
        self.notif_demandas.setObjectName("configCheckbox")
        self.notif_demandas.setChecked(True)
        form_notificacoes.addRow("Ã°Å¸Å½Â«", self.notif_demandas)

        self.notif_movimentacoes = QCheckBox("Notificar sobre movimentaÃƒÂ§ÃƒÂµes de alto valor")
        self.notif_movimentacoes.setObjectName("configCheckbox")
        self.notif_movimentacoes.setChecked(False)
        form_notificacoes.addRow("Ã°Å¸â€™Â°", self.notif_movimentacoes)

        self.valor_alto = QSpinBox()
        self.valor_alto.setRange(0, 100000)
        self.valor_alto.setValue(5000)
        self.valor_alto.setSuffix(" R$")
        form_notificacoes.addRow("Valor mÃƒÂ­nimo para notificaÃƒÂ§ÃƒÂ£o:", self.valor_alto)

        layout.addWidget(grupo_notificacoes)

        # Grupo: ConfiguraÃƒÂ§ÃƒÂµes de Alerta
        grupo_alertas = QGroupBox("ConfiguraÃƒÂ§ÃƒÂµes de Alerta")
        grupo_alertas.setObjectName("configGroup")
        form_alertas = QFormLayout(grupo_alertas)
        form_alertas.setContentsMargins(20, 20, 20, 20)

        self.verificar_alertas_auto = QCheckBox("Verificar alertas automaticamente")
        self.verificar_alertas_auto.setObjectName("configCheckbox")
        self.verificar_alertas_auto.setChecked(True)
        form_alertas.addRow("", self.verificar_alertas_auto)

        self.intervalo_verificacao = QComboBox()
        self.intervalo_verificacao.addItems(["1 minuto", "5 minutos", "15 minutos", "30 minutos", "1 hora"])
        form_alertas.addRow("Ã¢ÂÂ±Ã¯Â¸Â Intervalo de verificaÃƒÂ§ÃƒÂ£o:", self.intervalo_verificacao)

        self.tempo_notificacao = QComboBox()
        self.tempo_notificacao.addItems(["3 segundos", "5 segundos", "10 segundos", "30 segundos"])
        form_alertas.addRow("Ã¢ÂÂ²Ã¯Â¸Â DuraÃƒÂ§ÃƒÂ£o da notificaÃƒÂ§ÃƒÂ£o:", self.tempo_notificacao)

        layout.addWidget(grupo_alertas)

        grupo_silencio = QGroupBox("Modo Nao Perturbe")
        grupo_silencio.setObjectName("configGroup")
        form_silencio = QFormLayout(grupo_silencio)
        form_silencio.setContentsMargins(20, 20, 20, 20)

        self.modo_nao_perturbe = QCheckBox("Silenciar notificacoes visuais e sonoras nao criticas")
        self.modo_nao_perturbe.setObjectName("configCheckbox")
        self.modo_nao_perturbe.setChecked(False)
        form_silencio.addRow("Ã°Å¸Å’â„¢", self.modo_nao_perturbe)

        layout.addWidget(grupo_silencio)

        # BotÃƒÂ£o para testar notificaÃƒÂ§ÃƒÂ£o
        btn_testar = QPushButton("Ã°Å¸â€â€ Testar NotificaÃƒÂ§ÃƒÂ£o")
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

        btn_refresh = QPushButton('Ã°Å¸â€â€ž Atualizar')
        btn_refresh.clicked.connect(self.carregar_tabela_cargos)
        btn_layout.addWidget(btn_refresh)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # Ã¢Å¡Â Ã¯Â¸Â NÃƒÆ’O carregar dados aqui - serÃƒÂ¡ feito no carregar_listas()

        return widget

    def create_tab_servidor(self):
        """Aba de informaÃƒÂ§ÃƒÂµes do servidor"""
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

        titulo_servidor = QLabel("Ã°Å¸â€œÂ¡ InformaÃƒÂ§ÃƒÂµes do Servidor")
        titulo_servidor.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        info_layout.addWidget(titulo_servidor)

        info_layout.addSpacing(10)

        self.status_api = QLabel("Status da API: Verificando...")
        info_layout.addWidget(self.status_api)

        self.endereco_server = QLabel(f"EndereÃƒÂ§o Local: {self.get_ip_local()}")
        info_layout.addWidget(self.endereco_server)

        self.porta_server = QLabel("Porta: 8000")
        info_layout.addWidget(self.porta_server)

        self.status_banco = QLabel("Banco de Dados: Verificando...")
        info_layout.addWidget(self.status_banco)

        self.api_versao = QLabel("VersÃƒÂ£o da API: Verificando...")
        info_layout.addWidget(self.api_versao)

        layout.addWidget(info_frame)

        btn_testar = QPushButton("Ã°Å¸â€â€ž Testar ConexÃƒÂ£o")
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
                self.departamentos = ["TI", "Administrativo", "Financeiro", "RH", "Comercial", "Marketing", "LogÃƒÂ­stica"]
            if not self.categorias:
                self.categorias = ["PerifÃƒÂ©ricos", "Hardware", "Armazenamento", "Monitores", "Cabos", "Redes", "ConsumÃƒÂ­veis", "Softwares"]

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
            print("Ã°Å¸â€Â Carregando cargos...")
            cargos = api_client.get_cargos_completo()
            self.cargos_detalhados = cargos or []
            print(f"Ã°Å¸â€Â Cargos recebidos: {len(cargos) if cargos else 0}")

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
            print(f"Ã¢Å“â€¦ Cargos carregados: {len(cargos)}")
        except Exception as e:
            print(f"Ã¢ÂÅ’ Erro ao carregar cargos: {e}")
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
        descricao_edit.setPlaceholderText("Descricao do item (opcional)")
        descricao_edit.setPlainText(descricao_inicial or "")
        form_layout.addRow("Descricao:", descricao_edit)

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
            QMessageBox.warning(self, "Atencao", mensagem_vazia)
            return None

        item = tabela.item(row, coluna)
        if item is None:
            QMessageBox.warning(self, "Erro", "Nao foi possivel identificar o item selecionado.")
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
                QMessageBox.warning(self, "Atencao", "Digite o nome da empresa!")
                return

            if nome in self.empresas:
                QMessageBox.warning(self, "Atencao", f"Empresa '{nome}' ja existe!")
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
            QMessageBox.warning(self, "Atencao", "Digite o nome da empresa!")
            return

        if novo_nome != empresa_atual and novo_nome in self.empresas:
            QMessageBox.warning(self, "Atencao", f"Empresa '{novo_nome}' ja existe!")
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
            "Confirmar exclusÃƒÂ£o",
            f"Tem certeza que deseja remover a empresa '{empresa}'?\n\n"
            f"Esta aÃƒÂ§ÃƒÂ£o nÃƒÂ£o poderÃƒÂ¡ ser desfeita e sÃƒÂ³ serÃƒÂ¡ permitida se nenhum material ou mÃƒÂ¡quina estiver usando esta empresa.",
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
                QMessageBox.warning(self, "Erro", "Erro ao remover empresa. Verifique se nÃƒÂ£o estÃƒÂ¡ sendo usada.")

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
        descricao_edit.setPlaceholderText("DescriÃƒÂ§ÃƒÂ£o do departamento (opcional)")
        form_layout.addRow("DescriÃƒÂ§ÃƒÂ£o:", descricao_edit)

        layout.addLayout(form_layout)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec():
            nome = nome_edit.text().strip()
            if not nome:
                QMessageBox.warning(self, "Atencao", "Digite o nome do departamento!")
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
            QMessageBox.warning(self, "Atencao", "Digite o nome do departamento!")
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
            QMessageBox.warning(self, "Atencao", "Selecione um departamento para remover")
            return

        dept_id = int(self.tabela_departamentos.item(row, 0).text())
        dept_nome = self.tabela_departamentos.item(row, 1).text()

        confirm = QMessageBox.question(
            self,
            "Confirmar exclusÃƒÂ£o",
            f"Tem certeza que deseja remover o departamento '{dept_nome}'?\n\n"
            f"Ã¢Å¡Â Ã¯Â¸Â Esta aÃƒÂ§ÃƒÂ£o nÃƒÂ£o poderÃƒÂ¡ ser desfeita e sÃƒÂ³ serÃƒÂ¡ permitida se nenhuma mÃƒÂ¡quina ou colaborador estiver usando este departamento.",
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
                QMessageBox.warning(self, "Erro", "Erro ao remover departamento. Verifique se nÃƒÂ£o estÃƒÂ¡ sendo usado.")

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
                QMessageBox.warning(self, "Atencao", "Digite o nome da categoria!")
                return

            if nome in self.categorias:
                QMessageBox.warning(self, "Atencao", f"Categoria '{nome}' ja existe!")
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
            QMessageBox.warning(self, "Atencao", "Digite o nome da categoria!")
            return

        if novo_nome != categoria_atual and novo_nome in self.categorias:
            QMessageBox.warning(self, "Atencao", f"Categoria '{novo_nome}' ja existe!")
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
            "Confirmar exclusÃƒÂ£o",
            f"Tem certeza que deseja remover a categoria '{categoria}'?\n\n"
            f"Esta aÃƒÂ§ÃƒÂ£o nÃƒÂ£o poderÃƒÂ¡ ser desfeita e sÃƒÂ³ serÃƒÂ¡ permitida se nenhum material estiver usando esta categoria.",
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
                QMessageBox.warning(self, "Erro", "Erro ao remover categoria. Verifique se nÃƒÂ£o estÃƒÂ¡ sendo usada.")

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
        descricao_edit.setPlaceholderText("DescriÃƒÂ§ÃƒÂ£o do cargo (opcional)")
        form_layout.addRow("DescriÃƒÂ§ÃƒÂ£o:", descricao_edit)

        layout.addLayout(form_layout)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec():
            nome = nome_edit.text().strip()
            if not nome:
                QMessageBox.warning(self, "Atencao", "Digite o nome do cargo!")
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
            QMessageBox.warning(self, "Atencao", "Digite o nome do cargo!")
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
            QMessageBox.warning(self, "Atencao", "Selecione um cargo para remover")
            return

        cargo_id = int(self.tabela_cargos.item(row, 0).text())
        cargo_nome = self.tabela_cargos.item(row, 1).text()

        confirm = QMessageBox.question(
            self,
            "Confirmar exclusÃƒÂ£o",
            f"Tem certeza que deseja remover o cargo '{cargo_nome}'?\n\n"
            f"Ã¢Å¡Â Ã¯Â¸Â Esta aÃƒÂ§ÃƒÂ£o nÃƒÂ£o poderÃƒÂ¡ ser desfeita e sÃƒÂ³ serÃƒÂ¡ permitida se nenhum colaborador ou usuÃƒÂ¡rio estiver usando este cargo.",
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
                QMessageBox.warning(self, "Erro", "Erro ao remover cargo. Verifique se nÃƒÂ£o estÃƒÂ¡ sendo usado.")

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
                self.status_api.setText("Ã¢Å“â€¦ Status da API: Online")
                self.status_api.setStyleSheet("color: #2a9d8f;")
                data = response.json()
                self.api_versao.setText(f"Ã°Å¸â€œÂ¦ VersÃƒÂ£o da API: {data.get('status', 'Desconhecido')}")
            else:
                self.status_api.setText("Ã¢ÂÅ’ Status da API: Offline")
                self.status_api.setStyleSheet("color: #e76f51;")
                self.api_versao.setText("Ã°Å¸â€œÂ¦ VersÃƒÂ£o da API: NÃƒÂ£o disponÃƒÂ­vel")
        except:
            self.status_api.setText("Ã¢ÂÅ’ Status da API: Offline")
            self.status_api.setStyleSheet("color: #e76f51;")
            self.api_versao.setText("Ã°Å¸â€œÂ¦ VersÃƒÂ£o da API: NÃƒÂ£o disponÃƒÂ­vel")

        try:
            response = requests.get(health_url, timeout=5)
            if response.status_code == 200:
                self.status_banco.setText("Ã¢Å“â€¦ Banco de Dados: Conectado")
                self.status_banco.setStyleSheet("color: #2a9d8f;")
            else:
                self.status_banco.setText("Ã¢ÂÅ’ Banco de Dados: Desconectado")
                self.status_banco.setStyleSheet("color: #e76f51;")
        except:
            self.status_banco.setText("Ã¢ÂÅ’ Banco de Dados: Desconectado")
            self.status_banco.setStyleSheet("color: #e76f51;")

    def testar_notificacao(self):
        """Testa a notificaÃƒÂ§ÃƒÂ£o"""
        notification_manager.info(
            "Esta ÃƒÂ© uma notificaÃƒÂ§ÃƒÂ£o de teste!\n\nSe vocÃƒÂª estÃƒÂ¡ vendo isso, as notificaÃƒÂ§ÃƒÂµes estÃƒÂ£o funcionando.",
            self.window(),
            5000
        )

    def carregar_configuracoes(self):
        """Carrega as configuraÃƒÂ§ÃƒÂµes salvas do backend"""
        print("Carregando configuraÃƒÂ§ÃƒÂµes...")
        try:
            config = api_client.get_configuracoes()

            if config:
                if "empresa_padrao" in config:
                    idx = self.empresa_padrao.findText(config["empresa_padrao"])
                    if idx >= 0:
                        self.empresa_padrao.setCurrentIndex(idx)

                if "alerta_estoque" in config:
                    self.alerta_estoque.setValue(int(config["alerta_estoque"]))

                if "alerta_estoque_critico" in config:
                    self.alerta_estoque_critico.setValue(int(config["alerta_estoque_critico"]))

                if "backup_automatico" in config:
                    self.backup_automatico.setChecked(config["backup_automatico"] == True or config["backup_automatico"] == "true")

                if "frequencia_backup" in config:
                    idx = self.frequencia_backup.findText(config["frequencia_backup"])
                    if idx >= 0:
                        self.frequencia_backup.setCurrentIndex(idx)

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
                    idx = self.intervalo_verificacao.findText(config["intervalo_verificacao"])
                    if idx >= 0:
                        self.intervalo_verificacao.setCurrentIndex(idx)

                if "tempo_notificacao" in config:
                    idx = self.tempo_notificacao.findText(config["tempo_notificacao"])
                    if idx >= 0:
                        self.tempo_notificacao.setCurrentIndex(idx)

                if "modo_nao_perturbe" in config:
                    self.modo_nao_perturbe.setChecked(config["modo_nao_perturbe"] == True or config["modo_nao_perturbe"] == "true")

                print("Ã¢Å“â€¦ ConfiguraÃƒÂ§ÃƒÂµes carregadas com sucesso")

        except Exception as e:
            print(f"Ã¢ÂÅ’ Erro ao carregar configuraÃƒÂ§ÃƒÂµes: {e}")

    def salvar_configuracoes(self):
        """Salva as configuraÃƒÂ§ÃƒÂµes no backend"""

        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))

        config = {
            "empresa_padrao": self.empresa_padrao.currentText(),
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
                notification_manager.success("ConfiguraÃƒÂ§ÃƒÂµes salvas com sucesso!", self.window(), 3000)
                # Reconfigurar scheduler de backup apÃƒÂ³s salvar
                api_client.reconfigurar_backup()
                from core.notification_manager import notification_manager as core_notification_manager
                core_notification_manager.carregar_configuracoes()
            else:
                notification_manager.error("Erro ao salvar configuraÃƒÂ§ÃƒÂµes", self.window(), 3000)
        except Exception as e:
            QApplication.restoreOverrideCursor()
            notification_manager.error(f"Erro ao salvar: {e}", self.window(), 3000)

    def cancelar(self):
        notification_manager.info("AlteraÃƒÂ§ÃƒÂµes canceladas.", self.window(), 2000)

    def carregar_dados(self):
        self.carregar_configuracoes()
        self.carregar_info_servidor()
