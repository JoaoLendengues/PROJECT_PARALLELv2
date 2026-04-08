from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer
from PySide6.QtGui import QFont


class ToastNotification(QFrame):
    """Notificação estilo Toast (pop-up no canto da tela)"""
    
    def __init__(self, message, tipo="info", parent=None, duration=5000):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Cores por tipo
        cores = {
            "info": {"bg": "#2c7da0", "icon": "ℹ️"},
            "success": {"bg": "#2a9d8f", "icon": "✅"},
            "warning": {"bg": "#f4a261", "icon": "⚠️"},
            "error": {"bg": "#e76f51", "icon": "❌"}
        }
        
        cor = cores.get(tipo, cores["info"])
        
        # Estilo do frame
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {cor['bg']};
                border-radius: 10px;
                border: none;
            }}
            QLabel {{
                color: white;
                background-color: transparent;
                border: none;
            }}
        """)
        
        # Layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(10)
        
        # Ícone
        icon_label = QLabel(cor["icon"])
        icon_label.setFont(QFont("Segoe UI", 16))
        layout.addWidget(icon_label)
        
        # Mensagem
        self.message_label = QLabel(message)
        self.message_label.setFont(QFont("Segoe UI", 11))
        self.message_label.setWordWrap(True)
        layout.addWidget(self.message_label)
        
        # Botão fechar
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(20, 20)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: white;
                border: none;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.2);
                border-radius: 10px;
            }
        """)
        close_btn.clicked.connect(self.fechar)
        layout.addWidget(close_btn)
        
        # Ajustar tamanho
        self.adjustSize()
        
        # Posicionar no canto inferior direito
        self.posicionar()
        
        # Animação de entrada
        self.anim_entrada = QPropertyAnimation(self, b"windowOpacity")
        self.anim_entrada.setDuration(300)
        self.anim_entrada.setStartValue(0)
        self.anim_entrada.setEndValue(1)
        self.anim_entrada.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.anim_entrada.start()
        
        # Auto-fechar
        if duration > 0:
            QTimer.singleShot(duration, self.fechar_animado)
    
    def posicionar(self):
        """Posiciona a notificação no canto inferior direito"""
        if self.parent():
            parent_rect = self.parent().rect()
            x = parent_rect.width() - self.width() - 20
            y = parent_rect.height() - self.height() - 20
            self.move(x, y)
    
    def fechar_animado(self):
        """Fecha com animação de fade out"""
        self.anim_saida = QPropertyAnimation(self, b"windowOpacity")
        self.anim_saida.setDuration(300)
        self.anim_saida.setStartValue(1)
        self.anim_saida.setEndValue(0)
        self.anim_saida.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.anim_saida.finished.connect(self.close)
        self.anim_saida.start()
    
    def fechar(self):
        self.close()


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
        toast.show()
        self._notifications.append(toast)
        
        # Remover da lista quando fechar
        toast.destroyed.connect(lambda: self._notifications.remove(toast))
        
        return toast
    
    def success(self, message, parent=None, duration=3000):
        """Notificação de sucesso"""
        return self.show(message, "success", duration, parent)
    
    def warning(self, message, parent=None, duration=4000):
        """Notificação de aviso"""
        return self.show(message, "warning", duration, parent)
    
    def error(self, message, parent=None, duration=5000):
        """Notificação de erro"""
        return self.show(message, "error", duration, parent)
    
    def info(self, message, parent=None, duration=3000):
        """Notificação informativa"""
        return self.show(message, "info", duration, parent)


# Instância global
notification_manager = NotificationManager()
