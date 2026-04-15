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
import socket
import requests
from datetime import datetime
import os
import sys
import subprocess


class ParametrosWidget(QWidget):
    def __init__(self):
        super().__init__()
        # Inicializar listas vazias (serão carregadas do backend)
        self.empresas = []
        self.departamentos = []
        self.categorias = []
        self.timer_alertas = None
        self.init_ui()
        self.carregar_listas()
        self.carregar_configuracoes()
        self.carregar_info_servidor()
        self.carregar_alertas()
        self.configurar_timer_alertas()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(24, 24, 24, 24)
        
        # Título
        titulo = QLabel("⚙️ Parâmetros do Sistema")
        titulo.setProperty("class", "page-title")
        layout.addWidget(titulo)
        
        # Tabs
        tabs = QTabWidget()
        tabs.setObjectName("paramTabs")
        
        # Abas
        tab_geral = self.create_tab_geral()
        tabs.addTab(tab_geral, "⚙️ Configurações Gerais")
        
        tab_notificacoes = self.create_tab_notificacoes()
        tabs.addTab(tab_notificacoes, "🔔 Notificações")
        
        tab_alertas = self.create_tab_alertas()
        tabs.addTab(tab_alertas, "⚠️ Alertas")
        
        tab_empresas = self.create_tab_empresas()
        tabs.addTab(tab_empresas, "🏢 Empresas")
        
        tab_departamentos = self.create_tab_departamentos()
        tabs.addTab(tab_departamentos, "📁 Departamentos")
        
        tab_categorias = self.create_tab_categorias()
        tabs.addTab(tab_categorias, "📂 Categorias")

        tab_cargos = self.create_tab_cargos()
        tabs.addTab(tab_cargos, '📋 Cargos')
        
        tab_backup = self.create_tab_backup()
        tabs.addTab(tab_backup, '💾 Backup')
        
        tab_servidor = self.create_tab_servidor()
        tabs.addTab(tab_servidor, "🖥️ Servidor")
        
        layout.addWidget(tabs)
        
        # Botões
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.btn_salvar = QPushButton("💾 Salvar Configurações")
        self.btn_salvar.setObjectName("btnPrimary")
        self.btn_salvar.clicked.connect(self.salvar_configuracoes)
        btn_layout.addWidget(self.btn_salvar)
        
        self.btn_cancelar = QPushButton("❌ Cancelar")
        self.btn_cancelar.setObjectName("btnSecondary")
        self.btn_cancelar.clicked.connect(self.cancelar)
        btn_layout.addWidget(self.btn_cancelar)
        
        layout.addLayout(btn_layout)
    
    def create_tab_geral(self):
        """Aba de Configurações Gerais"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(20)
        
        # Grupo: Configurações do Sistema
        grupo_sistema = QGroupBox("Configurações do Sistema")
        grupo_sistema.setObjectName("configGroup")
        form_sistema = QFormLayout(grupo_sistema)
        form_sistema.setContentsMargins(20, 20, 20, 20)
        
        self.nome_sistema = QLineEdit("Project Parallel")
        self.nome_sistema.setReadOnly(True)
        self.nome_sistema.setObjectName("configInputOnly")
        form_sistema.addRow("📌 Nome do Sistema:", self.nome_sistema)
        
        self.versao = QLineEdit("1.0.0")
        self.versao.setReadOnly(True)
        self.versao.setObjectName("configInputReadonly")
        form_sistema.addRow("🔢 Versão:", self.versao)
        
        self.empresa_padrao = QComboBox()
        self.empresa_padrao.setObjectName("configCombo")
        form_sistema.addRow("🏢 Empresa Padrão:", self.empresa_padrao)
        
        layout.addWidget(grupo_sistema)
        
        # Grupo: Configurações de Estoque
        grupo_estoque = QGroupBox("Configurações de Estoque")
        grupo_estoque.setObjectName("configGroup")
        form_estoque = QFormLayout(grupo_estoque)
        form_estoque.setContentsMargins(20, 20, 20, 20)
        
        self.alerta_estoque = QSpinBox()
        self.alerta_estoque.setObjectName("configSpin")
        self.alerta_estoque.setRange(0, 100)
        self.alerta_estoque.setValue(5)
        self.alerta_estoque.setSuffix(" unidades")
        form_estoque.addRow("⚠️ Alerta de Estoque Baixo:", self.alerta_estoque)
        
        self.alerta_estoque_critico = QSpinBox()
        self.alerta_estoque_critico.setObjectName("configSpin")
        self.alerta_estoque_critico.setRange(0, 100)
        self.alerta_estoque_critico.setValue(2)
        self.alerta_estoque_critico.setSuffix(" unidades")
        form_estoque.addRow("🔴 Alerta de Estoque Crítico:", self.alerta_estoque_critico)
        
        layout.addWidget(grupo_estoque)
        
        # Grupo: Configurações de Backup
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
        form_backup.addRow("📅 Frequência:", self.frequencia_backup)
        
        self.horario_backup = QTimeEdit()
        self.horario_backup.setTime(QTime(2, 0))
        form_backup.addRow("⏰ Horário:", self.horario_backup)
        
        self.dias_retencao = QSpinBox()
        self.dias_retencao.setRange(7, 365)
        self.dias_retencao.setValue(30)
        self.dias_retencao.setSuffix(" dias")
        form_backup.addRow("📁 Reter backups por:", self.dias_retencao)
        
        layout.addWidget(grupo_backup)
        
        layout.addStretch()
        return widget
    
    def create_tab_backup(self):
        """Aba de gerenciamento de backup"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        
        # Seção: Backup Manual
        grupo_manual = QGroupBox("Backup Manual")
        grupo_manual.setObjectName("configGroup")
        manual_layout = QVBoxLayout(grupo_manual)
        manual_layout.setContentsMargins(20, 20, 20, 20)
        
        btn_executar_backup = QPushButton("🔄 Executar Backup Agora")
        btn_executar_backup.setObjectName("btnPrimary")
        btn_executar_backup.setMinimumHeight(40)
        btn_executar_backup.clicked.connect(self.executar_backup_manual)
        manual_layout.addWidget(btn_executar_backup)
        
        lbl_info = QLabel("⚠️ O backup será salvo na pasta 'backups' do servidor e compactado em formato .gz")
        lbl_info.setStyleSheet("color: #64748b; font-size: 11px; margin-top: 10px;")
        manual_layout.addWidget(lbl_info)
        
        layout.addWidget(grupo_manual)
        
        # Seção: Lista de Backups
        grupo_lista = QGroupBox("Backups Disponíveis")
        grupo_lista.setObjectName("configGroup")
        lista_layout = QVBoxLayout(grupo_lista)
        lista_layout.setContentsMargins(20, 20, 20, 20)
        
        # Tabela de backups
        self.tabela_backups = QTableWidget()
        self.tabela_backups.setColumnCount(3)
        self.tabela_backups.setHorizontalHeaderLabels(["Nome do Arquivo", "Data", "Tamanho"])
        self.tabela_backups.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tabela_backups.verticalHeader().setVisible(False)
        self.tabela_backups.setAlternatingRowColors(True)
        self.tabela_backups.setSortingEnabled(True)
        
        self.tabela_backups.setStyleSheet("""
            QTableWidget::item {
                padding: 10px 8px;
            }
            QHeaderView::section {
                padding: 10px 12px;
            }
        """)
        
        lista_layout.addWidget(self.tabela_backups)
        
        # Botões de ação
        btn_layout = QHBoxLayout()
        
        btn_atualizar_lista = QPushButton("🔄 Atualizar Lista")
        btn_atualizar_lista.clicked.connect(self.carregar_lista_backups)
        btn_layout.addWidget(btn_atualizar_lista)
        
        btn_restaurar = QPushButton("📥 Restaurar Backup")
        btn_restaurar.setObjectName("btnWarning")
        btn_restaurar.clicked.connect(self.restaurar_backup_selecionado)
        btn_layout.addWidget(btn_restaurar)
        
        btn_layout.addStretch()
        lista_layout.addLayout(btn_layout)
        
        layout.addWidget(grupo_lista)
        
        # Carregar lista de backups
        self.carregar_lista_backups()
        
        return widget
    
    def executar_backup_manual(self):
        """Executa backup manual"""
        try:
            QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
            success, result = api_client.executar_backup()
            QApplication.restoreOverrideCursor()
            
            if success:
                notification_manager.success(f"✅ Backup realizado com sucesso!\nArquivo: {result.get('arquivo', 'desconhecido')}", self.window(), 5000)
                self.carregar_lista_backups()
            else:
                notification_manager.error("❌ Erro ao realizar backup", self.window(), 4000)
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
            print(f"❌ Erro ao carregar lista de backups: {e}")
    
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
            f"📅 Data: {backup_data}\n\n"
            f"⚠️ ATENÇÃO: Esta ação irá SUBSTITUIR todos os dados atuais pelos dados do backup.\n"
            f"⚠️ Esta ação não pode ser desfeita!",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            try:
                QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
                success, result = api_client.restaurar_backup(backup_nome)
                QApplication.restoreOverrideCursor()
                
                if success:
                    notification_manager.success("✅ Backup restaurado com sucesso! O sistema será reiniciado.", self.window(), 5000)
                    QTimer.singleShot(2000, self.reiniciar_aplicacao)
                else:
                    notification_manager.error(f"❌ Erro ao restaurar backup: {result.get('detail', 'Erro desconhecido') if result else 'Erro'}", self.window(), 5000)
            except Exception as e:
                QApplication.restoreOverrideCursor()
                notification_manager.error(f"Erro: {e}", self.window(), 4000)
    
    def reiniciar_aplicacao(self):
        """Reinicia a aplicação após restauração"""
        QMessageBox.information(self, "Reiniciando", "O sistema será reiniciado para aplicar as alterações.")
        python = sys.executable
        script = os.path.abspath(sys.argv[0])
        subprocess.Popen([python, script])
        sys.exit(0)
    
    def create_tab_notificacoes(self):
        """Aba de configurações de notificações"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(20)
        
        # Grupo: Notificações do Sistema
        grupo_notificacoes = QGroupBox("Configurações de Notificações")
        grupo_notificacoes.setObjectName("configGroup")
        form_notificacoes = QFormLayout(grupo_notificacoes)
        form_notificacoes.setContentsMargins(20, 20, 20, 20)
        
        self.notif_estoque_baixo = QCheckBox("Notificar quando estoque estiver baixo")
        self.notif_estoque_baixo.setObjectName("configCheckbox")
        self.notif_estoque_baixo.setChecked(True)
        form_notificacoes.addRow("📦", self.notif_estoque_baixo)
        
        self.notif_estoque_critico = QCheckBox("Notificar quando estoque estiver crítico")
        self.notif_estoque_critico.setObjectName("configCheckbox")
        self.notif_estoque_critico.setChecked(True)
        form_notificacoes.addRow("🔴", self.notif_estoque_critico)
        
        self.notif_manutencao = QCheckBox("Notificar sobre manutenções pendentes")
        self.notif_manutencao.setObjectName("configCheckbox")
        self.notif_manutencao.setChecked(True)
        form_notificacoes.addRow("🔧", self.notif_manutencao)
        
        self.notif_pedidos = QCheckBox("Notificar sobre pedidos pendentes de aprovação")
        self.notif_pedidos.setObjectName("configCheckbox")
        self.notif_pedidos.setChecked(True)
        form_notificacoes.addRow("📋", self.notif_pedidos)
        
        self.notif_demandas = QCheckBox("Notificar sobre novas demandas de TI")
        self.notif_demandas.setObjectName("configCheckbox")
        self.notif_demandas.setChecked(True)
        form_notificacoes.addRow("🎫", self.notif_demandas)
        
        self.notif_movimentacoes = QCheckBox("Notificar sobre movimentações de alto valor")
        self.notif_movimentacoes.setObjectName("configCheckbox")
        self.notif_movimentacoes.setChecked(False)
        form_notificacoes.addRow("💰", self.notif_movimentacoes)
        
        self.valor_alto = QSpinBox()
        self.valor_alto.setRange(0, 100000)
        self.valor_alto.setValue(5000)
        self.valor_alto.setSuffix(" R$")
        form_notificacoes.addRow("Valor mínimo para notificação:", self.valor_alto)
        
        layout.addWidget(grupo_notificacoes)
        
        # Grupo: Configurações de Alerta
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
        form_alertas.addRow("⏱️ Intervalo de verificação:", self.intervalo_verificacao)
        
        self.tempo_notificacao = QComboBox()
        self.tempo_notificacao.addItems(["3 segundos", "5 segundos", "10 segundos", "30 segundos"])
        form_alertas.addRow("⏲️ Duração da notificação:", self.tempo_notificacao)
        
        layout.addWidget(grupo_alertas)
        
        # Botão para testar notificação
        btn_testar = QPushButton("🔔 Testar Notificação")
        btn_testar.clicked.connect(self.testar_notificacao)
        layout.addWidget(btn_testar)
        
        layout.addStretch()
        return widget
    
    def create_tab_alertas(self):
        """Aba de configuração de alertas"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(20)
        
        # Grupo: Alertas Ativos
        grupo_alertas = QGroupBox("Alertas do Sistema")
        grupo_alertas.setObjectName("configGroup")
        
        alertas_layout = QVBoxLayout(grupo_alertas)
        alertas_layout.setContentsMargins(20, 20, 20, 20)
        
        self.lista_alertas = QTableWidget()
        self.lista_alertas.setColumnCount(5)
        self.lista_alertas.setHorizontalHeaderLabels(["Tipo", "Mensagem", "Status", "Data", "Ações"])
        self.lista_alertas.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.lista_alertas.setAlternatingRowColors(True)
        
        self.lista_alertas.setStyleSheet("""
            QTableWidget::item {
                padding: 10px 8px;
            }
            QHeaderView::section {
                padding: 10px 12px;
            }
        """)
        alertas_layout.addWidget(self.lista_alertas)
        
        btn_verificar = QPushButton("🔍 Verificar Alertas Agora")
        btn_verificar.clicked.connect(self.verificar_alertas)
        alertas_layout.addWidget(btn_verificar)
        
        layout.addWidget(grupo_alertas)
        
        # Grupo: Histórico de Alertas
        grupo_historico = QGroupBox("Histórico de Alertas")
        grupo_historico.setObjectName("configGroup")
        
        historico_layout = QVBoxLayout(grupo_historico)
        historico_layout.setContentsMargins(20, 20, 20, 20)
        
        self.historico_alertas = QTableWidget()
        self.historico_alertas.setColumnCount(4)
        self.historico_alertas.setHorizontalHeaderLabels(["Data/Hora", "Tipo", "Mensagem", "Status"])
        self.historico_alertas.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.historico_alertas.setAlternatingRowColors(True)
        
        self.historico_alertas.setStyleSheet("""
            QTableWidget::item {
                padding: 10px 8px;
            }
            QHeaderView::section {
                padding: 10px 12px;
            }
        """)
        historico_layout.addWidget(self.historico_alertas)
        
        layout.addWidget(grupo_historico)
        
        layout.addStretch()
        return widget
    
    def create_tab_empresas(self):
        """Aba de gerenciamento de empresas"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        self.tabela_empresas = QTableWidget()
        self.tabela_empresas.setColumnCount(2)
        self.tabela_empresas.setHorizontalHeaderLabels(["ID", "Nome da Empresa"])
        self.tabela_empresas.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tabela_empresas.verticalHeader().setVisible(False)
        
        self.tabela_empresas.setStyleSheet("""
            QTableWidget::item {
                padding: 10px 8px;
            }
            QHeaderView::section {
                padding: 10px 12px;
            }
        """)
        
        self.carregar_tabela_empresas()
        
        layout.addWidget(self.tabela_empresas)
        
        btn_layout = QHBoxLayout()
        btn_adicionar = QPushButton("+ Adicionar Empresa")
        btn_adicionar.clicked.connect(self.adicionar_empresa)
        btn_layout.addWidget(btn_adicionar)
        
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
        self.tabela_departamentos.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tabela_departamentos.verticalHeader().setVisible(False)
        
        self.tabela_departamentos.setStyleSheet("""
            QTableWidget::item {
                padding: 10px 8px;
            }
            QHeaderView::section {
                padding: 10px 12px;
            }
        """)
        
        self.carregar_tabela_departamentos()
        
        layout.addWidget(self.tabela_departamentos)
        
        btn_layout = QHBoxLayout()
        btn_adicionar = QPushButton("+ Adicionar Departamento")
        btn_adicionar.clicked.connect(self.adicionar_departamento)
        btn_layout.addWidget(btn_adicionar)
        
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
        self.tabela_categorias.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tabela_categorias.verticalHeader().setVisible(False)
        
        self.tabela_categorias.setStyleSheet("""
            QTableWidget::item {
                padding: 10px 8px;
            }
            QHeaderView::section {
                padding: 10px 12px;
            }
        """)
        
        self.carregar_tabela_categorias()
        
        layout.addWidget(self.tabela_categorias)
        
        btn_layout = QHBoxLayout()
        btn_adicionar = QPushButton("+ Adicionar Categoria")
        btn_adicionar.clicked.connect(self.adicionar_categoria)
        btn_layout.addWidget(btn_adicionar)
        
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
        self.tabela_cargos.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tabela_cargos.verticalHeader().setVisible(False)

        self.tabela_cargos.setStyleSheet("""
            QTableWidget::item {
                padding: 10px 8px;
            }
            QHeaderView::section {
                padding: 10px 12px;
            }
        """)

        layout.addWidget(self.tabela_cargos)
        
        btn_layout = QHBoxLayout()
        btn_adicionar = QPushButton('+ Adicionar Cargo')
        btn_adicionar.clicked.connect(self.adicionar_cargo)
        btn_layout.addWidget(btn_adicionar)

        btn_remover = QPushButton('- Remover Cargo')
        btn_remover.clicked.connect(self.remover_cargo)
        btn_layout.addWidget(btn_remover)

        btn_refresh = QPushButton('🔄 Atualizar')
        btn_refresh.clicked.connect(self.carregar_tabela_cargos)
        btn_layout.addWidget(btn_refresh)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # Carregar os dados da tabela
        self.carregar_tabela_cargos()

        return widget
    
    def create_tab_servidor(self):
        """Aba de informações do servidor"""
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
        
        titulo_servidor = QLabel("📡 Informações do Servidor")
        titulo_servidor.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        info_layout.addWidget(titulo_servidor)
        
        info_layout.addSpacing(10)
        
        self.status_api = QLabel("Status da API: Verificando...")
        info_layout.addWidget(self.status_api)
        
        self.endereco_server = QLabel(f"Endereço Local: {self.get_ip_local()}")
        info_layout.addWidget(self.endereco_server)
        
        self.porta_server = QLabel("Porta: 8000")
        info_layout.addWidget(self.porta_server)
        
        self.status_banco = QLabel("Banco de Dados: Verificando...")
        info_layout.addWidget(self.status_banco)
        
        self.api_versao = QLabel("Versão da API: Verificando...")
        info_layout.addWidget(self.api_versao)
        
        layout.addWidget(info_frame)
        
        btn_testar = QPushButton("🔄 Testar Conexão")
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
            self.atualizar_combos()
            
            QApplication.restoreOverrideCursor()
            
        except Exception as e:
            QApplication.restoreOverrideCursor()
            print(f"❌ Erro ao carregar listas: {e}")
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
        self.tabela_empresas.setRowCount(len(self.empresas))
        for i, empresa in enumerate(self.empresas):
            self.tabela_empresas.setItem(i, 0, QTableWidgetItem(str(i + 1)))
            self.tabela_empresas.setItem(i, 1, QTableWidgetItem(empresa))
    
    def carregar_tabela_departamentos(self):
        """Carrega a tabela de departamentos do backend"""
        try:
            departamentos = api_client.get_departamentos_completo()
            self.tabela_departamentos.setRowCount(len(departamentos))
            for i, dept in enumerate(departamentos):
                self.tabela_departamentos.setItem(i, 0, QTableWidgetItem(str(dept.get("id", ""))))
                self.tabela_departamentos.setItem(i, 1, QTableWidgetItem(dept.get("nome", "")))
                self.tabela_departamentos.setItem(i, 2, QTableWidgetItem("Ativo" if dept.get("ativo", True) else "Inativo"))
        except Exception as e:
            print(f"❌ Erro ao carregar departamentos: {e}")
    
    def carregar_tabela_categorias(self):
        self.tabela_categorias.setRowCount(len(self.categorias))
        for i, cat in enumerate(self.categorias):
            self.tabela_categorias.setItem(i, 0, QTableWidgetItem(str(i + 1)))
            self.tabela_categorias.setItem(i, 1, QTableWidgetItem(cat))

    def carregar_tabela_cargos(self):
        """Carrega a tabela de cargos do backend"""
        try:
            print("🔍 Carregando cargos...")
            cargos = api_client.get_cargos_completo()
            print(f"🔍 Cargos recebidos: {len(cargos) if cargos else 0}")
            
            if not cargos:
                self.tabela_cargos.setRowCount(0)
                return
            
            self.tabela_cargos.setRowCount(len(cargos))
            for i, cargo in enumerate(cargos):
                self.tabela_cargos.setItem(i, 0, QTableWidgetItem(str(cargo.get("id", ""))))
                self.tabela_cargos.setItem(i, 1, QTableWidgetItem(cargo.get("nome", "")))
                self.tabela_cargos.setItem(i, 2, QTableWidgetItem("Ativo" if cargo.get("ativo", True) else "Inativo"))
            
            self.tabela_cargos.resizeColumnsToContents()
            print(f"✅ Cargos carregados: {len(cargos)}")
        except Exception as e:
            print(f"❌ Erro ao carregar cargos: {e}")
            import traceback
            traceback.print_exc()
    
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
    
    def remover_empresa(self):
        row = self.tabela_empresas.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Atenção", "Selecione uma empresa para remover")
            return
        
        empresa = self.empresas[row]
        
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
            f"⚠️ Esta ação não poderá ser desfeita e só será permitida se nenhuma máquina ou colaborador estiver usando este departamento.",
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
    
    def remover_categoria(self):
        row = self.tabela_categorias.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Atenção", "Selecione uma categoria para remover")
            return
        
        categoria = self.categorias[row]
        
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
            f"⚠️ Esta ação não poderá ser desfeita e só será permitida se nenhum colaborador ou usuário estiver usando este cargo.",
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
    # MÉTODOS EXISTENTES
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
        try:
            response = requests.get("http://10.1.1.151:8000/health", timeout=5)
            if response.status_code == 200:
                self.status_api.setText("✅ Status da API: Online")
                self.status_api.setStyleSheet("color: #2a9d8f;")
                data = response.json()
                self.api_versao.setText(f"📦 Versão da API: {data.get('status', 'Desconhecido')}")
            else:
                self.status_api.setText("❌ Status da API: Offline")
                self.status_api.setStyleSheet("color: #e76f51;")
                self.api_versao.setText("📦 Versão da API: Não disponível")
        except:
            self.status_api.setText("❌ Status da API: Offline")
            self.status_api.setStyleSheet("color: #e76f51;")
            self.api_versao.setText("📦 Versão da API: Não disponível")
        
        try:
            response = requests.get("http://10.1.1.151:8000/health", timeout=5)
            if response.status_code == 200:
                self.status_banco.setText("✅ Banco de Dados: Conectado")
                self.status_banco.setStyleSheet("color: #2a9d8f;")
            else:
                self.status_banco.setText("❌ Banco de Dados: Desconectado")
                self.status_banco.setStyleSheet("color: #e76f51;")
        except:
            self.status_banco.setText("❌ Banco de Dados: Desconectado")
            self.status_banco.setStyleSheet("color: #e76f51;")
    
    def configurar_timer_alertas(self):
        if self.timer_alertas:
            self.timer_alertas.stop()
        
        self.timer_alertas = QTimer()
        self.timer_alertas.timeout.connect(self.verificar_alertas_periodico)
        
        intervalo_texto = self.intervalo_verificacao.currentText()
        if "1 minuto" in intervalo_texto:
            self.timer_alertas.start(60000)
        elif "5 minutos" in intervalo_texto:
            self.timer_alertas.start(300000)
        elif "15 minutos" in intervalo_texto:
            self.timer_alertas.start(900000)
        elif "30 minutos" in intervalo_texto:
            self.timer_alertas.start(1800000)
        else:
            self.timer_alertas.start(3600000)
    
    def verificar_alertas_periodico(self):
        if self.verificar_alertas_auto.isChecked():
            self.verificar_alertas()
    
    def testar_notificacao(self):
        notification_manager.info(
            "Esta é uma notificação de teste!\n\nSe você está vendo isso, as notificações estão funcionando.",
            self.window(),
            5000
        )
    
    def carregar_alertas(self):
        self.verificar_alertas()
    
    def verificar_alertas(self):
        try:
            parent = self.window()
            
            duracao_texto = self.tempo_notificacao.currentText()
            if "3 segundos" in duracao_texto:
                duracao = 4000
            elif "5 segundos" in duracao_texto:
                duracao = 6000
            elif "10 segundos" in duracao_texto:
                duracao = 10000
            else:
                duracao = 8000
            
            materiais = api_client.listar_materiais()
            
            if self.notif_estoque_baixo.isChecked():
                limite_baixo = self.alerta_estoque.value()
                for mat in materiais:
                    qtd = mat.get("quantidade", 0)
                    nome = mat.get("nome", "")
                    if qtd <= limite_baixo and qtd > 0:
                        msg = f"📦 ESTOQUE BAIXO!\n\nMaterial: {nome}\nQuantidade disponível: {qtd} unidades"
                        notification_manager.show(msg, "warning", duracao, parent)
                        return
            
            if self.notif_estoque_critico.isChecked():
                limite_critico = self.alerta_estoque_critico.value()
                for mat in materiais:
                    qtd = mat.get("quantidade", 0)
                    nome = mat.get("nome", "")
                    if qtd <= limite_critico and qtd > 0:
                        msg = f"🔴 ESTOQUE CRÍTICO!\n\nMaterial: {nome}\nQuantidade disponível: {qtd} unidades"
                        notification_manager.show(msg, "error", duracao, parent)
                        return
            
            if self.notif_manutencao.isChecked():
                manutencoes = api_client.listar_manutencoes(status="pendente")
                for man in manutencoes:
                    maquina = man.get('maquina_nome', 'Máquina')
                    msg = f"🔧 MANUTENÇÃO PENDENTE!\n\nMáquina: {maquina}\nDescrição: {man.get('descricao', '')[:50]}"
                    notification_manager.show(msg, "warning", duracao, parent)
                    return
            
            if self.notif_pedidos.isChecked():
                pedidos = api_client.listar_pedidos(status="pendente")
                for ped in pedidos:
                    msg = f"📋 PEDIDO PENDENTE!\n\nMaterial: {ped.get('material_nome', '')}\nQuantidade: {ped.get('quantidade')}\nSolicitante: {ped.get('solicitante')}"
                    notification_manager.show(msg, "info", duracao, parent)
                    return
            
            if self.notif_demandas.isChecked():
                demandas = api_client.listar_demandas(status="aberto")
                for dem in demandas:
                    prioridade = dem.get("prioridade", "media")
                    prioridade_texto = "ALTA" if prioridade == "alta" else "MÉDIA" if prioridade == "media" else "BAIXA"
                    msg = f"🎫 DEMANDA {prioridade_texto}!\n\nTítulo: {dem.get('titulo', '')[:50]}\nSolicitante: {dem.get('solicitante')}"
                    notification_manager.show(msg, "error" if prioridade == "alta" else "warning", duracao, parent)
                    return
            
            print("✅ Nenhum alerta encontrado")
        
        except Exception as e:
            print(f"❌ Erro ao verificar alertas: {e}")
    
    def resolver_alerta(self, row):
        tipo = self.lista_alertas.item(row, 0).text()
        mensagem = self.lista_alertas.item(row, 1).text()
        
        confirm = QMessageBox.question(
            self,
            "Resolver Alerta",
            f"Deseja marcar este alerta como resolvido?\n\n{tipo}: {mensagem}",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            self.adicionar_historico(tipo, mensagem, "Resolvido")
            self.lista_alertas.removeRow(row)
            notification_manager.success("Alerta resolvido com sucesso!", self.window(), 3000)
    
    def adicionar_historico(self, tipo, mensagem, status):
        row = self.historico_alertas.rowCount()
        self.historico_alertas.insertRow(row)
        self.historico_alertas.setItem(row, 0, QTableWidgetItem(datetime.now().strftime("%d/%m/%Y %H:%M")))
        self.historico_alertas.setItem(row, 1, QTableWidgetItem(tipo))
        self.historico_alertas.setItem(row, 2, QTableWidgetItem(mensagem))
        
        status_item = QTableWidgetItem(status)
        if status == "Resolvido":
            status_item.setForeground(QColor(42, 157, 143))
        else:
            status_item.setForeground(QColor(231, 111, 81))
        self.historico_alertas.setItem(row, 3, status_item)
    
    def carregar_configuracoes(self):
        """Carrega as configurações salvas do backend"""
        print("Carregando configurações...")
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
                
                print("✅ Configurações carregadas com sucesso")
            
        except Exception as e:
            print(f"❌ Erro ao carregar configurações: {e}")
        
        self.configurar_timer_alertas()
    
    def salvar_configuracoes(self):
        """Salva as configurações no backend"""
        
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
            "tempo_notificacao": self.tempo_notificacao.currentText()
        }
        
        try:
            success = api_client.salvar_configuracoes(config)
            
            QApplication.restoreOverrideCursor()
            
            if success:
                notification_manager.success("Configurações salvas com sucesso!", self.window(), 3000)
                self.configurar_timer_alertas()
                # Reconfigurar scheduler de backup após salvar
                api_client.reconfigurar_backup()
            else:
                notification_manager.error("Erro ao salvar configurações", self.window(), 3000)
        except Exception as e:
            QApplication.restoreOverrideCursor()
            notification_manager.error(f"Erro ao salvar: {e}", self.window(), 3000)
    
    def cancelar(self):
        notification_manager.info("Alterações canceladas.", self.window(), 2000)
    
    def carregar_dados(self):
        self.carregar_configuracoes()
        self.carregar_info_servidor()
        