from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer
from PySide6.QtGui import QFont, QColor, QPalette


class ToastNotification(QFrame):
    """Notificação estilo Toast (pop-up no canto da tela) - Versão melhorada"""
    
    def __init__(self, message, tipo="info", parent=None, duration=5000):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_DeleteOnClose)
        
        # Cores e ícones por tipo (mais vibrantes)
        cores = {
            "info": {"bg": "#2196F3", "bg_hover": "#1976D2", "icon": "ℹ️", "titulo": "INFORMAÇÃO"},
            "success": {"bg": "#4CAF50", "bg_hover": "#388E3C", "icon": "✅", "titulo": "SUCESSO"},
            "warning": {"bg": "#FF9800", "bg_hover": "#F57C00", "icon": "⚠️", "titulo": "ATENÇÃO"},
            "error": {"bg": "#f44336", "bg_hover": "#D32F2F", "icon": "❌", "titulo": "ERRO"}
        }
        
        cor = cores.get(tipo, cores["info"])
        
        # Estilo do frame (mais destacado)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {cor['bg']};
                border-radius: 12px;
                border: 2px solid white;
            }}
            QFrame:hover {{
                background-color: {cor['bg_hover']};
            }}
            QLabel {{
                color: white;
                background-color: transparent;
                border: none;
            }}
            QPushButton {{
                background-color: transparent;
                color: white;
                border: none;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: rgba(255, 255, 255, 0.2);
                border-radius: 10px;
            }}
        """)
        
        # Layout principal
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Frame interno para o conteúdo
        content_frame = QFrame()
        content_frame.setStyleSheet("background-color: transparent;")
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(15, 12, 15, 12)
        content_layout.setSpacing(5)
        
        # Cabeçalho (ícone + título)
        header_layout = QHBoxLayout()
        
        # Ícone grande
        icon_label = QLabel(cor["icon"])
        icon_label.setFont(QFont("Segoe UI", 20))
        header_layout.addWidget(icon_label)
        
        # Título
        title_label = QLabel(cor["titulo"])
        title_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        title_label.setStyleSheet("letter-spacing: 1px;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Botão fechar
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(24, 24)
        close_btn.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        close_btn.clicked.connect(self.fechar)
        header_layout.addWidget(close_btn)
        
        content_layout.addLayout(header_layout)
        
        # Linha separadora
        linha = QFrame()
        linha.setFrameShape(QFrame.HLine)
        linha.setStyleSheet("background-color: rgba(255,255,255,0.3); max-height: 1px;")
        content_layout.addWidget(linha)
        
        # Mensagem
        self.message_label = QLabel(message)
        self.message_label.setFont(QFont("Segoe UI", 11))
        self.message_label.setWordWrap(True)
        self.message_label.setMinimumWidth(250)
        self.message_label.setMaximumWidth(350)
        content_layout.addWidget(self.message_label)
        
        main_layout.addWidget(content_frame)
        
        # Ajustar tamanho
        self.adjustSize()
        
        # Posicionar no canto inferior direito
        self.posicionar()
        
        # Mostrar com animação
        self.show()
        
        # Animação de entrada (fade in + slide)
        self.setWindowOpacity(0)
        self.anim_entrada = QPropertyAnimation(self, b"windowOpacity")
        self.anim_entrada.setDuration(300)
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
        """Posiciona a notificação no canto inferior direito"""
        if self.parent():
            parent_rect = self.parent().rect()
            x = parent_rect.width() - self.width() - 20
            y = parent_rect.height() - self.height() - 80  # 80px acima do canto
            self.move(x, y)
        else:
            # Fallback: posicionar na tela
            screen = self.screen().availableGeometry()
            x = screen.width() - self.width() - 20
            y = screen.height() - self.height() - 80
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
        """Fecha a notificação imediatamente"""
        self.hide()
        self.deleteLater()


class NotificationManager:
    """Gerenciador de notificações do sistema"""
    
    _instance = None
    _notifications = []
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def show(self, message, tipo="info", duration=5000, parent=None):
        """Exibe uma notificação"""
        toast = ToastNotification(message, tipo, parent, duration)
        self._notifications.append(toast)
        
        # Remover da lista quando fechar
        toast.destroyed.connect(lambda: self._notifications.remove(toast))
        
        return toast
    
    def success(self, message, parent=None, duration=4000):
        """Notificação de sucesso"""
        return self.show(message, "success", duration, parent)
    
    def warning(self, message, parent=None, duration=5000):
        """Notificação de aviso"""
        return self.show(message, "warning", duration, parent)
    
    def error(self, message, parent=None, duration=6000):
        """Notificação de erro"""
        return self.show(message, "error", duration, parent)
    
    def info(self, message, parent=None, duration=4000):
        """Notificação informativa"""
        return self.show(message, "info", duration, parent)


# Instância global
notification_manager = NotificationManager()
