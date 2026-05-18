from PySide6.QtCore import QObject, QTimer

from api_client import api_client
from core.notification_manager import notification_manager


class AlertService(QObject):
    """Servico leve para sincronizar alertas administrativos com o backend."""

    def __init__(self):
        super().__init__()
        self._timer = None

    def iniciar(self):
        """Inicia a sincronizacao periodica dos alertas."""
        if self._timer is not None and self._timer.isActive():
            return

        self._timer = QTimer(self)
        self._timer.timeout.connect(self.verificar_todos_alertas)
        self._timer.start(300000)
        print("Servico de alertas iniciado")

        QTimer.singleShot(1200, self.verificar_todos_alertas)

    def parar(self):
        """Para a sincronizacao periodica."""
        if self._timer:
            self._timer.stop()
            self._timer = None
        print("Servico de alertas parado")

    def verificar_todos_alertas(self):
        """Solicita ao backend a materializacao dos alertas do usuario atual."""
        try:
            import requests

            response = requests.post(
                f"{api_client.base_url}/api/notificacoes/sincronizar-alertas",
                headers=api_client.get_headers(),
                timeout=30,
            )
            if response.status_code == 200:
                payload = response.json()
                created = int(payload.get("created", 0) or 0)
                if created > 0:
                    print(f"Alertas sincronizados: {created} nova(s) notificacao(oes)")
                notification_manager.verificar_novas_notificacoes()
            else:
                print(f"Erro ao sincronizar alertas: HTTP {response.status_code} - {response.text}")
        except Exception as e:
            print(f"Erro ao sincronizar alertas: {e}")


alert_service = AlertService()
