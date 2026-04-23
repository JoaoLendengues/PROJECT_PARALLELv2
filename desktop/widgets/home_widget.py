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
        self.main_window = None
        self._loaded = False  # ✅ Flag para controle de carregamento
        self.init_ui()
        
        # Timer para atualizar status da internet a cada 30 segundos (já começa após carregar)
        self.timer_internet = None
    
    def set_usuario(self, nome):
        """Define o nome do usuário para a saudação"""
        self.usuario_nome = nome
        self.update_saudacao()

    def set_main_window(self, main_window):
        """Define a referência para a janela principal (para navegação)"""
        self.main_window = main_window
    
    def on_show(self):
        """✅ Chamado quando a aba é selecionada - carrega dados sob demanda"""
        if not self._loaded:
            self.carregar_dados()
            self._loaded = True
            
            # Iniciar timer de internet APÓS o primeiro carregamento
            if not self.timer_internet:
                self.timer_internet = QTimer()
                self.timer_internet.timeout.connect(self.atualizar_status_internet)
                self.timer_internet.start(30000)  # 30 segundos
    
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
        
        # Timer para data/hora (sempre rodando)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_datetime)
        self.timer.start(1000)
        self.update_datetime()
        
        # Cards
        self.cards_layout = QGridLayout()
        self.cards_layout.setSpacing(20)
        layout.addLayout(self.cards_layout)
        
        # Criar cards interativos (UI apenas, sem dados)
        self.criar_cards_interativos()
        
        # ⚠️ NÃO carregar dados aqui - será feito no on_show()
        
        layout.addStretch()
    
    def update_datetime(self):
        now = datetime.now()
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
            },
            {
                "nome": "demandas",
                "icono": "🎫",
                "titulo": "Demandas Abertas",
                "cor_icone": "#ef4444",
                "cor_hover": "#fee2e2",
                "subtitulo": "Chamados de TI pendentes.",
                "link": "Ver demandas",
                "acao": "show_demandas"
            },
            {
                "nome": "internet",
                "icono": "🌐",
                "titulo": "Status da Internet",
                "cor_icone": "#06b6d4",
                "cor_hover": "#cffafe",
                "subtitulo": "Qualidade da conexão.",
                "link": "Atualizar",
                "acao": "atualizar_status_internet",
                "especial": True
            }
        ]
        
        posicoes = [
            (0, 0),  # Materiais
            (0, 1),  # Máquinas
            (1, 0),  # Manutenções
            (1, 1),  # Pedidos
            (2, 0),  # Demandas
            (2, 1),  # Status da Internet
        ]
        
        for config, pos in zip(cards_config, posicoes):
            if config.get("especial") and config["nome"] == "internet":
                card = self.criar_card_internet(config)
                self.internet_card = card
            else:
                card = self.criar_card(config)
                setattr(self, f"value_{config['nome']}", card.valor_label)
            
            self.cards_layout.addWidget(card, pos[0], pos[1])
    
    def criar_card(self, config):
        """Cria um card individual com efeitos interativos"""
        
        card = QFrame()
        card.setProperty("class", "dashboard-card")
        card.setMinimumHeight(160)
        card.setMaximumHeight(190)
        card.setCursor(QCursor(Qt.PointingHandCursor))
        
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
            QFrame > QLabel {{
                border: none;
                outline: none;
            }}
        """)
        
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
        
        # Valor
        valor_label = QLabel("0")
        valor_label.setStyleSheet(f"color: {config['cor_icone']}; font-size: 28px; font-weight: bold; background: transparent; border: none; outline: none;")
        layout.addWidget(valor_label)
        
        # Subtítulo
        subtitle_label = QLabel(config['subtitulo'])
        subtitle_label.setStyleSheet("color: #94a3b8; font-size: 11px; background: transparent; border: none; outline: none;")
        subtitle_label.setWordWrap(True)
        layout.addWidget(subtitle_label)
        
        layout.addStretch()
        
        # Link
        link_label = QLabel(config['link'])
        link_label.setStyleSheet(f"color: {config['cor_icone']}; font-size: 11px; font-weight: 500; background: transparent; border: none; outline: none;")
        layout.addWidget(link_label)
        
        card.valor_label = valor_label
        
        acao = config['acao']
        card.mousePressEvent = lambda event, a=acao: self.executar_acao(a)
        
        return card
    
    def criar_card_internet(self, config):
        """Cria o card especial para status da internet (padronizado)"""
        
        card = QFrame()
        card.setProperty("class", "dashboard-card")
        card.setMinimumHeight(160)
        card.setMaximumHeight(190)
        card.setCursor(QCursor(Qt.PointingHandCursor))
        
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
            QFrame > QLabel {{
                border: none;
                outline: none;
            }}
        """)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(6)
        
        # Ícone (dinâmico - muda conforme o status)
        self.internet_icon = QLabel(config['icono'])
        self.internet_icon.setFont(QFont("Segoe UI", 24))
        self.internet_icon.setStyleSheet(f"color: {config['cor_icone']}; background: transparent; border: none;")
        layout.addWidget(self.internet_icon)
        
        # Título
        title_label = QLabel(config['titulo'])
        title_label.setStyleSheet("color: #64748b; font-size: 13px; font-weight: 500; background: transparent; border: none;")
        layout.addWidget(title_label)
        
        # VALOR PRINCIPAL (ex: "Excelente", "Ruim", "Offline") - como os outros cards
        self.internet_valor = QLabel("Verificando...")
        self.internet_valor.setStyleSheet("font-size: 20px; font-weight: bold; background: transparent; border: none;")
        layout.addWidget(self.internet_valor)
        
        # Subtítulo (ex: "Latência: 45 ms")
        self.internet_subtitulo = QLabel("Medindo conexão...")
        self.internet_subtitulo.setStyleSheet("color: #94a3b8; font-size: 11px; background: transparent; border: none;")
        self.internet_subtitulo.setWordWrap(True)
        layout.addWidget(self.internet_subtitulo)
        
        layout.addStretch()
        
        # Link
        link_label = QLabel(config['link'])
        link_label.setStyleSheet(f"color: {config['cor_icone']}; font-size: 11px; font-weight: 500; background: transparent; border: none;")
        layout.addWidget(link_label)
        
        card.valor_label = None
        
        acao = config['acao']
        card.mousePressEvent = lambda event, a=acao: self.executar_acao(a)
        
        return card
    
    def executar_acao(self, acao):
        """Executa a ação correspondente ao card clicado"""
        if acao == "atualizar_status_internet":
            self.atualizar_status_internet()
            return
        
        if self.main_window and hasattr(self.main_window, acao):
            getattr(self.main_window, acao)()
    
    def atualizar_status_internet(self):
        """Atualiza o status da internet no card (padronizado)"""
        from widgets.toast_notification import notification_manager
        
        try:
            status = api_client.get_status_internet()
            
            if status.get("status") == "online":
                qualidade = status.get("qualidade", "regular")
                latencia = status.get("latencia_ms", 0)
                cor = status.get("cor", "#06b6d4")
                
                textos_qualidade = {
                    "excelente": "🟢 Excelente",
                    "bom": "📶 Bom",
                    "regular": "⚠️ Regular",
                    "ruim": "🔴 Ruim"
                }
                
                texto_qualidade = textos_qualidade.get(qualidade, "🟡 Desconhecido")
                
                self.internet_valor.setText(texto_qualidade)
                self.internet_valor.setStyleSheet(f"color: {cor}; font-size: 20px; font-weight: bold; background: transparent; border: none;")
                self.internet_subtitulo.setText(f"Latência: {latencia} ms")
                self.internet_icon.setText(status.get("icone", "🌐"))
                self.internet_icon.setStyleSheet(f"color: {cor}; background: transparent; border: none;")
                
                notification_manager.success(f"✅ Internet: {qualidade.upper()} ({latencia} ms)", self.window(), 3000)
                
            else:
                self.internet_valor.setText("🔴 Offline")
                self.internet_valor.setStyleSheet("color: #ef4444; font-size: 20px; font-weight: bold; background: transparent; border: none;")
                self.internet_subtitulo.setText("Sem conexão com a internet")
                self.internet_icon.setText("❌")
                notification_manager.error("❌ Sem conexão com a internet", self.window(), 4000)
                
        except Exception as e:
            print(f"❌ Erro ao atualizar status da internet: {e}")
            self.internet_valor.setText("❌ Erro")
            self.internet_valor.setStyleSheet("color: #ef4444; font-size: 20px; font-weight: bold; background: transparent; border: none;")
            self.internet_subtitulo.setText("Falha na medição")
    
    def carregar_dados(self):
        """Carrega os dados do dashboard da API"""
        print("Carregando dados do dashboard...")

        try:
            dados = api_client.get_dashboard_resumo()
            resumo = dados.get("resumo", {})
        
            self.value_materiais.setText(str(resumo.get("total_materiais", 0)))
            self.value_maquinas.setText(str(resumo.get("maquinas_ativas", 0)))
            self.value_manutencoes.setText(str(resumo.get("manutencoes_pendentes", 0)))
            self.value_pedidos.setText(str(resumo.get("pedidos_pendentes", 0)))
            
            if hasattr(self, 'value_demandas'):
                self.value_demandas.setText(str(resumo.get("demandas_abertas", 0)))
            
            print(f"✅ Dashboard atualizado: Materiais={resumo.get('total_materiais', 0)}")
            
        except Exception as e:
            print(f"❌ Erro ao carregar dashboard: {e}")
        
        # Atualizar status da internet ao carregar a tela
        self.atualizar_status_internet()
        