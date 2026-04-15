import threading
from datetime import datetime
from PySide6.QtCore import QObject, Signal, QTimer
from api_client import api_client


class NotificationManager(QObject):
    """Gerenciador central de notificações - Singleton"""
    
    # Sinais para comunicação com a UI
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
        
        # Carregar configurações
        self.carregar_configuracoes()
        
        # Iniciar timer de verificação (a cada 30 segundos)
        self.iniciar_verificacao_periodica()
    
    def carregar_configuracoes(self):
        """Carrega as configurações de notificação do backend"""
        try:
            config = api_client.get_configuracoes()
            if config:
                self._modo_nao_perturbe = config.get("modo_nao_perturbe", False)
                self._horario_nao_perturbe = {
                    "ativo": config.get("nao_perturbe_ativo", False),
                    "inicio": config.get("nao_perturbe_inicio", "22:00"),
                    "fim": config.get("nao_perturbe_fim", "06:00")
                }
        except Exception as e:
            print(f"Erro ao carregar configurações: {e}")
    
    def iniciar_verificacao_periodica(self):
        """Inicia a verificação periódica de novas notificações"""
        self._timer_verificacao = QTimer()
        self._timer_verificacao.timeout.connect(self.verificar_novas_notificacoes)
        self._timer_verificacao.start(30000)  # 30 segundos
    
    def verificar_novas_notificacoes(self):
        """Verifica se há novas notificações no backend"""
        try:
            # Verificar contador de não lidas
            count = api_client.contar_notificacoes_nao_lidas()
            
            if count != self._ultimo_contador:
                self._ultimo_contador = count
                self.contador_atualizado.emit(count)
                
                # Buscar novas notificações
                if count > 0:
                    self.buscar_novas_notificacoes()
                    
        except Exception as e:
            print(f"Erro ao verificar notificações: {e}")
    
    def buscar_novas_notificacoes(self):
        """Busca as notificações não lidas do backend"""
        try:
            notificacoes = api_client.listar_notificacoes(status="nao_lida", limit=20)
            
            # Verificar notificações novas (que não estavam na lista anterior)
            ids_anteriores = [n.get("id") for n in self._ultimas_notificacoes]
            
            for notif in notificacoes:
                if notif.get("id") not in ids_anteriores:
                    self._ultimas_notificacoes.insert(0, notif)
                    # Emitir sinal para mostrar notificação
                    self.nova_notificacao.emit(notif)
                    
            # Manter apenas as últimas 50
            self._ultimas_notificacoes = self._ultimas_notificacoes[:50]
            self.notificacoes_atualizadas.emit()
            
        except Exception as e:
            print(f"Erro ao buscar notificações: {e}")
    
    def deve_mostrar_notificacao(self, prioridade):
        """Verifica se a notificação deve ser mostrada (respeitando modo não perturbe)"""
        if not self._modo_nao_perturbe:
            return True
        
        if prioridade == "alta":
            return True  # Notificações altas sempre são mostradas
        
        # Verificar horário atual
        from datetime import datetime
        agora = datetime.now().strftime("%H:%M")
        
        inicio = self._horario_nao_perturbe.get("inicio", "22:00")
        fim = self._horario_nao_perturbe.get("fim", "06:00")
        
        if inicio < fim:
            # Ex: 22:00 - 06:00
            return not (inicio <= agora < fim)
        else:
            # Ex: 22:00 - 06:00 (passando da meia-noite)
            return not (agora >= inicio or agora < fim)
    
    def criar_notificacao(self, tipo, titulo, mensagem, prioridade, acao=None, acao_id=None, dados_extra=None):
        """Cria uma nova notificação no backend"""
        try:
            # Verificar se é uma notificação que precisa de cooldown
            if self._verificar_cooldown(tipo):
                return None
            
            payload = {
                "tipo": tipo,
                "titulo": titulo,
                "mensagem": mensagem,
                "prioridade": prioridade,
                "acao": acao,
                "acao_id": acao_id,
                "dados_extra": dados_extra
            }
            
            # Chamar API para criar notificação
            # Nota: O backend vai pegar o usuario_id do token
            response = api_client.criar_notificacao_backend(payload)
            
            if response:
                # Registrar timestamp do último envio para cooldown
                self._registrar_envio(tipo)
                return response
                
        except Exception as e:
            print(f"Erro ao criar notificação: {e}")
        
        return None
    
    def _verificar_cooldown(self, tipo):
        """Verifica se a notificação está em período de cooldown"""
        cooldowns = {
            "estoque_critico": 1800,   # 30 minutos
            "estoque_baixo": 3600,      # 1 hora
            "manutencao": 3600,         # 1 hora
            "pedido": 7200,             # 2 horas
            "demanda": 3600,            # 1 hora
            "backup": 86400,            # 1 dia
        }
        
        cooldown = cooldowns.get(tipo, 300)  # 5 minutos padrão
        
        # Verificar último envio
        ultimo_envio = getattr(self, f"_ultimo_envio_{tipo}", None)
        if ultimo_envio:
            from datetime import datetime
            segundos_passados = (datetime.now() - ultimo_envio).total_seconds()
            if segundos_passados < cooldown:
                return True
        
        return False
    
    def _registrar_envio(self, tipo):
        """Registra o timestamp do último envio"""
        from datetime import datetime
        setattr(self, f"_ultimo_envio_{tipo}", datetime.now())
    
    def marcar_como_lida(self, notificacao_id):
        """Marca uma notificação como lida"""
        success = api_client.marcar_notificacao_lida(notificacao_id)
        if success:
            self.verificar_novas_notificacoes()
        return success
    
    def marcar_todas_como_lidas(self):
        """Marca todas as notificações como lidas"""
        success = api_client.marcar_todas_notificacoes_lidas()
        if success:
            self._ultimo_contador = 0
            self.contador_atualizado.emit(0)
            self.verificar_novas_notificacoes()
        return success
    
    def get_notificacoes(self, status=None, prioridade=None, limit=50):
        """Retorna a lista de notificações"""
        return api_client.listar_notificacoes(status=status, prioridade=prioridade, limit=limit)
    
    def get_contador_nao_lidas(self):
        """Retorna o contador atual de notificações não lidas"""
        return self._ultimo_contador
    
    def atualizar_contador(self):
        """Força a atualização do contador"""
        self._ultimo_contador = api_client.contar_notificacoes_nao_lidas()
        self.contador_atualizado.emit(self._ultimo_contador)
        return self._ultimo_contador


# Instância global
notification_manager = NotificationManager()
