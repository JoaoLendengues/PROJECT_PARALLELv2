from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QTableWidget, QHeaderView,
                               QMessageBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont


class MateriaisWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.info_label = None
        self.init_ui()
    
    def init_ui(self):
        # Layout principal
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        
        # === CABEÇALHO ===
        header = QHBoxLayout()
        
        # Título
        titulo = QLabel("📦 Materiais")
        titulo.setProperty("class", "page-title")
        header.addWidget(titulo)
        
        header.addStretch()
        
        # Botões do cabeçalho
        self.novo_btn = QPushButton("➕ Novo Material")
        self.novo_btn.setFixedHeight(40)
        self.novo_btn.clicked.connect(self.novo_material)
        header.addWidget(self.novo_btn)
        
        self.atualizar_btn = QPushButton("🔄 Atualizar")
        self.atualizar_btn.setFixedHeight(40)
        self.atualizar_btn.clicked.connect(self.carregar_dados)
        header.addWidget(self.atualizar_btn)
        
        layout.addLayout(header)
        
        # === TABELA ===
        self.tabela = QTableWidget()
        self.tabela.setAlternatingRowColors(True)
        self.tabela.setSelectionBehavior(QTableWidget.SelectRows)
        
        # Configurar colunas
        headers = ["ID", "Nome", "Descrição", "Quantidade", "Categoria", "Empresa", "Status"]
        self.tabela.setColumnCount(len(headers))
        self.tabela.setHorizontalHeaderLabels(headers)
        
        # Ajustar largura das colunas
        self.tabela.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tabela.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        
        layout.addWidget(self.tabela)
        
        # === BOTÕES DE AÇÃO ===
        acoes = QHBoxLayout()
        acoes.addStretch()
        
        self.editar_btn = QPushButton("✏️ Editar")
        self.editar_btn.clicked.connect(self.editar_material)
        acoes.addWidget(self.editar_btn)
        
        self.deletar_btn = QPushButton("🗑️ Deletar")
        self.deletar_btn.clicked.connect(self.deletar_material)
        acoes.addWidget(self.deletar_btn)
        
        layout.addLayout(acoes)
        
        # === PLACEHOLDER ===
        self.mostrar_placeholder()
    
    def mostrar_placeholder(self):
        """Mostra mensagem enquanto não há dados"""
        # Esconder a tabela
        self.tabela.setVisible(False)
        
        # Criar label de informação
        self.info_label = QLabel(
            "⏳ Aguardando conexão com o backend...\n\n"
            "Esta tela será carregada quando o servidor estiver rodando."
        )
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setStyleSheet("color: #64748b; font-size: 14px; padding: 50px;")
        
        # Adicionar ao layout
        layout = self.layout()
        layout.addWidget(self.info_label)
    
    def remover_placeholder(self):
        """Remove o placeholder e mostra a tabela"""
        if self.info_label:
            self.info_label.deleteLater()
            self.info_label = None
        self.tabela.setVisible(True)
    
    def novo_material(self):
        """Abre diálogo para criar novo material"""
        QMessageBox.information(
            self, 
            "Em desenvolvimento", 
            "Funcionalidade será implementada em breve!"
        )
    
    def editar_material(self):
        """Edita o material selecionado"""
        current_row = self.tabela.currentRow()
        if current_row < 0:
            QMessageBox.warning(
                self, 
                "Atenção", 
                "Selecione um material para editar"
            )
            return
        QMessageBox.information(
            self, 
            "Em desenvolvimento", 
            "Funcionalidade será implementada em breve!"
        )
    
    def deletar_material(self):
        """Deleta o material selecionado"""
        current_row = self.tabela.currentRow()
        if current_row < 0:
            QMessageBox.warning(
                self, 
                "Atenção", 
                "Selecione um material para deletar"
            )
            return
        QMessageBox.information(
            self, 
            "Em desenvolvimento", 
            "Funcionalidade será implementada em breve!"
        )
    
    def carregar_dados(self):
        """Carrega os dados dos materiais da API"""
        print("Carregando materiais...")
        # TODO: Conectar com a API depois
        # Quando tiver dados, chamar: self.remover_placeholder()
