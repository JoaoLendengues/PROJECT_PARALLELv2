from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QFormLayout, QLineEdit,
                               QComboBox, QSpinBox, QCheckBox, QGroupBox,
                               QTabWidget, QMessageBox, QFrame, QScrollArea)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont


class ParametrosWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        # Layout principal
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(24, 24, 24, 24)
        
        # Título
        titulo = QLabel("⚙️ Parâmetros do Sistema")
        titulo.setProperty("class", "page-title")
        layout.addWidget(titulo)
        
        # Área de rolagem
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        # Widget de conteúdo
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(20)
        
        # Tabs
        tabs = QTabWidget()
        tabs.setObjectName("paramTabs")
        
        # Criar as abas
        tab_geral = self.create_tab_geral()
        tabs.addTab(tab_geral, "⚙️ Configurações Gerais")
        
        tab_empresas = self.create_tab_empresas()
        tabs.addTab(tab_empresas, "🏢 Empresas")
        
        tab_categorias = self.create_tab_categorias()
        tabs.addTab(tab_categorias, "📁 Categorias")
        
        tab_notificacoes = self.create_tab_notificacoes()
        tabs.addTab(tab_notificacoes, "🔔 Notificações")
        
        content_layout.addWidget(tabs)
        
        # Botões de ação
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.btn_salvar = QPushButton("💾 Salvar Configurações")
        self.btn_salvar.setObjectName("btnPrimary")
        self.btn_salvar.setFixedHeight(40)
        self.btn_salvar.setMinimumWidth(180)
        self.btn_salvar.clicked.connect(self.salvar_configuracoes)
        btn_layout.addWidget(self.btn_salvar)
        
        self.btn_cancelar = QPushButton("❌ Cancelar")
        self.btn_cancelar.setObjectName("btnSecondary")
        self.btn_cancelar.setFixedHeight(40)
        self.btn_cancelar.setMinimumWidth(120)
        self.btn_cancelar.clicked.connect(self.cancelar)
        btn_layout.addWidget(self.btn_cancelar)
        
        content_layout.addLayout(btn_layout)
        content_layout.addStretch()
        
        scroll.setWidget(content_widget)
        layout.addWidget(scroll)
    
    def create_tab_geral(self):
        """Cria a aba de configurações gerais"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(20)
        
        # Grupo: Configurações do Sistema
        grupo_sistema = QGroupBox("Configurações do Sistema")
        grupo_sistema.setObjectName("configGroup")
        
        form_sistema = QFormLayout(grupo_sistema)
        form_sistema.setSpacing(15)
        form_sistema.setLabelAlignment(Qt.AlignRight)
        form_sistema.setContentsMargins(20, 20, 20, 20)
        
        self.nome_sistema = QLineEdit("Project Parallel")
        self.nome_sistema.setObjectName("configInput")
        self.nome_sistema.setMinimumWidth(450)  # <-- ADICIONADO
        self.nome_sistema.setMaximumWidth(600)
        self.nome_sistema.setFixedHeight(35)
        form_sistema.addRow("📌 Nome do Sistema:", self.nome_sistema)
        
        self.versao = QLineEdit("1.0.0")
        self.versao.setReadOnly(True)
        self.versao.setObjectName("configInputReadonly")
        self.versao.setMinimumWidth(400)  # <-- ADICIONADO
        self.versao.setMaximumWidth(500)  # <-- ADICIONADO
        self.versao.setFixedHeight(35)
        form_sistema.addRow("🔢 Versão:", self.versao)
        
        layout.addWidget(grupo_sistema)
        
        # Grupo: Configurações de Estoque
        grupo_estoque = QGroupBox("Configurações de Estoque")
        grupo_estoque.setObjectName("configGroup")
        
        form_estoque = QFormLayout(grupo_estoque)
        form_estoque.setSpacing(15)
        form_estoque.setLabelAlignment(Qt.AlignRight)
        form_estoque.setContentsMargins(20, 20, 20, 20)
        
        self.alerta_estoque = QSpinBox()
        self.alerta_estoque.setObjectName("configSpin")
        self.alerta_estoque.setRange(0, 100)
        self.alerta_estoque.setValue(5)
        self.alerta_estoque.setSuffix(" unidades")
        self.alerta_estoque.setMinimumWidth(200)  # <-- ADICIONADO
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
        form_backup.setSpacing(15)
        form_backup.setLabelAlignment(Qt.AlignRight)
        form_backup.setContentsMargins(20, 20, 20, 20)
        
        self.backup_automatico = QCheckBox("Realizar backup automático")
        self.backup_automatico.setObjectName("configCheckbox")
        self.backup_automatico.setChecked(True)
        form_backup.addRow("", self.backup_automatico)
        
        self.frequencia_backup = QComboBox()
        self.frequencia_backup.setObjectName("configCombo")
        self.frequencia_backup.addItems(["Diário", "Semanal", "Mensal"])
        self.frequencia_backup.setMinimumWidth(200)  # <-- ADICIONADO
        form_backup.addRow("📅 Frequência:", self.frequencia_backup)
        
        layout.addWidget(grupo_backup)
        
        layout.addStretch()
        return widget
    
    def create_tab_empresas(self):
        """Cria a aba de gerenciamento de empresas"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(20)
        
        # Card de informações
        info_frame = QFrame()
        info_frame.setObjectName("infoCard")
        
        info_layout = QVBoxLayout(info_frame)
        
        info_title = QLabel("🏢 Gerenciamento de Empresas")
        info_title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        info_title.setStyleSheet("color: #1e293b; margin-bottom: 12px;")
        info_layout.addWidget(info_title)
        
        info_text = QLabel(
            "Empresas cadastradas no sistema:\n\n"
            "• Matriz\n"
            "• Filial\n\n"
            "📌 Funcionalidade em desenvolvimento - Em breve você poderá:\n"
            "  • Adicionar novas empresas\n"
            "  • Editar informações\n"
            "  • Ativar/desativar filiais"
        )
        info_text.setWordWrap(True)
        info_text.setStyleSheet("color: #5a6e85; font-size: 13px; line-height: 1.5;")
        info_layout.addWidget(info_text)
        
        layout.addWidget(info_frame)
        layout.addStretch()
        
        return widget
    
    def create_tab_categorias(self):
        """Cria a aba de gerenciamento de categorias"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(20)
        
        # Card de informações
        info_frame = QFrame()
        info_frame.setObjectName("infoCard")
        
        info_layout = QVBoxLayout(info_frame)
        
        info_title = QLabel("📁 Categorias de Materiais")
        info_title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        info_title.setStyleSheet("color: #1e293b; margin-bottom: 12px;")
        info_layout.addWidget(info_title)
        
        info_text = QLabel(
            "Categorias disponíveis:\n\n"
            "• Periféricos\n"
            "• Hardware\n"
            "• Armazenamento\n"
            "• Monitores\n"
            "• Cabos\n"
            "• Redes\n"
            "• Consumíveis\n"
            "• Softwares\n\n"
            "📌 Funcionalidade em desenvolvimento - Em breve você poderá:\n"
            "  • Adicionar novas categorias\n"
            "  • Editar categorias existentes\n"
            "  • Definir cores para categorias"
        )
        info_text.setWordWrap(True)
        info_text.setStyleSheet("color: #5a6e85; font-size: 13px; line-height: 1.5;")
        info_layout.addWidget(info_text)
        
        layout.addWidget(info_frame)
        layout.addStretch()
        
        return widget
    
    def create_tab_notificacoes(self):
        """Cria a aba de configurações de notificações"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(20)
        
        # Grupo: Notificações
        grupo_notificacoes = QGroupBox("Configurações de Notificações")
        grupo_notificacoes.setObjectName("configGroup")
        
        form_notificacoes = QFormLayout(grupo_notificacoes)
        form_notificacoes.setSpacing(15)
        form_notificacoes.setContentsMargins(20, 20, 20, 20)
        
        self.notif_manutencao = QCheckBox("Notificar sobre manutenções pendentes")
        self.notif_manutencao.setObjectName("configCheckbox")
        self.notif_manutencao.setChecked(True)
        form_notificacoes.addRow("🔧", self.notif_manutencao)
        
        self.notif_pedidos = QCheckBox("Notificar sobre pedidos pendentes")
        self.notif_pedidos.setObjectName("configCheckbox")
        self.notif_pedidos.setChecked(True)
        form_notificacoes.addRow("📋", self.notif_pedidos)
        
        self.notif_movimentacoes = QCheckBox("Notificar sobre movimentações de alto valor")
        self.notif_movimentacoes.setObjectName("configCheckbox")
        self.notif_movimentacoes.setChecked(False)
        form_notificacoes.addRow("📊", self.notif_movimentacoes)
        
        layout.addWidget(grupo_notificacoes)
        
        # Card de informação adicional
        info_frame = QFrame()
        info_frame.setObjectName("infoCardSmall")
        
        info_layout = QHBoxLayout(info_frame)
        
        info_label = QLabel(
            "💡 As notificações aparecerão no canto superior direito da tela "
            "e também podem ser enviadas por e-mail (configuração futura)."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #92400e; font-size: 12px;")
        info_layout.addWidget(info_label)
        
        layout.addWidget(info_frame)
        layout.addStretch()
        
        return widget
    
    def salvar_configuracoes(self):
        """Salva as configurações"""
        QMessageBox.information(
            self, 
            "Sucesso", 
            "✅ Configurações salvas com sucesso!\n\n"
            "As alterações serão aplicadas após reiniciar o sistema."
        )
    
    def cancelar(self):
        """Cancela as alterações"""
        QMessageBox.information(self, "Cancelado", "❌ Alterações canceladas.")
    
    def carregar_dados(self):
        """Carrega as configurações salvas"""
        print("Carregando parâmetros...")
