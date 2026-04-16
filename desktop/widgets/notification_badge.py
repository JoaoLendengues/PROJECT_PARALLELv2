from PySide6.QtWidgets import QPushButton, QHBoxLayout, QWidget
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont

class NotificationBadge(QPushButton):
    """Botão de notificações com badge no sidebar"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._contador = 0
        self._timer = None
        self.setup_ui()
        self.iniciar_atualizacao_periodica()

    def setup_ui(self):
        """Configura a inteface do botão"""
        self.setText('🔔 Notificações')
        self.setProperty('class', 'menu-button')
        self.setFixedHeight(48)
        self.setCursor(Qt.PointingHandCursor)

        # Estilo do badge
        self.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding-left: 16px;
            }
        """)

    def set_contador(self, count):
        """Atualiza o badge com o número de notificações não lidas"""
        self._contador = count

        if count > 0:
            self.setText(f'🔔🔴 Notificações [{count}]')
            self.setToolTip(f'Você tem {count} notificação(ões) não lida(s)')
        else:
            self.setText('🔔 Notificações')
            self.setToolTip('Nenhuma notificação não lida')

    def get_contador(self):
        return self._contador
    
    def iniciar_atualizacao_periodica(self):
        """Inicia a atualização periódica do contador"""
        self._timer = QTimer()
        self._timer.timeout.connect(self.atualizar_contador)
        self._timer.start(30000) # 30 segundos

    def atualizar_contador(self):
        """Atualiza o contador de notificações não lidas"""
        try:
            from api_client import api_client
            count = api_client.contar_notificacoes_nao_lidas()
            self.set_contador(count)
        except Exception as e:
            print(f'Erro ao atualizar contador: {e}')

    def force_update(self):
        """Força a atualização do contador"""
        self.atualizar_contador()


         