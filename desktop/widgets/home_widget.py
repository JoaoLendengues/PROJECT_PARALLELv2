from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QFrame, QGridLayout)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont
from datetime import datetime
from api_client import api_client


class HomeWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.usuario_nome = None
        self.valor_materiais = QLabel("0")
        self.valor_maquinas = QLabel("0")
        self.valor_manutencoes = QLabel("0")
        self.valor_pedidos = QLabel("0")
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
        
        # Timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_datetime)
        self.timer.start(1000)
        
        self.update_datetime()
        
        # Cards
        self.cards_layout = QGridLayout()
        self.cards_layout.setSpacing(20)
        layout.addLayout(self.cards_layout)
        
        # Criar cards manualmente um por um
        self.criar_cards_manualmente()

        # Carregar dados da API com um pequeno delay para garantir que os cards foram criados
        QTimer.singleShot(100, self.carregar_dados)
        
        layout.addStretch()
    
    def update_datetime(self):
        now = datetime.now()
        self.data_hora_label.setText(now.strftime("%A, %d de %B de %Y - %H:%M"))
        self.update_saudacao()
    
    def update_saudacao(self):
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
    
    def criar_cards_manualmente(self):
        """Cria os cards manualmente para evitar duplicação"""
        
        # Card 1 - Materiais
        card1 = QFrame()
        card1.setProperty("class", "dashboard-card")
        card1.setMinimumHeight(180)
        layout1 = QVBoxLayout(card1)
        layout1.setContentsMargins(20, 15, 20, 15)
        layout1.setSpacing(8)
        
        icon1 = QLabel("📦")
        icon1.setFont(QFont("Segoe UI", 28))
        layout1.addWidget(icon1)
        
        title1 = QLabel("Materiais em Estoque")
        title1.setStyleSheet("color: #64748b; font-size: 14px; font-weight: 500;")
        layout1.addWidget(title1)
        
        value1 = QLabel("1.452")
        value1.setStyleSheet("color: #3b82f6; font-size: 36px; font-weight: bold;")
        layout1.addWidget(value1)
        
        subtitle1 = QLabel("Atualmente em estoque.")
        subtitle1.setStyleSheet("color: #94a3b8; font-size: 18px;")
        layout1.addWidget(subtitle1)
        
        layout1.addStretch()
        
        link1 = QLabel("Clique para gerenciar")
        link1.setStyleSheet("color: #3b82f6; font-size: 12px; font-weight: 500; border-top: 1px solid #e2e8f0; padding-top: 10px;")
        layout1.addWidget(link1)
        
        # Card 2 - Máquinas
        card2 = QFrame()
        card2.setProperty("class", "dashboard-card")
        card2.setMinimumHeight(180)
        layout2 = QVBoxLayout(card2)
        layout2.setContentsMargins(20, 15, 20, 15)
        layout2.setSpacing(8)
        
        icon2 = QLabel("🖥️")
        icon2.setFont(QFont("Segoe UI", 28))
        layout2.addWidget(icon2)
        
        title2 = QLabel("Máquinas Ativas")
        title2.setStyleSheet("color: #64748b; font-size: 14px; font-weight: 500;")
        layout2.addWidget(title2)
        
        value2 = QLabel("18")
        value2.setStyleSheet("color: #10b981; font-size: 36px; font-weight: bold;")
        layout2.addWidget(value2)
        
        subtitle2 = QLabel("Máquinas em operação.")
        subtitle2.setStyleSheet("color: #94a3b8; font-size: 18px;")
        layout2.addWidget(subtitle2)
        
        layout2.addStretch()
        
        link2 = QLabel("Clique para ver")
        link2.setStyleSheet("color: #10b981; font-size: 14px; font-weight: 500; border-top: 1px solid #e2e8f0; padding-top: 10px;")
        layout2.addWidget(link2)
        
        # Card 3 - Manutenções
        card3 = QFrame()
        card3.setProperty("class", "dashboard-card")
        card3.setMinimumHeight(180)
        layout3 = QVBoxLayout(card3)
        layout3.setContentsMargins(20, 15, 20, 15)
        layout3.setSpacing(8)
        
        icon3 = QLabel("🔧")
        icon3.setFont(QFont("Segoe UI", 28))
        layout3.addWidget(icon3)
        
        title3 = QLabel("Manutenções Pendentes")
        title3.setStyleSheet("color: #64748b; font-size: 14px; font-weight: 500;")
        layout3.addWidget(title3)
        
        value3 = QLabel("7")
        value3.setStyleSheet("color: #f59e0b; font-size: 36px; font-weight: bold;")
        layout3.addWidget(value3)
        
        subtitle3 = QLabel("Tarefas agendadas.")
        subtitle3.setStyleSheet("color: #94a3b8; font-size: 18px;")
        layout3.addWidget(subtitle3)
        
        layout3.addStretch()
        
        link3 = QLabel("Ações necessárias")
        link3.setStyleSheet("color: #f59e0b; font-size: 12px; font-weight: 500; border-top: 1px solid #e2e8f0; padding-top: 10px;")
        layout3.addWidget(link3)
        
        # Card 4 - Pedidos
        card4 = QFrame()
        card4.setProperty("class", "dashboard-card")
        card4.setMinimumHeight(180)
        layout4 = QVBoxLayout(card4)
        layout4.setContentsMargins(20, 15, 20, 15)
        layout4.setSpacing(8)
        
        icon4 = QLabel("📋")
        icon4.setFont(QFont("Segoe UI", 28))
        layout4.addWidget(icon4)
        
        title4 = QLabel("Pedidos Pendentes")
        title4.setStyleSheet("color: #64748b; font-size: 14px; font-weight: 500;")
        layout4.addWidget(title4)
        
        value4 = QLabel("24")
        value4.setStyleSheet("color: #8b5cf6; font-size: 36px; font-weight: bold;")
        layout4.addWidget(value4)
        
        subtitle4 = QLabel("Pedidos de compra e venda.")
        subtitle4.setStyleSheet("color: #94a3b8; font-size: 18px;")
        layout4.addWidget(subtitle4)
        
        layout4.addStretch()
        
        link4 = QLabel("Aguardando aprovação")
        link4.setStyleSheet("color: #8b5cf6; font-size: 12px; font-weight: 500; border-top: 1px solid #e2e8f0; padding-top: 10px;")
        layout4.addWidget(link4)
        
        # Adicionar cards ao layout
        self.cards_layout.addWidget(card1, 0, 0)
        self.cards_layout.addWidget(card2, 0, 1)
        self.cards_layout.addWidget(card3, 1, 0)
        self.cards_layout.addWidget(card4, 1, 1)
    
    def carregar_dados(self):
        """Carrega os dados do dashboard da API"""
        print("Carregando dados do dashboard...")
    
        try:
            dados = api_client.get_dashboard_resumo()
            resumo = dados.get("resumo", {})
        
            # Atualizar valores nos cards
            self.valor_materiais.setText(str(resumo.get("total_materiais", 0)))
            self.valor_maquinas.setText(str(resumo.get("maquinas_ativas", 0)))
            self.valor_manutencoes.setText(str(resumo.get("manutencoes_pendentes", 0)))
            self.valor_pedidos.setText(str(resumo.get("pedidos_pendentes", 0)))
            
            print(f"✅ Dashboard atualizado: Materiais={resumo.get('total_materiais', 0)}")
            
        except Exception as e:
            print(f"❌ Erro ao carregar dashboard: {e}")

            
