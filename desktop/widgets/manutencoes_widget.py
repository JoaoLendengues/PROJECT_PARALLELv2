from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QTableWidget, QHeaderView,
                               QMessageBox)
from PySide6.QtCore import Qt


class ManutencoesWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.info_label = None
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        
        header = QHBoxLayout()
        
        titulo = QLabel("🔧 Manutenções")
        titulo.setProperty("class", "page-title")
        header.addWidget(titulo)
        
        header.addStretch()
        
        self.btn_novo = QPushButton("+ Nova Manutenção")
        self.btn_novo.setFixedHeight(40)
        self.btn_novo.clicked.connect(self.nova_manutencao)
        header.addWidget(self.btn_novo)
        
        self.btn_atualizar = QPushButton("🔄 Atualizar")
        self.btn_atualizar.setFixedHeight(40)
        self.btn_atualizar.clicked.connect(self.carregar_dados)
        header.addWidget(self.btn_atualizar)
        
        layout.addLayout(header)
        
        self.tabela = QTableWidget()
        self.tabela.setAlternatingRowColors(True)
        self.tabela.setSelectionBehavior(QTableWidget.SelectRows)
        
        headers = ["ID", "Máquina", "Tipo", "Descrição", "Data Início", "Responsável", "Status"]
        self.tabela.setColumnCount(len(headers))
        self.tabela.setHorizontalHeaderLabels(headers)
        
        self.tabela.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        
        layout.addWidget(self.tabela)
        
        acoes = QHBoxLayout()
        acoes.addStretch()
        
        self.btn_concluir = QPushButton("✓ Concluir")
        self.btn_concluir.clicked.connect(self.concluir_manutencao)
        acoes.addWidget(self.btn_concluir)
        
        layout.addLayout(acoes)
        
        self.mostrar_placeholder()
    
    def mostrar_placeholder(self):
        self.tabela.setVisible(False)
        self.info_label = QLabel("⏳ Aguardando conexão com o backend...")
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setStyleSheet("color: #64748b; font-size: 14px; padding: 50px;")
        layout = self.layout()
        layout.addWidget(self.info_label)
    
    def remover_placeholder(self):
        if self.info_label:
            self.info_label.deleteLater()
            self.info_label = None
        self.tabela.setVisible(True)
    
    def nova_manutencao(self):
        QMessageBox.information(self, "Em desenvolvimento", "Funcionalidade será implementada em breve!")
    
    def concluir_manutencao(self):
        row = self.tabela.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Atenção", "Selecione uma manutenção para concluir")
            return
        QMessageBox.information(self, "Em desenvolvimento", "Funcionalidade será implementada em breve!")
    
    def carregar_dados(self):
        print("Carregando manutenções...")
        