from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                                QFrame, QGridLayout, QScrollArea)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont
from datetime import datetime

class HomeWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(24)

        # Cabeçalho com saudação
        header = QHBoxLayout()

        # Saudação
        self.saudacao_label = QLabel()
        self.saudacao_label.setFont(QFont('Segoe UI', 24, QFont.Weight.Bold))
        self.saudacao_label.setStyleSheet('color: #1e293b;')
        header.addWidget(self.saudacao_label)

        header.addStretch()

        # Data e Hora
        self.data_hora_label = QLabel()
        self.data_hora_label.setFont(QFont('Segoe UI', 18))
        self.data_hora_label.setStyleSheet('color: #64748b; background-color: #f1f5f9; padding 8px 16px; border-radius: 12px;')
        self.data_hora_label.setAlignment(Qt.AlignRight)
        header.addWidget(self.data_hora_label)

        layout.addLayout(header)

        # Atualizar saudação e data/hora
        self.update_datetime()

        # Timer para atualizar a cada segundo
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_datetime)
        self.timer.start(1000)

        # Cards de resumo (Serão preenchidos com dados da API depois)
        self.cards_layout = QGridLayout()
        self.cards_layout.setSpacing(20)
        layout.addLayout(self.cards_layout)

        # Criar cards placeholder
        self.create_cards()

        layout.addStretch()

    def update_datetime(self):
        """Atualiza a saudação e data/hora"""
        now = datetime.now()

        # Definir saudação baseada na hora
        hora = now.hour
        if hora < 12:
            saudacao = 'Bom dia'
        elif hora < 18:
            saudacao = 'Boa tarde'
        else:
            saudacao = 'Boa noite'
    
        self.saudacao_label.setText(f'{saudacao}, pessoa!')
        self.data_hora_label.setText(now.strftime('%d/%m/%Y • %H:%M'))

    def create_cards(self):
        """Cria os cards de informações do dashboard"""
        cards_data = [
            {
                "title": "Materiais em Estoque",
                "value": "1,452",
                "subtitle": "Atualmente em estoque.",
                "link": "Clique para gerenciar",
                "color": "#2c7da0",
                "icon": "📦",
                "class": "card-1"
            },
            {
                "title": "Máquinas Ativas",
                "value": "18",
                "subtitle": "Máquinas em operação.",
                "link": "Clique para ver",
                "color": "#2a9d8f",
                "icon": "🖥️",
                "class": "card-2"
            },
            {
                "title": "Manutenções Pendentes",
                "value": "7",
                "subtitle": "Tarefas agendadas.",
                "link": "Ações necessárias",
                "color": "#e76f51",
                "icon": "🔧",
                "class": "card-3"
            },
            {
                "title": "Pedidos Pendentes",
                "value": "24",
                "subtitle": "Pedidos de compra e venda.",
                "link": "Aguardando aprovação",
                "color": "#f4a261",
                "icon": "📋",
                "class": "card-4"
            }
        ]

        # Limpar layout existente
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        row, col = 0, 0
        for card_data in cards_data:
            card = self.create_card(card_data)
            self.cards_layout.addWidget(card, row, col)
            col += 1
            if col >= 2:
                col = 0
                row += 1

    def create_card(self, data):
        """Cria um card individual"""
        card = QFrame()
        card.setProperty('class', f'dashboard-card {data['class']}')
        card.setFixedHeight(180)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(8)

        # Cabeçalho do card do ícone
        header_layout = QHBoxLayout()

        # Ícone
        icon_label = QLabel(data['icon'])
        icon_label.setFont(QFont("Segoe UI", 24))
        header_layout.addWidget(icon_label)

        header_layout.addStretch()

        layout.addLayout(header_layout)

        # Título
        title_label = QLabel(data['title'])
        title_label.setProperty('class', 'card-title')
        title_label.setFont(QFont('Segoe UI', 12, QFont.Weight.Medium))
        title_label.setStyleSheet('Color: #64748b;')
        layout.addWidget(title_label)


        # Valor
        value_label = QLabel(data['value'])
        value_label.setProperty('class', 'card-value')
        value_label.setFont(QFont('Segoe UI', 36, QFont.Weight.Bold))
        value_label.setStyleSheet(f'color: {data['color']};')
        layout.addWidget(value_label)


        # Subtítulo
        subtitle_label = QLabel(data['subtitle'])
        subtitle_label.setProperty('class', 'card-subtitle')
        subtitle_label.setFont(QFont('Segoe UI', 11))
        subtitle_label.setStyleSheet('color: #94a3b8;')
        layout.addWidget(subtitle_label)

        layout.addStretch()

        # Link/Botão
        link_label = QLabel(data['link'])
        link_label.setProperty('class', 'card-link')
        link_label.setFont(QFont('Segoe UI', 11, QFont.Weight.Medium))
        link_label.setStyleSheet(f'color: {data['color']}; border-top: 1px solid #e9ecef; padding-top: 12px')
        link_label.setAlignment(Qt.AlignLeft)
        layout.addWidget(link_label)

        return card

    def carregar_dados(self):
        """Carrega os dados do dashboard (será implementado depois)"""
        print('Carregando dados do dashboard...')
    