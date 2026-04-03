from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QFrame, QGridLayout)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont
from datetime import datetime


class HomeWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.usuario_nome = None
        self.init_ui()
    
    def set_usuario(self, nome):
        """Define o nome do usuário para a saudação"""
        self.usuario_nome = nome
        self.update_saudacao()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(24)
        
        # Saudação
        self.saudacao_label = QLabel()
        self.saudacao_label.setFont(QFont("Segoe UI", 28, QFont.Weight.Bold))
        self.saudacao_label.setStyleSheet("color: #1e293b; margin-bottom: 10px;")
        layout.addWidget(self.saudacao_label)
        
        # Data e hora
        self.data_hora_label = QLabel()
        self.data_hora_label.setFont(QFont("Segoe UI", 13))
        self.data_hora_label.setStyleSheet("color: #64748b; margin-bottom: 30px;")
        layout.addWidget(self.data_hora_label)
        
        # Timer para atualizar data/hora
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_datetime)
        self.timer.start(1000)
        
        # Atualizar imediatamente
        self.update_datetime()
        
        # Layout dos cards
        self.cards_layout = QGridLayout()
        self.cards_layout.setSpacing(20)
        layout.addLayout(self.cards_layout)
        
        # Criar os cards do dashboard
        self.create_cards()
        
        layout.addStretch()
    
    def update_datetime(self):
        """Atualiza a data/hora e a saudação"""
        now = datetime.now()
        self.data_hora_label.setText(now.strftime("%A, %d de %B de %Y - %H:%M"))
        self.update_saudacao()
    
    def update_saudacao(self):
        """Atualiza a saudação com o nome do usuário baseado na hora do dia"""
        now = datetime.now()
        hora = now.hour
        
        if hora < 12:
            saudacao = "Bom dia"
        elif hora < 18:
            saudacao = "Boa tarde"
        else:
            saudacao = "Boa noite"
        
        if self.usuario_nome:
            self.saudacao_label.setText(f"{saudacao}, {self.usuario_nome}!")
        else:
            self.saudacao_label.setText(f"{saudacao}!")
    
    def create_cards(self):
        """Cria os cards de informações do dashboard"""
        cards_data = [
            {
                "title": "Materiais em Estoque", 
                "value": "0", 
                "subtitle": "Atualmente em estoque.", 
                "link": "Clique para gerenciar", 
                "color": "#3b82f6", 
                "icon": "📦"
            },
            {
                "title": "Máquinas Ativas", 
                "value": "0", 
                "subtitle": "Máquinas em operação.", 
                "link": "Clique para ver", 
                "color": "#10b981", 
                "icon": "🖥️"
            },
            {
                "title": "Manutenções Pendentes", 
                "value": "0", 
                "subtitle": "Tarefas agendadas.", 
                "link": "Ações necessárias", 
                "color": "#f59e0b", 
                "icon": "🔧"
            },
            {
                "title": "Pedidos Pendentes", 
                "value": "0", 
                "subtitle": "Pedidos de compra e venda.", 
                "link": "Aguardando aprovação", 
                "color": "#8b5cf6", 
                "icon": "📋"
            }
        ]
        
        # Limpar layout existente
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Adicionar cards ao grid
        row, col = 0, 0
        for data in cards_data:
            card = self.create_card(data)
            self.cards_layout.addWidget(card, row, col)
            col += 1
            if col >= 2:
                col = 0
                row += 1
    
    def create_card(self, data):
        """Cria um card individual"""
        card = QFrame()
        card.setProperty("class", "dashboard-card")
        card.setFixedHeight(180)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(8)
        
        # Ícone
        icon_label = QLabel(data["icon"])
        icon_label.setFont(QFont("Segoe UI", 28))
        layout.addWidget(icon_label)
        
        # Título
        title_label = QLabel(data["title"])
        title_label.setStyleSheet("color: #64748b; font-size: 14px; font-weight: 500;")
        layout.addWidget(title_label)
        
        # Valor
        value_label = QLabel(data["value"])
        value_label.setStyleSheet(f"color: {data['color']}; font-size: 36px; font-weight: bold;")
        layout.addWidget(value_label)
        
        # Subtítulo
        subtitle_label = QLabel(data["subtitle"])
        subtitle_label.setStyleSheet("color: #94a3b8; font-size: 12px;")
        layout.addWidget(subtitle_label)
        
        layout.addStretch()
        
        # Link
        link_label = QLabel(data["link"])
        link_label.setStyleSheet(f"color: {data['color']}; font-size: 12px; font-weight: 500; border-top: 1px solid #e2e8f0; padding-top: 12px;")
        layout.addWidget(link_label)
        
        return card
    
    def carregar_dados(self):
        """Carrega os dados do dashboard (será implementado com a API)"""
        print("Carregando dashboard...")
        