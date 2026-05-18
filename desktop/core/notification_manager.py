from datetime import datetime

from PySide6.QtCore import QObject, QTimer, Signal
from PySide6.QtWidgets import QApplication

from api_client import api_client


class NotificationManager(QObject):
    """Gerenciador central de notificacoes do desktop."""

    nova_notificacao = Signal(dict)
    notificacoes_atualizadas = Signal()
    contador_atualizado = Signal(int)

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        super().__init__()
        self._initialized = True
        self._ultimas_notificacoes = []
        self._ultimo_contador = 0
        self._timer_verificacao = None
        self._modo_nao_perturbe = False
        self._horario_nao_perturbe = {"ativo": False, "inicio": "22:00", "fim": "06:00"}
        self._parent = None

        self.carregar_configuracoes()
        self.iniciar_verificacao_periodica()

    def set_parent(self, parent):
        """Define a janela principal para exibir toasts."""
        self._parent = parent
        try:
            from widgets.toast_notification import notification_manager as toast_manager

            toast_manager.set_parent(parent)
        except Exception as e:
            print(f"Erro ao vincular parent do toast manager: {e}")

    def carregar_configuracoes(self):
        """Carrega as configuracoes de notificacao do backend."""
        try:
            config = api_client.get_configuracoes()
            if config:
                self._modo_nao_perturbe = config.get("modo_nao_perturbe", False)
                self._horario_nao_perturbe = {
                    "ativo": config.get("nao_perturbe_ativo", False),
                    "inicio": config.get("nao_perturbe_inicio", "22:00"),
                    "fim": config.get("nao_perturbe_fim", "06:00"),
                }
        except Exception as e:
            print(f"Erro ao carregar configuracoes: {e}")

    def iniciar_verificacao_periodica(self):
        """Inicia a verificacao periodica de novas notificacoes."""
        if QApplication.instance() is None:
            return False

        if self._timer_verificacao is None:
            self._timer_verificacao = QTimer(self)
            self._timer_verificacao.timeout.connect(self.verificar_novas_notificacoes)

        if not self._timer_verificacao.isActive():
            self._timer_verificacao.start(30000)

        return True

    def verificar_novas_notificacoes(self):
        """Verifica se ha novas notificacoes no backend."""
        try:
            count = api_client.contar_notificacoes_nao_lidas()

            if count != self._ultimo_contador:
                self._ultimo_contador = count
                self.contador_atualizado.emit(count)

                if count > 0:
                    self.buscar_novas_notificacoes()
        except Exception as e:
            print(f"Erro ao verificar notificacoes: {e}")

    def buscar_novas_notificacoes(self):
        """Busca as notificacoes nao lidas do backend."""
        try:
            notificacoes = api_client.listar_notificacoes(status="nao_lida", limit=20)
            ids_anteriores = [n.get("id") for n in self._ultimas_notificacoes]

            for notif in notificacoes:
                if notif.get("id") not in ids_anteriores:
                    self._ultimas_notificacoes.insert(0, notif)
                    self.nova_notificacao.emit(notif)
                    self._mostrar_toast_notificacao(notif)

            self._ultimas_notificacoes = self._ultimas_notificacoes[:50]
            self.notificacoes_atualizadas.emit()
        except Exception as e:
            print(f"Erro ao buscar notificacoes: {e}")

    def _mostrar_toast_notificacao(self, notificacao):
        prioridade = notificacao.get("prioridade", "baixa")
        if not self.deve_mostrar_notificacao(prioridade):
            return

        try:
            from widgets.toast_notification import notification_manager as toast_manager

            parent_window = self._parent or QApplication.activeWindow()
            mensagem = notificacao.get("mensagem") or notificacao.get("titulo") or "Nova notificacao"
            duracao = {"alta": 10000, "media": 7000, "baixa": 5000}.get(prioridade, 5000)

            toast_manager.show(
                message=mensagem,
                tipo="warning" if prioridade in ["alta", "media"] else "info",
                duration=duracao,
                parent=parent_window,
                prioridade=prioridade,
                acao=notificacao.get("acao"),
                acao_id=notificacao.get("acao_id"),
                notificacao_id=notificacao.get("id"),
                title=notificacao.get("titulo"),
            )
        except Exception as e:
            print(f"Erro ao exibir toast de notificacao: {e}")

    def deve_mostrar_notificacao(self, prioridade):
        """Verifica se a notificacao deve ser mostrada."""
        if not self._modo_nao_perturbe:
            return True

        if prioridade == "alta":
            return True

        agora = datetime.now().strftime("%H:%M")
        inicio = self._horario_nao_perturbe.get("inicio", "22:00")
        fim = self._horario_nao_perturbe.get("fim", "06:00")

        if inicio < fim:
            return not (inicio <= agora < fim)
        return not (agora >= inicio or agora < fim)

    def criar_notificacao(self, tipo, titulo, mensagem, prioridade, acao=None, acao_id=None, dados_extra=None):
        """Cria uma nova notificacao apenas no backend."""
        try:
            if self._verificar_cooldown(tipo):
                return None

            payload = {
                "tipo": tipo,
                "titulo": titulo,
                "mensagem": mensagem,
                "prioridade": prioridade,
                "acao": acao,
                "acao_id": acao_id,
                "dados_extra": dados_extra,
            }

            response = api_client.criar_notificacao_backend(payload)
            if response:
                self._registrar_envio(tipo)
                return response
        except Exception as e:
            print(f"Erro ao criar notificacao: {e}")
        return None

    def criar_notificacao_sistema(self, tipo, titulo, mensagem, prioridade, acao=None, acao_id=None, dados_extra=None):
        """Cria uma notificacao no backend e exibe o toast."""
        if self._verificar_cooldown(tipo):
            print(f"Notificacao {tipo} em cooldown, ignorando...")
            return None

        payload = {
            "tipo": tipo,
            "titulo": titulo,
            "mensagem": mensagem,
            "prioridade": prioridade,
            "acao": acao,
            "acao_id": acao_id,
            "dados_extra": dados_extra,
        }

        try:
            result = api_client.criar_notificacao_backend(payload)
            if result:
                self._registrar_envio(tipo)

                if self.deve_mostrar_notificacao(prioridade):
                    from widgets.toast_notification import notification_manager as toast_manager

                    parent_window = self._parent or QApplication.activeWindow()
                    duracao = {"alta": 10000, "media": 7000, "baixa": 5000}.get(prioridade, 5000)

                    toast_manager.show(
                        message=mensagem,
                        tipo="warning" if prioridade in ["alta", "media"] else "info",
                        duration=duracao,
                        parent=parent_window,
                        prioridade=prioridade,
                        acao=acao,
                        acao_id=acao_id,
                        notificacao_id=result.get("id") if result else None,
                        title=titulo,
                    )

                return result
        except Exception as e:
            print(f"Erro ao criar notificacao do sistema: {e}")
        return None

    def _verificar_cooldown(self, tipo):
        """Verifica se a notificacao esta em periodo de cooldown."""
        cooldowns = {
            "estoque_critico": 1800,
            "estoque_baixo": 3600,
            "manutencao": 3600,
            "pedido": 7200,
            "demanda": 3600,
            "backup": 86400,
        }

        cooldown = cooldowns.get(tipo, 300)
        ultimo_envio = getattr(self, f"_ultimo_envio_{tipo}", None)
        if ultimo_envio:
            segundos_passados = (datetime.now() - ultimo_envio).total_seconds()
            if segundos_passados < cooldown:
                print(f"Cooldown ativo para {tipo}: {segundos_passados:.0f}s restantes de {cooldown}s")
                return True
        return False

    def _registrar_envio(self, tipo):
        """Registra o timestamp do ultimo envio."""
        agora = datetime.now()
        setattr(self, f"_ultimo_envio_{tipo}", agora)
        print(f"Registrado envio para {tipo} em {agora}")

    def marcar_como_lida(self, notificacao_id):
        """Marca uma notificacao como lida."""
        success = api_client.marcar_notificacao_lida(notificacao_id)
        if success:
            self.verificar_novas_notificacoes()
        return success

    def marcar_todas_como_lidas(self):
        """Marca todas as notificacoes como lidas."""
        success = api_client.marcar_todas_notificacoes_lidas()
        if success:
            self._ultimo_contador = 0
            self.contador_atualizado.emit(0)
            self.verificar_novas_notificacoes()
        return success

    def get_notificacoes(self, status=None, prioridade=None, limit=50):
        """Retorna a lista de notificacoes."""
        return api_client.listar_notificacoes(status=status, prioridade=prioridade, limit=limit)

    def get_contador_nao_lidas(self):
        """Retorna o contador atual de notificacoes nao lidas."""
        return self._ultimo_contador

    def atualizar_contador(self):
        """Forca a atualizacao do contador."""
        self._ultimo_contador = api_client.contar_notificacoes_nao_lidas()
        self.contador_atualizado.emit(self._ultimo_contador)
        print(f"Contador atualizado: {self._ultimo_contador} notificacoes nao lidas")
        return self._ultimo_contador


notification_manager = NotificationManager()
