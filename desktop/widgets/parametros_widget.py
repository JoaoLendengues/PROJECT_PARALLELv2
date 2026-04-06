from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QFormLayout, QLineEdit,
                               QComboBox, QSpinBox, QCheckBox, QGroupBox,
                               QTabWidget, QMessageBox, QTableWidget,
                               QTableWidgetItem, QHeaderView, QDialog,
                               QDialogButtonBox, QFrame, QScrollArea)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QColor
from api_client import api_client
import socket
import requests


class ParametrosWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.empresas = ["Matriz", "Filial 1", "Filial 2", "Filial 3"]
        self.departamentos = ["TI", "Administrativo", "Financeiro", "RH", "Comercial", "Marketing", "Logística"]
        self.categorias = ["Periféricos", "Hardware", "Armazenamento", "Monitores", "Cabos", "Redes", "Consumíveis", "Softwares"]
        self.init_ui()
        self.carregar_configuracoes()
        self.carregar_info_servidor()
    
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
        
        tab_empresas = self.create_tab_empresas()
        tabs.addTab(tab_empresas, "🏢 Empresas")
        
        tab_departamentos = self.create_tab_departamentos()
        tabs.addTab(tab_departamentos, "📁 Departamentos")
        
        tab_categorias = self.create_tab_categorias()
        tabs.addTab(tab_categorias, "📂 Categorias")
        
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
        self.nome_sistema.setObjectName("configInput")
        form_sistema.addRow("📌 Nome do Sistema:", self.nome_sistema)
        
        self.versao = QLineEdit("1.0.0")
        self.versao.setReadOnly(True)
        self.versao.setObjectName("configInputReadonly")
        form_sistema.addRow("🔢 Versão:", self.versao)
        
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
        
        self.notificar_estoque = QCheckBox("Notificar quando estoque estiver baixo")
        self.notificar_estoque.setObjectName("configCheckbox")
        self.notificar_estoque.setChecked(True)
        form_estoque.addRow("", self.notificar_estoque)
        
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
        
        self.horario_backup = QComboBox()
        self.horario_backup.setObjectName("configCombo")
        self.horario_backup.addItems(["00:00", "01:00", "02:00", "03:00", "04:00", "05:00", "06:00", "07:00", "08:00", "09:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00", "17:00", "18:00", "19:00", "20:00", "21:00", "22:00", "23:00"])
        form_backup.addRow("⏰ Horário:", self.horario_backup)
        
        layout.addWidget(grupo_backup)
        
        layout.addStretch()
        return widget
    
    def create_tab_empresas(self):
        """Aba de gerenciamento de empresas"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Tabela de empresas
        self.tabela_empresas = QTableWidget()
        self.tabela_empresas.setColumnCount(2)
        self.tabela_empresas.setHorizontalHeaderLabels(["ID", "Nome da Empresa"])
        self.tabela_empresas.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        
        # Carregar empresas
        self.carregar_tabela_empresas()
        
        layout.addWidget(self.tabela_empresas)
        
        # Botões
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
        
        # Tabela de departamentos
        self.tabela_departamentos = QTableWidget()
        self.tabela_departamentos.setColumnCount(2)
        self.tabela_departamentos.setHorizontalHeaderLabels(["ID", "Departamento"])
        self.tabela_departamentos.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        
        # Carregar departamentos
        self.carregar_tabela_departamentos()
        
        layout.addWidget(self.tabela_departamentos)
        
        # Botões
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
        
        # Tabela de categorias
        self.tabela_categorias = QTableWidget()
        self.tabela_categorias.setColumnCount(2)
        self.tabela_categorias.setHorizontalHeaderLabels(["ID", "Categoria"])
        self.tabela_categorias.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        
        # Carregar categorias
        self.carregar_tabela_categorias()
        
        layout.addWidget(self.tabela_categorias)
        
        # Botões
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
    
    def create_tab_servidor(self):
        """Aba de informações do servidor"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        
        # Card de informações
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
        
        # Título
        titulo_servidor = QLabel("📡 Informações do Servidor")
        titulo_servidor.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        info_layout.addWidget(titulo_servidor)
        
        info_layout.addSpacing(10)
        
        # Status da API
        self.status_api = QLabel("Status da API: Verificando...")
        info_layout.addWidget(self.status_api)
        
        # Endereço do servidor
        self.endereco_server = QLabel(f"Endereço Local: {self.get_ip_local()}")
        info_layout.addWidget(self.endereco_server)
        
        # Porta
        self.porta_server = QLabel("Porta: 8000")
        info_layout.addWidget(self.porta_server)
        
        # Status do banco
        self.status_banco = QLabel("Banco de Dados: Verificando...")
        info_layout.addWidget(self.status_banco)
        
        # Versão da API
        self.api_versao = QLabel("Versão da API: Verificando...")
        info_layout.addWidget(self.api_versao)
        
        layout.addWidget(info_frame)
        
        # Botão de teste
        btn_testar = QPushButton("🔄 Testar Conexão")
        btn_testar.clicked.connect(self.carregar_info_servidor)
        layout.addWidget(btn_testar)
        
        layout.addStretch()
        
        # Timer para atualização periódica
        self.timer_servidor = QTimer()
        self.timer_servidor.timeout.connect(self.carregar_info_servidor)
        self.timer_servidor.start(30000)  # Atualiza a cada 30 segundos
        
        return widget
    
    def carregar_tabela_empresas(self):
        """Carrega a tabela de empresas"""
        self.tabela_empresas.setRowCount(len(self.empresas))
        for i, empresa in enumerate(self.empresas):
            self.tabela_empresas.setItem(i, 0, QTableWidgetItem(str(i + 1)))
            self.tabela_empresas.setItem(i, 1, QTableWidgetItem(empresa))
    
    def carregar_tabela_departamentos(self):
        """Carrega a tabela de departamentos"""
        self.tabela_departamentos.setRowCount(len(self.departamentos))
        for i, dept in enumerate(self.departamentos):
            self.tabela_departamentos.setItem(i, 0, QTableWidgetItem(str(i + 1)))
            self.tabela_departamentos.setItem(i, 1, QTableWidgetItem(dept))
    
    def carregar_tabela_categorias(self):
        """Carrega a tabela de categorias"""
        self.tabela_categorias.setRowCount(len(self.categorias))
        for i, cat in enumerate(self.categorias):
            self.tabela_categorias.setItem(i, 0, QTableWidgetItem(str(i + 1)))
            self.tabela_categorias.setItem(i, 1, QTableWidgetItem(cat))
    
    def adicionar_empresa(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Adicionar Empresa")
        dialog.setModal(True)
        dialog.setMinimumWidth(300)
        
        layout = QVBoxLayout(dialog)
        nome_edit = QLineEdit()
        nome_edit.setPlaceholderText("Nome da empresa")
        layout.addWidget(nome_edit)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec():
            nome = nome_edit.text().strip()
            if nome and nome not in self.empresas:
                self.empresas.append(nome)
                self.carregar_tabela_empresas()
    
    def remover_empresa(self):
        row = self.tabela_empresas.currentRow()
        if row >= 0 and row < len(self.empresas):
            self.empresas.pop(row)
            self.carregar_tabela_empresas()
    
    def adicionar_departamento(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Adicionar Departamento")
        dialog.setModal(True)
        dialog.setMinimumWidth(300)
        
        layout = QVBoxLayout(dialog)
        nome_edit = QLineEdit()
        nome_edit.setPlaceholderText("Nome do departamento")
        layout.addWidget(nome_edit)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec():
            nome = nome_edit.text().strip()
            if nome and nome not in self.departamentos:
                self.departamentos.append(nome)
                self.carregar_tabela_departamentos()
    
    def remover_departamento(self):
        row = self.tabela_departamentos.currentRow()
        if row >= 0 and row < len(self.departamentos):
            self.departamentos.pop(row)
            self.carregar_tabela_departamentos()
    
    def adicionar_categoria(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Adicionar Categoria")
        dialog.setModal(True)
        dialog.setMinimumWidth(300)
        
        layout = QVBoxLayout(dialog)
        nome_edit = QLineEdit()
        nome_edit.setPlaceholderText("Nome da categoria")
        layout.addWidget(nome_edit)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec():
            nome = nome_edit.text().strip()
            if nome and nome not in self.categorias:
                self.categorias.append(nome)
                self.carregar_tabela_categorias()
    
    def remover_categoria(self):
        row = self.tabela_categorias.currentRow()
        if row >= 0 and row < len(self.categorias):
            self.categorias.pop(row)
            self.carregar_tabela_categorias()
    
    def get_ip_local(self):
        """Obtém o IP local da máquina"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"
    
    def carregar_info_servidor(self):
        """Carrega informações do servidor"""
        try:
            # Testar API
            response = requests.get("http://localhost:8000/health", timeout=5)
            if response.status_code == 200:
                self.status_api.setText("✅ Status da API: Online")
                self.status_api.setStyleSheet("color: #2a9d8f;")
                data = response.json()
                self.api_versao.setText(f"📦 Versão da API: {data.get('status', 'Desconhecido')}")
            else:
                self.status_api.setText("❌ Status da API: Offline")
                self.status_api.setStyleSheet("color: #e76f51;")
                self.api_versao.setText("📦 Versão da API: Não disponível")
        except Exception as e:
            self.status_api.setText("❌ Status da API: Offline")
            self.status_api.setStyleSheet("color: #e76f51;")
            self.api_versao.setText("📦 Versão da API: Não disponível")
        
        # Testar banco (via API)
        try:
            response = requests.get("http://localhost:8000/health", timeout=5)
            if response.status_code == 200:
                self.status_banco.setText("✅ Banco de Dados: Conectado")
                self.status_banco.setStyleSheet("color: #2a9d8f;")
            else:
                self.status_banco.setText("❌ Banco de Dados: Desconectado")
                self.status_banco.setStyleSheet("color: #e76f51;")
        except:
            self.status_banco.setText("❌ Banco de Dados: Desconectado")
            self.status_banco.setStyleSheet("color: #e76f51;")
    
    def carregar_configuracoes(self):
        """Carrega as configurações salvas (futuramente do backend)"""
        print("Carregando configurações...")
    
    def salvar_configuracoes(self):
        """Salva as configurações no backend"""
        # Aqui enviaremos as configurações para o backend
        config = {
            "nome_sistema": self.nome_sistema.text(),
            "alerta_estoque": self.alerta_estoque.value(),
            "notificar_estoque": self.notificar_estoque.isChecked(),
            "backup_automatico": self.backup_automatico.isChecked(),
            "frequencia_backup": self.frequencia_backup.currentText(),
            "horario_backup": self.horario_backup.currentText(),
            "empresas": self.empresas,
            "departamentos": self.departamentos,
            "categorias": self.categorias
        }
        
        # TODO: Enviar para o backend via API
        print(f"Configurações salvas: {config}")
        
        QMessageBox.information(self, "Sucesso", "Configurações salvas com sucesso!\n\nAs alterações serão aplicadas após reiniciar o sistema.")
    
    def cancelar(self):
        """Cancela as alterações"""
        QMessageBox.information(self, "Cancelado", "Alterações canceladas.")
    
    def carregar_dados(self):
        """Carrega os dados (chamado pelo main_window)"""
        self.carregar_configuracoes()
        self.carregar_info_servidor()
        