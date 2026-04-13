from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QFrame, QGridLayout)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QCursor
from datetime import datetime
from api_client import api_client


class HomeWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.usuario_nome = None
        self.main_window = None  # Referência para a janela principal
        self.init_ui()
    
    def set_usuario(self, nome):
        """Define o nome do usuário para a saudação"""
        self.usuario_nome = nome
        self.update_saudacao()

    def set_main_window(self, main_window):
        """Define a referência para a janela principal (para navegação)"""
        self.main_window = main_window
    
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
        
        # Timer para atualizar data e hora
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_datetime)
        self.timer.start(1000)
        
        self.update_datetime()
        
        # Cards
        self.cards_layout = QGridLayout()
        self.cards_layout.setSpacing(20)
        layout.addLayout(self.cards_layout)
        
        # Criar cards interativos
        self.criar_cards_interativos()

        # Carregar dados da API
        self.carregar_dados()
        
        layout.addStretch()
    
    def update_datetime(self):
        now = datetime.now()
        # Formatar data em Português
        dias_semana = ['Segunda-feira', 'Terça-feira', 'Quarta-feira', 'Quinta-feira', 'Sexta-feira', 'Sábado', 'Domingo']
        meses = ['janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho',
                 'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro']
        
        dia_semana = dias_semana[now.weekday()]
        dia = now.day
        mes = meses[now.month - 1]
        ano = now.year
        hora = now.strftime('%H:%M')

        self.data_hora_label.setText(f'{dia_semana}, {dia} de {mes} de {ano} - {hora}')
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
    
    def criar_cards_interativos(self):
        """Cria os cards interativos com efeito hover e clique"""
        
        # Configuração dos cards
        cards_config = [
            {
                "nome": "materiais",
                "icono": "📦",
                "titulo": "Materiais em Estoque",
                "cor_icone": "#3b82f6",
                "cor_hover": "#dbeafe",
                "subtitulo": "Atualmente em estoque.",
                "link": "Clique para gerenciar",
                "acao": "show_materiais"
            },
            {
                "nome": "maquinas",
                "icono": "🖥️",
                "titulo": "Máquinas Ativas",
                "cor_icone": "#10b981",
                "cor_hover": "#d1fae5",
                "subtitulo": "Máquinas em operação.",
                "link": "Clique para ver",
                "acao": "show_maquinas"
            },
            {
                "nome": "manutencoes",
                "icono": "🔧",
                "titulo": "Manutenções Pendentes",
                "cor_icone": "#f59e0b",
                "cor_hover": "#fed7aa",
                "subtitulo": "Tarefas agendadas.",
                "link": "Ações necessárias",
                "acao": "show_manutencoes"
            },
            {
                "nome": "pedidos",
                "icono": "📋",
                "titulo": "Pedidos Pendentes",
                "cor_icone": "#8b5cf6",
                "cor_hover": "#ede9fe",
                "subtitulo": "Pedidos de compra.",
                "link": "Aguardando aprovação",
                "acao": "show_pedidos"
            }
        ]
        
        # Posições dos cards no grid (linha, coluna)
        posicoes = [
            (0, 0),  # Materiais
            (0, 1),  # Máquinas
            (1, 0),  # Manutenções
            (1, 1),  # Pedidos
        ]
        
        for config, pos in zip(cards_config, posicoes):
            card = self.criar_card(config)
            self.cards_layout.addWidget(card, pos[0], pos[1])
            
            # Guardar referência para atualizar valores
            setattr(self, f"value_{config['nome']}", card.valor_label)
    
    def criar_card(self, config):
        """Cria um card individual com efeitos interativos"""
        
        card = QFrame()
        card.setProperty("class", "dashboard-card")
        card.setMinimumHeight(160)
        card.setMaximumHeight(190)
        card.setCursor(QCursor(Qt.PointingHandCursor))  # Mãozinha ao passar o mouse
        
        # Estilo do card com efeito hover
        card.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border-radius: 16px;
                border: 1px solid #e2e8f0;
            }}
            QFrame:hover {{
                background-color: {config['cor_hover']};
                border: 1px solid {config['cor_icone']};
            }}
            QFrame > QLabel{{
                border: none;
                outline: none;
            }}
        """)
        
        # Layout interno
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(6)
        
        # Ícone
        icon_label = QLabel(config['icono'])
        icon_label.setFont(QFont("Segoe UI", 24))
        icon_label.setStyleSheet(f"color: {config['cor_icone']}; background: transparent; border: none; outline: none;")
        layout.addWidget(icon_label)
        
        # Título
        title_label = QLabel(config['titulo'])
        title_label.setStyleSheet("color: #64748b; font-size: 13px; font-weight: 500; background: transparent; border: none; outline: none;")
        layout.addWidget(title_label)
        
        # Valor (será atualizado dinamicamente)
        valor_label = QLabel("0")
        valor_label.setStyleSheet(f"color: {config['cor_icone']}; font-size: 28px; font-weight: bold; background: transparent; border: none; outline: none;")
        layout.addWidget(valor_label)
        
        # Subtítulo
        subtitle_label = QLabel(config['subtitulo'])
        subtitle_label.setStyleSheet("color: #94a3b8; font-size: 11px; background: transparent; border: none; outline: none;")
        subtitle_label.setWordWrap(True)
        layout.addWidget(subtitle_label)
        
        layout.addStretch()
        
        # Link (SEM BORDA) - LINHA CORRIGIDA
        link_label = QLabel(config['link'])
        link_label.setStyleSheet(f"color: {config['cor_icone']}; font-size: 11px; font-weight: 500; background: transparent; border: none; outline: none;")
        layout.addWidget(link_label)
        
        # Armazenar o valor_label como atributo do card para fácil acesso
        card.valor_label = valor_label
        
        # Conectar clique
        acao = config['acao']
        card.mousePressEvent = lambda event, a=acao: self.executar_acao(a)
        
        return card
    
    def executar_acao(self, acao):
        """Executa a ação de navegação correspondente ao card clicado"""
        if self.main_window and hasattr(self.main_window, acao):
            # Chamar o método da MainWindow para trocar de tela
            getattr(self.main_window, acao)()
    
    def carregar_dados(self):
        """Carrega os dados do dashboard da API"""
        print("Carregando dados do dashboard...")
    
        try:
            dados = api_client.get_dashboard_resumo()
            resumo = dados.get("resumo", {})
        
            # Atualizar valores nos cards
            self.value_materiais.setText(str(resumo.get("total_materiais", 0)))
            self.value_maquinas.setText(str(resumo.get("maquinas_ativas", 0)))
            self.value_manutencoes.setText(str(resumo.get("manutencoes_pendentes", 0)))
            self.value_pedidos.setText(str(resumo.get("pedidos_pendentes", 0)))
            
            print(f"✅ Dashboard atualizado: Materiais={resumo.get('total_materiais', 0)}")
            
        except Exception as e:
            print(f"❌ Erro ao carregar dashboard: {e}")
