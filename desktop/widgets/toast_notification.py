from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer
from PySide6.QtGui import QFont


class ToastNotification(QFrame):
    """Notificação estilo Toast - Restrita à janela do sistema"""
    
    def __init__(self, message, tipo="info", parent=None, duration=5000):
        super().__init__(parent)
        
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_DeleteOnClose)
        
        # Cores fixas e legíveis
        cores = {
            "info": {
                "bg": "#E3F2FD",
                "bg_hover": "#BBDEFB",
                "icon": "ℹ️", 
                "titulo": "INFORMAÇÃO",
                "texto": "#0D47A1"
            },
            "success": {
                "bg": "#E8F5E9", 
                "bg_hover": "#C8E6C9", 
                "icon": "✅", 
                "titulo": "SUCESSO",
                "texto": "#1B5E20"
            },
            "warning": {
                "bg": "#FFF3E0", 
                "bg_hover": "#FFE0B2", 
                "icon": "⚠️", 
                "titulo": "ATENÇÃO",
                "texto": "#E65100"
            },
            "error": {
                "bg": "#FFEBEE", 
                "bg_hover": "#FFCDD2", 
                "icon": "❌", 
                "titulo": "ERRO",
                "texto": "#B71C1C"
            }
        }
        
        cor = cores.get(tipo, cores["info"])
        
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {cor['bg']};
                border-radius: 12px;
                border: 1px solid #d0d0d0;
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
                background-color: transparent;
                color: {cor['texto']};
                border: none;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: rgba(0, 0, 0, 0.08);
                border-radius: 10px;
            }}
        """)
        
        # Layout
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        content_frame = QFrame()
        content_frame.setStyleSheet("background-color: transparent;")
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(15, 12, 15, 12)
        content_layout.setSpacing(5)
        
        # Cabeçalho
        header_layout = QHBoxLayout()
        
        icon_label = QLabel(cor["icon"])
        icon_label.setFont(QFont("Segoe UI", 18))
        header_layout.addWidget(icon_label)
        
        title_label = QLabel(cor["titulo"])
        title_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(22, 22)
        close_btn.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        close_btn.clicked.connect(self.fechar)
        header_layout.addWidget(close_btn)
        
        content_layout.addLayout(header_layout)
        
        # Linha separadora
        linha = QFrame()
        linha.setFrameShape(QFrame.HLine)
        linha.setStyleSheet("background-color: rgba(0,0,0,0.08); max-height: 1px;")
        content_layout.addWidget(linha)
        
        # Mensagem
        self.message_label = QLabel(message)
        self.message_label.setFont(QFont("Segoe UI", 10))
        self.message_label.setWordWrap(True)
        self.message_label.setMinimumWidth(250)
        self.message_label.setMaximumWidth(350)
        content_layout.addWidget(self.message_label)
        
        main_layout.addWidget(content_frame)
        
        # Ajustar tamanho
        self.adjustSize()
        
        # Posicionar
        self.posicionar()
        
        # Mostrar com animação
        self.show()
        
        # Animação de entrada
        self.setWindowOpacity(0)
        self.anim_entrada = QPropertyAnimation(self, b"windowOpacity")
        self.anim_entrada.setDuration(250)
        self.anim_entrada.setStartValue(0)
        self.anim_entrada.setEndValue(1)
        self.anim_entrada.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.anim_entrada.start()
        
        # Auto-fechar
        if duration > 0:
            self.timer_fechar = QTimer()
            self.timer_fechar.setSingleShot(True)
            self.timer_fechar.timeout.connect(self.fechar_animado)
            self.timer_fechar.start(duration)
    
    def posicionar(self):
        """Posiciona a notificação no canto inferior direito da janela pai"""
        if self.parent():
            parent_rect = self.parent().rect()
            x = parent_rect.width() - self.width() - 15
            
            # Calcular posição Y baseado no tamanho da janela
            if parent_rect.height() < 600:
                y = parent_rect.height() - self.height() - 60
            elif parent_rect.height() < 800:
                y = parent_rect.height() - self.height() - 80
            else:
                y = parent_rect.height() - self.height() - 120
            
            self.move(x, y)
        else:
            screen = self.screen().availableGeometry()
            x = screen.width() - self.width() - 15
            y = screen.height() - self.height() - 100
            self.move(x, y)
    
    def fechar_animado(self):
        """Fecha com animação de fade out"""
        if hasattr(self, 'timer_fechar'):
            self.timer_fechar.stop()
        
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        
        self.anim_saida = QPropertyAnimation(self, b"windowOpacity")
        self.anim_saida.setDuration(200)
        self.anim_saida.setStartValue(1)
        self.anim_saida.setEndValue(0)
        self.anim_saida.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.anim_saida.finished.connect(self.fechar)
        self.anim_saida.start()
    
    def fechar(self):
        self.hide()
        self.deleteLater()


class NotificationManager:
    """Gerenciador de notificações do sistema"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._fila = []
            cls._instance._notificacao_atual = None
            cls._instance._parent = None
        return cls._instance
    
    def set_parent(self, parent):
        """Define o parent para as notificações"""
        self._parent = parent
    
    def show(self, message, tipo="info", duration=5000, parent=None):
        """Adiciona notificação à fila"""
        self._fila.append({
            "message": message,
            "tipo": tipo,
            "duration": duration,
            "parent": parent or self._parent
        })
        
        if self._notificacao_atual is None:
            self._exibir_proxima()
    
    def _exibir_proxima(self):
        """Exibe a próxima notificação da fila"""
        if not self._fila:
            self._notificacao_atual = None
            return
        
        item = self._fila.pop(0)
        
        parent = item["parent"]
        if parent and hasattr(parent, 'window'):
            parent = parent.window()
        
        self._notificacao_atual = ToastNotification(
            item["message"], 
            item["tipo"], 
            parent, 
            item["duration"]
        )
        
        self._notificacao_atual.destroyed.connect(self._proxima)
    
    def _proxima(self):
        self._notificacao_atual = None
        self._exibir_proxima()
    
    def success(self, message, parent=None, duration=4000):
        return self.show(message, "success", duration, parent)
    
    def warning(self, message, parent=None, duration=5000):
        return self.show(message, "warning", duration, parent)
    
    def error(self, message, parent=None, duration=6000):
        return self.show(message, "error", duration, parent)
    
    def info(self, message, parent=None, duration=4000):
        return self.show(message, "info", duration, parent)
    
    def limpar_fila(self):
        if self._notificacao_atual:
            self._notificacao_atual.fechar()
        self._fila.clear()


notification_manager = NotificationManager()
