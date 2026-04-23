from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer, QPoint
from PySide6.QtGui import QFont


class ToastNotification(QFrame):
    """Notificação estilo Retangular Moderna - Animação suave"""
    
    def __init__(self, message, tipo="info", parent=None, duration=8000, 
                 prioridade="baixa", acao=None, acao_id=None, notificacao_id=None):
        super().__init__(parent)
        
        self.prioridade = prioridade
        self.acao = acao
        self.acao_id = acao_id
        self.notificacao_id = notificacao_id
        self.parent_window = parent
        self._duration = duration
        
        # Configurar como widget normal
        self.setAttribute(Qt.WA_DeleteOnClose)
        
        # Cores por prioridade
        cores = {
            "alta": {
                "bg": "#DC2626",
                "border_left": "#991B1B",
                "icon": "🔴",
                "titulo": "ALERTA"
            },
            "media": {
                "bg": "#D97706",
                "border_left": "#92400E",
                "icon": "⚠️",
                "titulo": "ATENÇÃO"
            },
            "baixa": {
                "bg": "#2563EB",
                "border_left": "#1E3A8A",
                "icon": "ℹ️",
                "titulo": "INFORMAÇÃO"
            }
        }
        
        self.cor = cores.get(prioridade, cores["baixa"])
        
        # Estilo - NOTIFICAÇÃO RETANGULAR
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {self.cor['bg']};
                border-left: 6px solid {self.cor['border_left']};
                border-radius: 8px;
            }}
            QLabel {{
                color: #FFFFFF;
                background-color: transparent;
                border: none;
            }}
            QPushButton {{
                background-color: rgba(255, 255, 255, 0.2);
                color: #FFFFFF;
                border: none;
                font-size: 12px;
                font-weight: bold;
                padding: 6px 16px;
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background-color: rgba(255, 255, 255, 0.35);
            }}
        """)
        
        self.init_ui(message)
        self.setup_animations()
        
        # Posicionar e iniciar animação
        self.posicionar()
        self.show_animation()
        
        # Timer para fechar
        if duration > 0:
            self.timer_fechar = QTimer()
            self.timer_fechar.setSingleShot(True)
            self.timer_fechar.timeout.connect(self.fechar_animado)
            self.timer_fechar.start(duration)
    
    def init_ui(self, message):
        """Inicializa a UI - NOTIFICAÇÃO RETANGULAR"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 12, 16, 12)
        layout.setSpacing(15)
        
        # Ícone
        self.icon_label = QLabel(self.cor["icon"])
        self.icon_label.setFont(QFont("Segoe UI", 20))
        layout.addWidget(self.icon_label)
        
        # Conteúdo principal (Vertical)
        content_layout = QVBoxLayout()
        content_layout.setSpacing(6)
        
        # Título
        self.title_label = QLabel(self.cor["titulo"])
        self.title_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        content_layout.addWidget(self.title_label)
        
        # Mensagem (com quebra de linha)
        self.message_label = QLabel(message)
        self.message_label.setFont(QFont("Segoe UI", 10))
        self.message_label.setWordWrap(True)
        self.message_label.setMaximumWidth(400)
        content_layout.addWidget(self.message_label)
        
        layout.addLayout(content_layout)
        
        # Botões
        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(8)
        
        if self.acao:
            self.action_btn = QPushButton("🔍 Ver")
            self.action_btn.setFixedHeight(32)
            self.action_btn.clicked.connect(self.executar_acao)
            btn_layout.addWidget(self.action_btn)
        
        self.close_btn = QPushButton("✕ Fechar")
        self.close_btn.setFixedHeight(32)
        self.close_btn.clicked.connect(self.fechar_animado)
        btn_layout.addWidget(self.close_btn)
        
        layout.addLayout(btn_layout)
        
        # Ajustar tamanho
        self.adjustSize()
        self.setFixedSize(self.width() + 20, self.height())
    
    def setup_animations(self):
        """Configura as animações"""
        self.opacity_anim = QPropertyAnimation(self, b"windowOpacity")
        self.opacity_anim.setDuration(250)
        self.opacity_anim.setEasingCurve(QEasingCurve.InOutQuad)
        
        self.slide_anim = QPropertyAnimation(self, b"pos")
        self.slide_anim.setDuration(300)
        self.slide_anim.setEasingCurve(QEasingCurve.OutCubic)
    
    def posicionar(self):
        """✅ Posiciona a notificação no SUPERIOR CENTRAL"""
        if self.parent():
            parent_rect = self.parent().rect()
            x = (parent_rect.width() - self.width()) // 2
            y = 20
            self.move(x, y)
    
    def show_animation(self):
        """Animação de entrada - slide + fade"""
        self.setWindowOpacity(0)
        self.show()
        
        final_pos = self.pos()
        start_pos = QPoint(final_pos.x(), final_pos.y() - 50)
        self.move(start_pos)
        
        self.opacity_anim.setStartValue(0)
        self.opacity_anim.setEndValue(1)
        self.opacity_anim.start()
        
        self.slide_anim.setStartValue(start_pos)
        self.slide_anim.setEndValue(final_pos)
        self.slide_anim.start()
    
    def fechar_animado(self):
        """Animação de saída - fade out + slide up"""
        if hasattr(self, 'timer_fechar'):
            self.timer_fechar.stop()
        
        current_pos = self.pos()
        end_pos = QPoint(current_pos.x(), current_pos.y() - 50)
        
        self.opacity_anim.setStartValue(1)
        self.opacity_anim.setEndValue(0)
        self.opacity_anim.start()
        
        self.slide_anim.setStartValue(current_pos)
        self.slide_anim.setEndValue(end_pos)
        self.slide_anim.start()
        
        self.opacity_anim.finished.connect(self.fechar)
    
    def fechar(self):
        """Fecha a notificação"""
        self.hide()
        self.deleteLater()
    
    def executar_acao(self):
        """Executa a ação da notificação"""
        self.fechar_animado()
        if self.parent_window and self.acao:
            if hasattr(self.parent_window, self.acao):
                getattr(self.parent_window, self.acao)()
    
    def mousePressEvent(self, event):
        super().mousePressEvent(event)


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
            cls._instance._delay_entre_notificacoes = 300  # ✅ Pequeno delay entre notificações
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
        if not hasattr(self, '_delay_entre_notificacoes'):
            self._delay_entre_notificacoes = 300
    
    def set_parent(self, parent):
        self._parent = parent
    
    def set_sons_habilitados(self, habilitado):
        self._sons_habilitados = habilitado
        try:
            from core.sound_manager import sound_manager
            sound_manager.set_habilitado(habilitado)
        except:
            pass
    
    def show(self, message, tipo="info", duration=8000, parent=None, 
             prioridade="baixa", acao=None, acao_id=None, notificacao_id=None):
        
        if self._sons_habilitados:
            try:
                from core.sound_manager import sound_manager
                sound_manager.tocar(prioridade)
            except:
                pass
        
        if parent is None:
            parent = self._parent
        
        # ✅ Adicionar à fila
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
        
        print(f"📊 Notificação adicionada à fila. Tamanho: {len(self._fila)}")
        
        # ✅ Só exibir se não tiver nenhuma notificação ativa
        if self._notificacao_atual is None:
            self._exibir_proxima()
    
    def _exibir_proxima(self):
        """Exibe a próxima notificação da fila"""
        if not self._fila:
            self._notificacao_atual = None
            print("📭 Fila vazia. Aguardando...")
            return
        
        item = self._fila.pop(0)
        print(f"🔔 Exibindo notificação. Restam {len(self._fila)} na fila")
        
        parent = item['parent']
        if parent and hasattr(parent, 'window'):
            try:
                if parent and not getattr(parent, 'deleted', False):
                    parent = parent.window()
                else:
                    parent = None
            except:
                parent = None
        
        # ✅ Criar a notificação
        self._notificacao_atual = ToastNotification(
            item['message'],
            item['tipo'],
            parent,
            item['duration'],
            item['prioridade'],
            item['acao'],
            item['acao_id'],
            item['notificacao_id']
        )
        
        # ✅ Quando a notificação for destruída, chamar _proxima
        self._notificacao_atual.destroyed.connect(self._proxima)
    
    def _proxima(self):
        """Chamado quando a notificação atual é fechada/destruída"""
        self._notificacao_atual = None
        print("✅ Notificação fechada. Verificando próxima...")
        
        # ✅ Pequeno delay antes de mostrar a próxima
        QTimer.singleShot(300, self._exibir_proxima)
    
    def success(self, message, parent=None, duration=8000, acao=None, acao_id=None):
        return self.show(message, "success", duration, parent, "baixa", acao, acao_id)
    
    def warning(self, message, parent=None, duration=8000, acao=None, acao_id=None):
        return self.show(message, "warning", duration, parent, "media", acao, acao_id)
    
    def error(self, message, parent=None, duration=10000, acao=None, acao_id=None):
        return self.show(message, "error", duration, parent, "alta", acao, acao_id)
    
    def info(self, message, parent=None, duration=8000, acao=None, acao_id=None):
        return self.show(message, "info", duration, parent, "baixa", acao, acao_id)
    
    def limpar_fila(self):
        if self._notificacao_atual:
            self._notificacao_atual.fechar()
        self._fila.clear()
        print("🧹 Fila de notificações limpa")


notification_manager = NotificationManager()
