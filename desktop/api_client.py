import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv('API_URL', 'http://localhost:8000')

class APIClient:
    """Cliente para comunicação com a API do Project Parallel"""

    def __init__(self):
        self.base_url = API_URL
        self.token = None

    def set_token(self, token):
        """Define o token de autenticação"""
        self.token = token

    def get_headers(self):
        """retorna os headers para as requisições"""
        headers = {'Content-Type': 'application/json'}
        if self.token:
            headers['authorization'] = f'Bearer {self.token}'
        return headers
    
    # =====================================================
    # Autenticação
    # =====================================================

    def login(self, codigo, senha):
        """Realiza login e armazena o token"""
        response = requests.post(
            f"{self.base_url}/api/auth/login",
            json={"codigo": codigo, "senha": senha},
            headers={"Content-Type": "application/json"}
    )
    
        if response.status_code == 200:
            data = response.json()
            self.set_token(data["access_token"])
            return {"success": True, "usuario": data["usuario"]}
        else:
            # Tentar extrair mensagem de erro corretamente
            try:
                error_data = response.json()
                if "detail" in error_data:
                    error_msg = error_data["detail"]
                else:
                    error_msg = str(error_data)
            except:
                error_msg = response.text if response.text else "Erro no login"
        
        return {"success": False, "error": error_msg}
        
    def trocar_senha(self, codigo, senha_atual, nova_senha):
        """Troca a senha do usuário"""
        response = requests.post(
            f'{self.base_url}/api/auth/trocar-senha',
            json={'codigo': codigo, 'senha_atual': senha_atual, 'nova_senha': nova_senha},
            headers={'Content-Type': 'application/json'}
        )
        return response.status_code == 200
    
    # =====================================================
    # Materiais
    # =====================================================

    def listar_materiais(self,search=None, categoria=None, empresa=None, status=None):
        """Lista materiais com filtros"""
        params = {'status': status}
        if search:
            params['search'] = search
        if categoria:
            params['categoria'] = categoria
        if empresa:
            params['empresa'] = empresa

        if status:
            params['status'] = status
            
        response = requests.get(
            f'{self.base_url}/api/materiais',
            headers=self.get_headers(),
            params=params
        )
        return response.json() if response.status_code == 200 else []
    
    def criar_material(self, material):
        """Cria um novo material"""
        response = requests.post(
            f"{self.base_url}/api/materiais",
            json=material,
            headers=self.get_headers()
        )
        # Verificar se foi criado com sucesso (status 201)
        if response.status_code == 201:
            return response.json()  # Retorna o material criado
        else:
            print(f"Erro ao criar material: {response.status_code} - {response.text}")
            return None
    
    def atualizar_material(self, material_id, material):
        """Atualiza um material"""
        response = requests.put(
            f'{self.base_url}/api/materiais/{material_id}',
            json=material,
            headers=self.get_headers()
        )
        return response.json() if response.status_code == 200 else None

    def deletar_material(self, material_id):
        """Deleta um material"""
        response = requests.delete(
            f'{self.base_url}/api/materiais/{material_id}',
            headers=self.get_headers()
        )
        return response.status_code == 200
    
    def listar_categorias(self):
        """Lista categorias de materiais"""
        response = requests.get(
            f'{self.base_url}/api/materiais/categorias/lista',
            headers=self.get_headers()
        )
        return response.json().get('categorias', []) if response.status_code == 200 else []
    

    # =====================================================
    # Máquinas
    # =====================================================

    def listar_maquinas(self, search=None, empresa=None, departamento=None, status='ativo'):
        """Lista maáquinas com filtros"""
        params = {'status': status}
        if search:
            params['search'] = search
        if empresa:
            params['empresa'] = empresa
        if departamento:
            params['departamento'] = departamento

        response = requests.get(
            f'{self.base_url}/api/maquinas',
            headers=self.get_headers(),
            params=params
        )
        return response.json() if response.status_code == 200 else []
    
    def criar_maquina(self, maquina):
        """Cria uma nova máquina"""
        response = requests.post(
            f"{self.base_url}/api/maquinas",
            json=maquina,
            headers=self.get_headers()
        )
        # Verificar se foi criado com sucesso (status 201)
        if response.status_code == 201:
            return response.json()  # Retorna a máquina criada
        else:
            print(f"Erro ao criar máquina: {response.status_code} - {response.text}")
            return None
    
    def atualizar_maquina(self, maquina_id, maquina):
        """Atualiza uma máquina"""
        response = requests.put(
            f'{self.base_url}/api/maquinas/{maquina_id}',
            json=maquina,
            headers=self.get_headers()
        )
        return response.json() if response.status_code == 200 else None
    
    def deletar_maquina(self, maquina_id):
        """Deleta uma máquina"""
        response = requests.delete(
            f'{self.base_url}/api/maquinas/{maquina_id}',
            headers=self.get_headers()
        )
        return response.status_code == 200
    
    def listar_departamentos(self):
        """Lista departamentos"""
        response = requests.get(
            f'{self.base_url}/api/maquinas/departamentos/lista',
            headers=self.get_headers()
        )
        return response.json().get('departamentos', []) if response.status_code == 200 else []
    

    # =====================================================
    # Movimentações
    # =====================================================

    def listar_movimentacoes(self, material_id=None, tipo=None, empresa=None, limit=100):
        """Lista movimentações com filtros"""
        params = {'limit': limit}
        if material_id:
            params['material_id'] = material_id

        if tipo:
            params['tipo'] = tipo

        if empresa:
            params['empresa'] = empresa

        response = requests.get(
            f'{self.base_url}/api/movimentacoes',
            headers=self.get_headers(),
            params=params
        )
        return response.json() if response.status_code == 200 else []
    
    def criar_movimentacao(self, movimentacao):
        """Registra uma movimentação"""
        response = requests.post(
            f'{self.base_url}/api/movimentacoes',
            json=movimentacao,
            headers=self.get_headers()
        )
        if response.status_code == 201:
            return response.json()
        else:
            print(f'Erro ao criar movimentação: {response.status_code} - {response.text}')
            return None
        
    def listar_materiais_para_movimentacao(self):
        """Lista materiais para usar no combo box"""
        response = requests.get(
            f'{self.base_url}/api/materiais',
            headers=self.get_headers()
        )
        return response.json() if response.status_code == 200 else []
    
    def listar_colaboradores_para_movimentacao(self):
        """Lista colaboradores para usar no combo box (destinatário)"""
        response = requests.get(
            f'{self.base_url}/api/colaboradores',
            headers=self.get_headers()
        )
        return response.json() if response.status_code == 200 else []

    
    # =====================================================
    # Manutenções
    # =====================================================

    def listar_manutencoes(self, status=None, maquina_id=None, limit=100):
        """Lista manutenções com filtros"""
        params = {'limit': limit}
        if status:
            params['status'] = status

        if maquina_id:
            params['maquina_id'] = maquina_id

        response = requests.get(
            f'{self.base_url}/api/manutencoes',
            headers=self.get_headers(),
            params=params
        )
        return response.json() if response.status_code == 200 else []
    
    def criar_manutencao(self, manutencao):
        """Cria uma nova manutenção"""
        response = requests.post(
            f"{self.base_url}/api/manutencoes",
            json=manutencao,
            headers=self.get_headers()
        )
        if response.status_code == 201:
            return response.json()
        else:
            print(f"Erro ao criar manutenção: {response.status_code} - {response.text}")
            return None
        
    def atualizar_manutencao(self, manutencao_id, manutencao):
        """Atualiza uma manutenção"""
        response = requests.put(
            f'{self.base_url}/api/manutencoes/{manutencao_id}',
            json=manutencao,
            headers=self.get_headers()
        )
        return response.json() if response.status_code == 200 else None
    
    def deletar_manutencao(self, manutencao_id):
        """Deleta uma manutenção"""
        response = requests.delete(
            f'{self.base_url}/api/manutencoes',
            headers=self.get_headers()
        )
        return response.status_code == 200
    
    def concluir_manutencao(self, manutencao_id):
        """conclui uma manutenção"""
        response = requests.put(
            f'{self.base_url}/api/manutencoes/{manutencao_id}/concluir',
            headers=self.get_headers()
        )
        return response.status_code == 200
    
    def listar_maquinas_para_manutencao(self):
        """Lista máquinas para usar no combo box"""
        response = requests.get(
            f'{self.base_url}/api/maquinas',
            headers=self.get_headers()
        )
        return response.json() if response.status_code == 200 else []
    

    # =====================================================
    # Pedidos
    # =====================================================

    def listar_pedidos(self, status=None, empresa=None, limit=100):
        """Lista pedidos com filtros"""
        params = {'limit': limit}
        if status:
            params['status'] = status

        if empresa:
            params['empresa'] = empresa

        response = requests.get(
            f'{self.base_url}/api/pedidos',
            headers=self.get_headers(),
            params=params
        )
        return response.json() if response.status_code == 200 else []

    def criar_pedido(self, pedido):
        """Cria um novo pedido (pode receber material_nome para criar material automaticamente)"""
        response = requests.post(
            f"{self.base_url}/api/pedidos",
            json=pedido,
            headers=self.get_headers()
        )
        if response.status_code == 201:
            return response.json()
        else:
            print(f"Erro ao criar pedido: {response.status_code} - {response.text}")
            return None
        
    def atualizar_pedido(self, pedido_id, pedido):
        """Atualiza um pedido"""
        response = requests.put(
            f"{self.base_url}/api/pedidos/{pedido_id}",
            json=pedido,
            headers=self.get_headers()
        )
        return response.json() if response.status_code == 200 else None

    def aprovar_pedido(self, pedido_id):
        """Aprova um pedido"""
        response = requests.put(
            f'{self.base_url}/api/pedidos/{pedido_id}/aprovar',
            headers=self.get_headers()
        )
        return response.status_code == 200

    def concluir_pedido(self, pedido_id):
        """Conclui um pedido"""
        response = requests.put(
            f'{self.base_url}/api/pedidos/{pedido_id}/concluir',
            headers=self.get_headers()
        )
        return response.status_code == 200

    def cancelar_pedido(self, pedido_id):
        """Cancela um pedido"""
        response = requests.put(
            f'{self.base_url}/api/pedidos/{pedido_id}/cancelar',
            headers=self.get_headers()
        )
        return response.status_code == 200
    
    def deletar_pedido(self, pedido_id):
        """Deleta um pedido"""
        response = requests.delete(
            f"{self.base_url}/api/pedidos/{pedido_id}",
            headers=self.get_headers()
        )
        return response.status_code == 200
    
    def listar_materiais_para_pedido(self):
        """Lista materiais para usar no combo box"""
        response = requests.get(
            f"{self.base_url}/api/materiais",
            headers=self.get_headers()
        )
        return response.json() if response.status_code == 200 else []
    

    # =====================================================
    # Usuários do Sistema
    # =====================================================

    def listar_usuarios(self):
        """Lista usuários do sistema"""
        response = requests.get(
            f"{self.base_url}/api/usuarios",
            headers=self.get_headers()
        )
        return response.json() if response.status_code == 200 else []
    
    def criar_usuario(self, usuario):
        """Cria um novo usuário"""
        response = requests.post(
            f"{self.base_url}/api/usuarios",
            json=usuario,
            headers=self.get_headers()
        )
        if response.status_code == 201:
            return response.json()
        else:
            print(f"Erro ao criar usuário: {response.status_code} - {response.text}")
            return None
        
    def atualizar_usuario(self, usuario_id, usuario):
        """Atualiza um usuário"""
        response = requests.put(
            f'{self.base_url}/api/usuarios/{usuario_id}',
            json=usuario,
            headers=self.get_headers()
        )
        return response.json() if response.status_code == 200 else None
    
    def deletar_usuario(self, usuario_id):
        """Deleta um usuário"""
        response = requests.delete(
            f'{self.base_url}/api/usuarios/{usuario_id}',
            headers=self.get_headers()
        )
        return response.status_code == 200
    
    def resetar_senha_usuario(self, usuario_id, nova_senha=None):
        """Reseta a senha de um usuário"""
        data = {}
        if nova_senha:
            data["nova_senha"] = nova_senha
        
        response = requests.post(
            f"{self.base_url}/api/usuarios/{usuario_id}/resetar-senha",
            json=data if data else None,
            headers=self.get_headers()
        )
        return response.status_code == 200
    
    def alterar_senha_usuario(self, usuario_id, nova_senha):
        """Altera a senha de um usuário específico"""
        response = requests.post(
            f"{self.base_url}/api/usuarios/{usuario_id}/alterar-senha",
            json={"nova_senha": nova_senha},
            headers=self.get_headers()
        )
        return response.status_code == 200


    # =====================================================
    # Colaboradores
    # =====================================================
    
    def listar_colaboradores(self, empresa=None):
        """Lista colaboradores"""
        params = {}
        if empresa:
            params["empresa"] = empresa
        
        response = requests.get(
            f"{self.base_url}/api/colaboradores",
            headers=self.get_headers(),
            params=params
        )
        return response.json() if response.status_code == 200 else []
    
    def criar_colaborador(self, colaborador):
        """Cria um novo colaborador"""
        response = requests.post(
            f"{self.base_url}/api/colaboradores",
            json=colaborador,
            headers=self.get_headers()
        )
        return response.json() if response.status_code == 201 else None
    

    # =====================================================
    # Dashboard
    # =====================================================

    def get_dashboard_resumo(self):
        """Obtém resumo para o dashboard"""
        response = requests.get(
            f"{self.base_url}/api/dashboard/resumo",
            headers=self.get_headers()
        )
        if response.status_code == 200:
            return response.json()
        else:
            return {
                "resumo": {
                    "total_materiais": 0,
                    "itens_baixo_estoque": 0,
                    "maquinas_ativas": 0,
                    "manutencoes_pendentes": 0,
                    "pedidos_pendentes": 0
                }
            }


# =====================================================
# Demandas / Chamados TI
# =====================================================

    def listar_demandas(self, status=None, prioridade=None, empresa=None):
        params = {}
        if status:
            params["status"] = status
        if prioridade:
            params["prioridade"] = prioridade
        if empresa:
            params["empresa"] = empresa
        
        response = requests.get(
            f"{self.base_url}/api/demandas",
            headers=self.get_headers(),
            params=params
        )
        if response.status_code == 200:
            return response.json()
        else:
                print(f"Erro ao listar demandas: {response.status_code} - {response.text}")
                return []

    def criar_demanda(self, demanda):
        response = requests.post(
            f"{self.base_url}/api/demandas",
            json=demanda,
            headers=self.get_headers()
        )
        if response.status_code == 201:
            return response.json()
        else:
                print(f"Erro ao criar demanda: {response.status_code} - {response.text}")
                return None

    def atualizar_demanda(self, demanda_id, demanda):
        response = requests.put(
            f"{self.base_url}/api/demandas/{demanda_id}",
            json=demanda,
            headers=self.get_headers()
        )
        if response.status_code == 200:
            return response.json()
        else:
                print(f"Erro ao atualizar demanda: {response.status_code} - {response.text}")
                return None

    def concluir_demanda(self, demanda_id):
        response = requests.put(
            f"{self.base_url}/api/demandas/{demanda_id}/concluir",
            headers=self.get_headers()
        )
        return response.status_code == 200

    def cancelar_demanda(self, demanda_id):
        response = requests.put(
            f"{self.base_url}/api/demandas/{demanda_id}/cancelar",
            headers=self.get_headers()
        )
        return response.status_code == 200

    def deletar_demanda(self, demanda_id):
        response = requests.delete(
            f"{self.base_url}/api/demandas/{demanda_id}",
            headers=self.get_headers()
        )
        return response.status_code == 200


# Instância global do cliente
api_client = APIClient()
    
