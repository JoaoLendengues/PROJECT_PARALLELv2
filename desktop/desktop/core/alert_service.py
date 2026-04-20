from PySide6.QtCore import QObject, QTimer, Signal
from datetime import datetime, timedelta
from api_client import api_client
from core.notification_manager import notification_manager


class AlertService(QObject):
    """Serviço para verificar alertas do sistema periodicamente"""
    
    def __init__(self):
        super().__init__()
        self._timer = None
        self._configuracoes = {}
        self._ultimos_alertas = {}  # Para evitar duplicatas
        self._carregar_configuracoes()
    
    def _carregar_configuracoes(self):
        """Carrega as configurações de alertas"""
        try:
            config = api_client.get_configuracoes()
            self._configuracoes = {
                "alerta_estoque": int(config.get("alerta_estoque", 5)),
                "alerta_estoque_critico": int(config.get("alerta_estoque_critico", 2)),
                "notif_estoque_baixo": config.get("notif_estoque_baixo", True) == True or config.get("notif_estoque_baixo") == "true",
                "notif_estoque_critico": config.get("notif_estoque_critico", True) == True or config.get("notif_estoque_critico") == "true",
                "notif_manutencao": config.get("notif_manutencao", True) == True or config.get("notif_manutencao") == "true",
                "notif_pedidos": config.get("notif_pedidos", True) == True or config.get("notif_pedidos") == "true",
                "notif_demandas": config.get("notif_demandas", True) == True or config.get("notif_demandas") == "true"
            }
        except Exception as e:
            print(f"Erro ao carregar configurações: {e}")
    
    def iniciar(self):
        """Inicia a verificação periódica de alertas"""
        self._timer = QTimer()
        self._timer.timeout.connect(self.verificar_todos_alertas)
        
        # Verificar a cada 5 minutos (ou conforme configuração)
        intervalo = 300000  # 5 minutos em ms
        self._timer.start(intervalo)
        print("✅ Serviço de alertas iniciado")
        
        # Executar primeira verificação imediatamente
        self.verificar_todos_alertas()
    
    def parar(self):
        """Para a verificação periódica"""
        if self._timer:
            self._timer.stop()
            self._timer = None
        print("⏸️ Serviço de alertas parado")
    
    def verificar_todos_alertas(self):
        """Verifica todos os tipos de alerta"""
        self._carregar_configuracoes()
        
        self.verificar_estoque()
        self.verificar_manutencoes()
        self.verificar_pedidos()
        self.verificar_demandas()
    
    def verificar_estoque(self):
        """Verifica materiais com estoque baixo ou crítico"""
        try:
            materiais = api_client.listar_materiais()
            
            for material in materiais:
                material_id = material.get("id")
                nome = material.get("nome", "Material")
                quantidade = material.get("quantidade", 0)
                
                # Chave única para evitar duplicatas
                chave = f"estoque_{material_id}"
                
                # Verificar estoque crítico (prioridade alta)
                if self._configuracoes.get("notif_estoque_critico", True):
                    limite_critico = self._configuracoes.get("alerta_estoque_critico", 2)
                    if quantidade <= limite_critico and quantidade > 0:
                        self._criar_alerta_estoque(
                            material_id, nome, quantidade, limite_critico, 
                            "critico", chave
                        )
                        continue  # Se já é crítico, não precisa verificar baixo
                
                # Verificar estoque baixo (prioridade média)
                if self._configuracoes.get("notif_estoque_baixo", True):
                    limite_baixo = self._configuracoes.get("alerta_estoque", 5)
                    if quantidade <= limite_baixo and quantidade > 0:
                        self._criar_alerta_estoque(
                            material_id, nome, quantidade, limite_baixo, 
                            "baixo", chave
                        )
                        
        except Exception as e:
            print(f"Erro ao verificar estoque: {e}")
    
    def _criar_alerta_estoque(self, material_id, nome, quantidade, limite, tipo, chave):
        """Cria notificação de alerta de estoque"""
        
        # Verificar cooldown (30 minutos para crítico, 1 hora para baixo)
        cooldown = 1800 if tipo == "critico" else 3600
        if self._verificar_cooldown(chave, cooldown):
            return
        
        if tipo == "critico":
            titulo = "🔴 ESTOQUE CRÍTICO!"
            mensagem = f"📦 {nome}\nApenas {quantidade} unidades restantes!\nLimite crítico: {limite} unidades"
            prioridade = "alta"
            acao = "show_materiais"
        else:
            titulo = "⚠️ ESTOQUE BAIXO"
            mensagem = f"📦 {nome}\nEstoque: {quantidade} unidades\nLimite de alerta: {limite} unidades"
            prioridade = "media"
            acao = "show_materiais"
        
        # Criar notificação no sistema
        notification_manager.criar_notificacao_sistema(
            tipo=f"estoque_{tipo}",
            titulo=titulo,
            mensagem=mensagem,
            prioridade=prioridade,
            acao=acao,
            acao_id=material_id,
            dados_extra={"quantidade": quantidade, "limite": limite}
        )
        
        # Registrar timestamp
        self._registrar_alerta(chave)
    
    def verificar_manutencoes(self):
        """Verifica manutenções pendentes"""
        try:
            if not self._configuracoes.get("notif_manutencao", True):
                return
            
            manutencoes = api_client.listar_manutencoes(status="pendente")
            
            for manut in manutencoes:
                manut_id = manut.get("id")
                maquina_nome = manut.get("maquina_nome", "Máquina")
                data_inicio = manut.get("data_inicio", "")
                descricao = manut.get("descricao", "")[:50]
                
                chave = f"manutencao_{manut_id}"
                
                # Verificar cooldown (1 hora)
                if self._verificar_cooldown(chave, 3600):
                    continue
                
                # Calcular dias pendente
                dias_pendente = 0
                if data_inicio:
                    try:
                        data_inicio_obj = datetime.strptime(data_inicio, "%Y-%m-%d")
                        dias_pendente = (datetime.now() - data_inicio_obj).days
                    except:
                        pass
                
                prioridade = "alta" if dias_pendente > 7 else "media"
                
                titulo = "🔧 MANUTENÇÃO PENDENTE!"
                mensagem = f"🖥️ {maquina_nome}\n"
                if dias_pendente > 0:
                    mensagem += f"Pendente há {dias_pendente} dia(s)\n"
                mensagem += f"Descrição: {descricao}"
                
                notification_manager.criar_notificacao_sistema(
                    tipo="manutencao",
                    titulo=titulo,
                    mensagem=mensagem,
                    prioridade=prioridade,
                    acao="show_manutencoes",
                    acao_id=manut_id,
                    dados_extra={"dias_pendente": dias_pendente}
                )
                
                self._registrar_alerta(chave)
                
        except Exception as e:
            print(f"Erro ao verificar manutenções: {e}")
    
    def verificar_pedidos(self):
        """Verifica pedidos pendentes"""
        try:
            if not self._configuracoes.get("notif_pedidos", True):
                return
            
            pedidos = api_client.listar_pedidos(status="pendente")
            
            for pedido in pedidos:
                pedido_id = pedido.get("id")
                material_nome = pedido.get("material_nome", "Material")
                quantidade = pedido.get("quantidade", 0)
                solicitante = pedido.get("solicitante", "")
                data_solicitacao = pedido.get("data_solicitacao", "")
                
                chave = f"pedido_{pedido_id}"
                
                # Verificar cooldown (2 horas)
                if self._verificar_cooldown(chave, 7200):
                    continue
                
                # Calcular dias desde solicitação
                dias_atraso = 0
                if data_solicitacao:
                    try:
                        data_solic_obj = datetime.strptime(data_solicitacao, "%Y-%m-%d")
                        dias_atraso = (datetime.now() - data_solic_obj).days
                    except:
                        pass
                
                prioridade = "alta" if dias_atraso > 3 else "media"
                
                titulo = "📋 PEDIDO PENDENTE!"
                mensagem = f"📦 {material_nome}\nQuantidade: {quantidade}\nSolicitante: {solicitante}"
                if dias_atraso > 0:
                    mensagem += f"\nAguardando há {dias_atraso} dia(s)"
                
                notification_manager.criar_notificacao_sistema(
                    tipo="pedido",
                    titulo=titulo,
                    mensagem=mensagem,
                    prioridade=prioridade,
                    acao="show_pedidos",
                    acao_id=pedido_id,
                    dados_extra={"dias_atraso": dias_atraso}
                )
                
                self._registrar_alerta(chave)
                
        except Exception as e:
            print(f"Erro ao verificar pedidos: {e}")
    
    def verificar_demandas(self):
        """Verifica demandas abertas"""
        try:
            if not self._configuracoes.get("notif_demandas", True):
                return
            
            demandas = api_client.listar_demandas(status="aberto")
            
            for demanda in demandas:
                demanda_id = demanda.get("id")
                titulo = demanda.get("titulo", "")
                solicitante = demanda.get("solicitante", "")
                prioridade_demanda = demanda.get("prioridade", "media")
                data_abertura = demanda.get("data_abertura", "")
                
                chave = f"demanda_{demanda_id}"
                
                # Verificar cooldown (1 hora)
                if self._verificar_cooldown(chave, 3600):
                    continue
                
                # Mapear prioridade da demanda para prioridade da notificação
                if prioridade_demanda == "alta":
                    prioridade_notif = "alta"
                elif prioridade_demanda == "media":
                    prioridade_notif = "media"
                else:
                    prioridade_notif = "baixa"
                
                titulo_notif = f"🎫 NOVA DEMANDA {prioridade_demanda.upper()}!"
                mensagem = f"Título: {titulo[:50]}\nSolicitante: {solicitante}"
                
                notification_manager.criar_notificacao_sistema(
                    tipo="demanda",
                    titulo=titulo_notif,
                    mensagem=mensagem,
                    prioridade=prioridade_notif,
                    acao="show_demandas",
                    acao_id=demanda_id,
                    dados_extra={"prioridade": prioridade_demanda}
                )
                
                self._registrar_alerta(chave)
                
        except Exception as e:
            print(f"Erro ao verificar demandas: {e}")
    
    def _verificar_cooldown(self, chave, segundos):
        """Verifica se o alerta ainda está em período de cooldown"""
        if chave in self._ultimos_alertas:
            tempo_passado = (datetime.now() - self._ultimos_alertas[chave]).total_seconds()
            if tempo_passado < segundos:
                return True
        return False
    
    def _registrar_alerta(self, chave):
        """Registra o timestamp do alerta para cooldown"""
        self._ultimos_alertas[chave] = datetime.now()


# Instância global
alert_service = AlertService()
