from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer
from PySide6.QtGui import QFont


class ToastNotification(QFrame):
    """Notificação estilo Toast - Widget interno (não janela separada)"""
    
    def __init__(self, message, tipo="info", parent=None, duration=5000, 
                 prioridade="baixa", acao=None, acao_id=None, notificacao_id=None):
        super().__init__(parent)
        
        self.prioridade = prioridade
        self.acao = acao
        self.acao_id = acao_id
        self.notificacao_id = notificacao_id
        self.parent_window = parent
        
        # Configurar como widget normal (não janela separada)
        self.setAttribute(Qt.WA_DeleteOnClose)
        
        # Cores por prioridade (fundos sólidos)
        cores = {
            "alta": {
                "bg": "#FEE2E2",
                "bg_hover": "#FECACA",
                "border": "#DC2626",
                "icon": "🔴",
                "titulo": "ALERTA",
                "texto": "#991B1B"
            },
            "media": {
                "bg": "#FEF3C7",
                "bg_hover": "#FDE68A",
                "border": "#D97706",
                "icon": "⚠️",
                "titulo": "ATENÇÃO",
                "texto": "#92400E"
            },
            "baixa": {
                "bg": "#DBEAFE",
                "bg_hover": "#BFDBFE",
                "border": "#2563EB",
                "icon": "ℹ️",
                "titulo": "INFORMAÇÃO",
                "texto": "#1E3A8A"
            }
        }
        
        cor = cores.get(prioridade, cores["baixa"])
        
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {cor['bg']};
                border-radius: 8px;
                border: 1px solid {cor['border']};
            }}
            QFrame:hover {{
                background-color: {cor['bg_hover']};
            }}
            QLabel {{
                color: {cor['texto']};
                background-color: transparent;
                border: none;
            }}
            QPushButton {{
                background-color: rgba(0, 0, 0, 0.08);
                color: {cor['texto']};
                border: none;
                font-size: 11px;
                font-weight: 500;
                padding: 4px 10px;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: rgba(0, 0, 0, 0.15);
            }}
        """)
        
        # Layout principal
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        content_frame = QFrame()
        content_frame.setStyleSheet("background-color: transparent;")
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(12, 10, 12, 10)
        content_layout.setSpacing(6)
        
        # Cabeçalho
        header_layout = QHBoxLayout()
        
        icon_label = QLabel(cor["icon"])
        icon_label.setFont(QFont("Segoe UI", 16))
        header_layout.addWidget(icon_label)
        
        title_label = QLabel(cor["titulo"])
        title_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(22, 22)
        close_btn.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        close_btn.clicked.connect(self.fechar_animado)
        header_layout.addWidget(close_btn)
        
        content_layout.addLayout(header_layout)
        
        # Linha separadora
        linha = QFrame()
        linha.setFrameShape(QFrame.HLine)
        linha.setStyleSheet(f"background-color: {cor['border']}; max-height: 1px;")
        content_layout.addWidget(linha)
        
        # Mensagem
        self.message_label = QLabel(message)
        self.message_label.setFont(QFont("Segoe UI", 9))
        self.message_label.setWordWrap(True)
        self.message_label.setMinimumWidth(250)
        self.message_label.setMaximumWidth(320)
        content_layout.addWidget(self.message_label)
        
        # Botões de ação
        if acao:
            btn_layout = QHBoxLayout()
            btn_layout.addStretch()
            
            action_btn = QPushButton("🔍 Ver")
            action_btn.clicked.connect(self.executar_acao)
            btn_layout.addWidget(action_btn)
            
            ignore_btn = QPushButton("🙈 Ignorar")
            ignore_btn.clicked.connect(self.ignorar)
            btn_layout.addWidget(ignore_btn)
            
            content_layout.addLayout(btn_layout)
        
        main_layout.addWidget(content_frame)
        
        self.adjustSize()
        self.posicionar()
        self.show()
        
        # Animação de entrada (fade in)
        self.setGraphicsEffect(None)
        self.anim_entrada = QPropertyAnimation(self, b"windowOpacity")
        self.anim_entrada.setDuration(200)
        self.anim_entrada.setStartValue(0)
        self.anim_entrada.setEndValue(1)
        self.anim_entrada.start()
        
        if duration > 0:
            self.timer_fechar = QTimer()
            self.timer_fechar.setSingleShot(True)
            self.timer_fechar.timeout.connect(self.fechar_animado)
            self.timer_fechar.start(duration)
    
    def posicionar(self):
        """Posiciona a notificação no topo central da janela pai"""
        if self.parent():
            parent_rect = self.parent().rect()
            x = (parent_rect.width() - self.width()) // 2
            y = 10
            self.move(x, y)
    
    def executar_acao(self):
        """Executa a ação da notificação"""
        self.fechar_animado()
        if self.parent_window and self.acao:
            if hasattr(self.parent_window, self.acao):
                getattr(self.parent_window, self.acao)()
    
    def ignorar(self):
        """Ignora a notificação"""
        self.fechar_animado()
    
    def fechar_animado(self):
        if hasattr(self, 'timer_fechar'):
            self.timer_fechar.stop()
        
        self.anim_saida = QPropertyAnimation(self, b"windowOpacity")
        self.anim_saida.setDuration(200)
        self.anim_saida.setStartValue(1)
        self.anim_saida.setEndValue(0)
        self.anim_saida.finished.connect(self.fechar)
        self.anim_saida.start()
    
    def fechar(self):
        self.hide()
        self.deleteLater()


class NotificationManager:
    """Gerenciador de notificações do sistema"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._fila = []
            cls._instance._notificacao_atual = None
            cls._instance._parent = None
            cls._instance._sons_habilitados = True
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        if not hasattr(self, '_fila'):
            self._fila = []
        if not hasattr(self, '_notificacao_atual'):
            self._notificacao_atual = None
        if not hasattr(self, '_parent'):
            self._parent = None
        if not hasattr(self, '_sons_habilitados'):
            self._sons_habilitados = True
    
    def set_parent(self, parent):
        self._parent = parent
    
    def set_sons_habilitados(self, habilitado):
        self._sons_habilitados = habilitado
        try:
            from core.sound_manager import sound_manager
            sound_manager.set_habilitado(habilitado)
        except:
            pass
    
    def show(self, message, tipo="info", duration=5000, parent=None, 
             prioridade="baixa", acao=None, acao_id=None, notificacao_id=None):
        
        print(f"🔍 DEBUG show: acao recebido = {acao}")
        print(f"🔍 DEBUG show: parent = {parent}")
        
        if self._sons_habilitados:
            try:
                from core.sound_manager import sound_manager
                sound_manager.tocar(prioridade)
            except:
                pass
        
        if parent is None:
            parent = self._parent
        
        self._fila.append({
            "message": message,
            "tipo": tipo,
            "duration": duration,
            "parent": parent,
            "prioridade": prioridade,
            "acao": acao,
            "acao_id": acao_id,
            "notificacao_id": notificacao_id
        })
        
        print(f"🔍 DEBUG show: item adicionado à fila com acao={acao}")
        
        if self._notificacao_atual is None:
            self._exibir_proxima()
    
    def _exibir_proxima(self):
        if not self._fila:
            self._notificacao_atual = None
            return
        
        item = self._fila.pop(0)
        
        print(f"🔍 DEBUG _exibir_proxima: item acao = {item.get('acao')}")
        
        parent = item["parent"]
        if parent and hasattr(parent, 'window'):
            parent = parent.window()
        
        self._notificacao_atual = ToastNotification(
            item["message"],
            item["tipo"],
            parent,
            item["duration"],
            item["prioridade"],
            item["acao"],
            item["acao_id"],
            item["notificacao_id"]
        )
        
        self._notificacao_atual.destroyed.connect(self._proxima)
    
    def _proxima(self):
        self._notificacao_atual = None
        self._exibir_proxima()
    
    def success(self, message, parent=None, duration=4000, acao=None, acao_id=None):
        return self.show(message, "success", duration, parent, "baixa", acao, acao_id)
    
    def warning(self, message, parent=None, duration=5000, acao=None, acao_id=None):
        return self.show(message, "warning", duration, parent, "media", acao, acao_id)
    
    def error(self, message, parent=None, duration=6000, acao=None, acao_id=None):
        return self.show(message, "error", duration, parent, "alta", acao, acao_id)
    
    def info(self, message, parent=None, duration=4000, acao=None, acao_id=None):
        return self.show(message, "info", duration, parent, "baixa", acao, acao_id)
    
    def limpar_fila(self):
        if self._notificacao_atual:
            self._notificacao_atual.fechar()
        self._fila.clear()


notification_manager = NotificationManager()
