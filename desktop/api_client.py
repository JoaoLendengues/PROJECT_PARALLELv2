import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv('API_URL', 'http://10.1.1.151:8000')

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
            headers['Authorization'] = f'Bearer {self.token}'
        return headers

    # =====================================================
    # Autenticação
    # =====================================================

    def login(self, codigo, senha):
        """Realiza login e armazena o token"""
        try:
            response = requests.post(
                f"{self.base_url}/api/auth/login",
                json={"codigo": codigo, "senha": senha},
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                self.set_token(data["access_token"])
                return {"success": True, "usuario": data["usuario"]}
            else:
                try:
                    error_data = response.json()
                    error_msg = error_data.get("detail", "Erro no login")
                except:
                    error_msg = response.text if response.text else "Erro no login"
                return {"success": False, "error": error_msg}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # =====================================================
    # Materiais
    # =====================================================

    def listar_materiais(self, search=None, categoria=None, empresa=None, status="ativo"):
        """Lista materiais com filtros"""
        params = {"status": status}
        if search:
            params["search"] = search
        if categoria:
            params["categoria"] = categoria
        if empresa:
            params["empresa"] = empresa
        
        try:
            response = requests.get(
                f"{self.base_url}/api/materiais",
                headers=self.get_headers(),
                params=params,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, dict) and "items" in data:
                    return data["items"]
                elif isinstance(data, list):
                    return data
                else:
                    print(f"⚠️ Formato inesperado: {type(data)}")
                    return []
            else:
                print(f"❌ Erro {response.status_code}: {response.text[:100]}")
                return []
        except Exception as e:
            print(f"❌ Erro ao listar materiais: {e}")
            return []
    
    def criar_material(self, material):
        """Cria um novo material"""
        try:
            response = requests.post(
                f"{self.base_url}/api/materiais",
                json=material,
                headers=self.get_headers(),
                timeout=30
            )
            if response.status_code == 201:
                return response.json()
            else:
                print(f"Erro ao criar material: {response.status_code}")
                return None
        except Exception as e:
            print(f"Erro ao criar material: {e}")
            return None
    
    def atualizar_material(self, material_id, material):
        """Atualiza um material"""
        try:
            response = requests.put(
                f"{self.base_url}/api/materiais/{material_id}",
                json=material,
                headers=self.get_headers(),
                timeout=30
            )
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"Erro ao atualizar material: {e}")
            return None
    
    def deletar_material(self, material_id):
        """Deleta um material"""
        try:
            response = requests.delete(
                f"{self.base_url}/api/materiais/{material_id}",
                headers=self.get_headers(),
                timeout=30
            )
            return response.status_code == 200
        except:
            return False
    
    def listar_categorias(self):
        """Lista categorias de materiais"""
        try:
            response = requests.get(
                f"{self.base_url}/api/materiais/categorias/lista",
                headers=self.get_headers(),
                timeout=30
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("categorias", [])
            return []
        except:
            return []

    # =====================================================
    # Máquinas
    # =====================================================

    def listar_maquinas(self, search=None, empresa=None, departamento=None, status="ativo"):
        """Lista máquinas com filtros"""
        params = {"status": status}
        if search:
            params["search"] = search
        if empresa:
            params["empresa"] = empresa
        if departamento:
            params["departamento"] = departamento
        
        try:
            response = requests.get(
                f"{self.base_url}/api/maquinas",
                headers=self.get_headers(),
                params=params,
                timeout=30
            )
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, dict) and "items" in data:
                    return data["items"]
                elif isinstance(data, list):
                    return data
            return []
        except:
            return []
    
    def criar_maquina(self, maquina):
        """Cria uma nova máquina"""
        try:
            response = requests.post(
                f"{self.base_url}/api/maquinas",
                json=maquina,
                headers=self.get_headers(),
                timeout=30
            )
            if response.status_code == 201:
                return response.json()
            return None
        except:
            return None
    
    def atualizar_maquina(self, maquina_id, maquina):
        """Atualiza uma máquina"""
        try:
            response = requests.put(
                f"{self.base_url}/api/maquinas/{maquina_id}",
                json=maquina,
                headers=self.get_headers(),
                timeout=30
            )
            if response.status_code == 200:
                return response.json()
            return None
        except:
            return None
    
    def deletar_maquina(self, maquina_id):
        """Deleta uma máquina"""
        try:
            response = requests.delete(
                f"{self.base_url}/api/maquinas/{maquina_id}",
                headers=self.get_headers(),
                timeout=30
            )
            return response.status_code == 200
        except:
            return False
    
    def listar_departamentos(self):
        """Lista departamentos"""
        try:
            response = requests.get(
                f"{self.base_url}/api/maquinas/departamentos/lista",
                headers=self.get_headers(),
                timeout=30
            )
            if response.status_code == 200:
                data = response.json()
                # O backend retorna {'departamentos': [...]}
                return data
            return []
        except:
            return []

    # =====================================================
    # Movimentações
    # =====================================================

    def listar_movimentacoes(self, material_id=None, tipo=None, empresa=None, limit=100):
        """Lista movimentações com filtros"""
        params = {"limit": limit}
        if material_id:
            params["material_id"] = material_id
        if tipo:
            params["tipo"] = tipo
        if empresa:
            params["empresa"] = empresa
        
        try:
            response = requests.get(
                f"{self.base_url}/api/movimentacoes",
                headers=self.get_headers(),
                params=params,
                timeout=30
            )
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    return data
            return []
        except:
            return []
    
    def criar_movimentacao(self, movimentacao):
        """Registra uma movimentação"""
        try:
            response = requests.post(
                f"{self.base_url}/api/movimentacoes",
                json=movimentacao,
                headers=self.get_headers(),
                timeout=30
            )
            if response.status_code == 201:
                return response.json()
            return None
        except:
            return None
    
    def listar_materiais_para_movimentacao(self):
        """Lista materiais para combo box"""
        return self.listar_materiais()
    
    def listar_colaboradores_para_movimentacao(self):
        """Lista colaboradores para combo box"""
        return self.listar_colaboradores()
    
    def deletar_movimentacao(self, movimentacao_id):
        """Deleta uma movimentação (requer admin)"""
        try:
            response = requests.delete(
                f"{self.base_url}/api/movimentacoes/{movimentacao_id}",
                headers=self.get_headers(),
                timeout=30
            )
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Erro ao deletar movimentação: {e}")
            return False

    # =====================================================
    # Manutenções
    # =====================================================

    def listar_manutencoes(self, status=None, maquina_id=None, limit=100):
        """Lista manutenções com filtros"""
        params = {"limit": limit}
        if status:
            params["status"] = status
        if maquina_id:
            params["maquina_id"] = maquina_id
        
        try:
            response = requests.get(
                f"{self.base_url}/api/manutencoes",
                headers=self.get_headers(),
                params=params,
                timeout=30
            )
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    return data
            return []
        except:
            return []
    
    def criar_manutencao(self, manutencao):
        """Cria uma nova manutenção"""
        try:
            response = requests.post(
                f"{self.base_url}/api/manutencoes",
                json=manutencao,
                headers=self.get_headers(),
                timeout=30
            )
            if response.status_code == 201:
                return response.json()
            return None
        except:
            return None
    
    def atualizar_manutencao(self, manutencao_id, manutencao):
        """Atualiza uma manutenção"""
        try:
            response = requests.put(
                f"{self.base_url}/api/manutencoes/{manutencao_id}",
                json=manutencao,
                headers=self.get_headers(),
                timeout=30
            )
            if response.status_code == 200:
                return response.json()
            return None
        except:
            return None
    
    def deletar_manutencao(self, manutencao_id):
        """Deleta uma manutenção"""
        try:
            response = requests.delete(
                f"{self.base_url}/api/manutencoes/{manutencao_id}",
                headers=self.get_headers(),
                timeout=30
            )
            return response.status_code == 200
        except:
            return False
    
    def concluir_manutencao(self, manutencao_id):
        """Conclui uma manutenção"""
        try:
            response = requests.put(
                f"{self.base_url}/api/manutencoes/{manutencao_id}/concluir",
                headers=self.get_headers(),
                timeout=30
            )
            return response.status_code == 200
        except:
            return False
    
    def listar_maquinas_para_manutencao(self):
        """Lista máquinas para combo box"""
        return self.listar_maquinas()

    # =====================================================
    # Pedidos
    # =====================================================

    def listar_pedidos(self, status=None, empresa=None, limit=100):
        """Lista pedidos com filtros"""
        params = {"limit": limit}
        if status:
            params["status"] = status
        if empresa:
            params["empresa"] = empresa
        
        try:
            response = requests.get(
                f"{self.base_url}/api/pedidos",
                headers=self.get_headers(),
                params=params,
                timeout=30
            )
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    return data
            return []
        except:
            return []
    
    def criar_pedido(self, pedido):
        """Cria um novo pedido"""
        try:
            response = requests.post(
                f"{self.base_url}/api/pedidos",
                json=pedido,
                headers=self.get_headers(),
                timeout=30
            )
            if response.status_code == 201:
                return response.json()
            return None
        except:
            return None
    
    def atualizar_pedido(self, pedido_id, pedido):
        """Atualiza um pedido"""
        try:
            response = requests.put(
                f"{self.base_url}/api/pedidos/{pedido_id}",
                json=pedido,
                headers=self.get_headers(),
                timeout=30
            )
            if response.status_code == 200:
                return response.json()
            return None
        except:
            return None
    
    def aprovar_pedido(self, pedido_id):
        """Aprova um pedido"""
        try:
            response = requests.put(
                f"{self.base_url}/api/pedidos/{pedido_id}/aprovar",
                headers=self.get_headers(),
                timeout=30
            )
            return response.status_code == 200
        except:
            return False
    
    def concluir_pedido(self, pedido_id):
        """Conclui um pedido"""
        try:
            response = requests.put(
                f"{self.base_url}/api/pedidos/{pedido_id}/concluir",
                headers=self.get_headers(),
                timeout=30
            )
            return response.status_code == 200
        except Exception as e:
            print(f'❌ Erro ao concluir pedido> {e}')
            return False
            
    
    def cancelar_pedido(self, pedido_id):
        """Cancela um pedido"""
        try:
            response = requests.put(
                f"{self.base_url}/api/pedidos/{pedido_id}/cancelar",
                headers=self.get_headers(),
                timeout=30
            )
            return response.status_code == 200
        except:
            return False
    
    def deletar_pedido(self, pedido_id):
        """Deleta um pedido"""
        try:
            response = requests.delete(
                f"{self.base_url}/api/pedidos/{pedido_id}",
                headers=self.get_headers(),
                timeout=30
            )
            return response.status_code == 200
        except:
            return False
    
    def listar_materiais_para_pedido(self):
        """Lista materiais para combo box"""
        return self.listar_materiais()

    # =====================================================
    # Colaboradores
    # =====================================================

    def listar_colaboradores(self, empresa=None):
        """Lista colaboradores"""
        params = {}
        if empresa:
            params["empresa"] = empresa
        
        try:
            response = requests.get(
                f"{self.base_url}/api/colaboradores",
                headers=self.get_headers(),
                params=params,
                timeout=30
            )
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    return data
            return []
        except:
            return []
    
    def criar_colaborador(self, colaborador):
        """Cria um novo colaborador"""
        try:
            response = requests.post(
                f"{self.base_url}/api/colaboradores",
                json=colaborador,
                headers=self.get_headers(),
                timeout=30
            )
            if response.status_code == 201:
                return response.json()
            return None
        except:
            return None
    
    def atualizar_colaborador(self, colaborador_id, colaborador):
        """Atualiza um colaborador"""
        try:
            response = requests.put(
                f"{self.base_url}/api/colaboradores/{colaborador_id}",
                json=colaborador,
                headers=self.get_headers(),
                timeout=30
            )
            if response.status_code == 200:
                return response.json()
            return None
        except:
            return None
    
    def deletar_colaborador(self, colaborador_id):
        """Deleta um colaborador"""
        try:
            response = requests.delete(
                f"{self.base_url}/api/colaboradores/{colaborador_id}",
                headers=self.get_headers(),
                timeout=30
            )
            return response.status_code == 200
        except:
            return False

    # =====================================================
    # Demandas
    # =====================================================

    def listar_demandas(self, status=None, prioridade=None, empresa=None):
        """Lista demandas com filtros"""
        params = {}
        if status:
            params["status"] = status
        if prioridade:
            params["prioridade"] = prioridade
        if empresa:
            params["empresa"] = empresa
        
        try:
            response = requests.get(
                f"{self.base_url}/api/demandas",
                headers=self.get_headers(),
                params=params,
                timeout=30
            )
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    return data
            return []
        except:
            return []
    
    def criar_demanda(self, demanda):
        """Cria uma nova demanda"""
        try:
            response = requests.post(
                f"{self.base_url}/api/demandas",
                json=demanda,
                headers=self.get_headers(),
                timeout=30
            )
            if response.status_code == 201:
                return response.json()
            return None
        except:
            return None
    
    def atualizar_demanda(self, demanda_id, demanda):
        """Atualiza uma demanda"""
        try:
            response = requests.put(
                f"{self.base_url}/api/demandas/{demanda_id}",
                json=demanda,
                headers=self.get_headers(),
                timeout=30
            )
            if response.status_code == 200:
                return response.json()
            return None
        except:
            return None
    
    def concluir_demanda(self, demanda_id):
        """Conclui uma demanda"""
        try:
            response = requests.put(
                f"{self.base_url}/api/demandas/{demanda_id}/concluir",
                headers=self.get_headers(),
                timeout=30
            )
            return response.status_code == 200
        except:
            return False
    
    def cancelar_demanda(self, demanda_id):
        """Cancela uma demanda"""
        try:
            response = requests.put(
                f"{self.base_url}/api/demandas/{demanda_id}/cancelar",
                headers=self.get_headers(),
                timeout=30
            )
            return response.status_code == 200
        except:
            return False
    
    def deletar_demanda(self, demanda_id):
        """Deleta uma demanda"""
        try:
            response = requests.delete(
                f"{self.base_url}/api/demandas/{demanda_id}",
                headers=self.get_headers(),
                timeout=30
            )
            return response.status_code == 200
        except:
            return False

    # =====================================================
    # Usuários
    # =====================================================

    def listar_usuarios(self):
        """Lista usuários do sistema"""
        try:
            response = requests.get(
                f"{self.base_url}/api/usuarios",
                headers=self.get_headers(),
                timeout=30
            )
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    return data
            return []
        except:
            return []
    
    def criar_usuario(self, usuario):
        """Cria um novo usuário"""
        try:
            response = requests.post(
                f"{self.base_url}/api/usuarios",
                json=usuario,
                headers=self.get_headers(),
                timeout=30
            )
            if response.status_code == 201:
                return response.json()
            return None
        except:
            return None
    
    def atualizar_usuario(self, usuario_id, usuario):
        """Atualiza um usuário"""
        try:
            response = requests.put(
                f"{self.base_url}/api/usuarios/{usuario_id}",
                json=usuario,
                headers=self.get_headers(),
                timeout=30
            )
            if response.status_code == 200:
                return response.json()
            return None
        except:
            return None
    
    def deletar_usuario(self, usuario_id):
        """Deleta um usuário"""
        try:
            response = requests.delete(
                f"{self.base_url}/api/usuarios/{usuario_id}",
                headers=self.get_headers(),
                timeout=30
            )
            return response.status_code == 200
        except:
            return False
    
    def resetar_senha_usuario(self, usuario_id, nova_senha=None):
        """Reseta a senha de um usuário"""
        data = {}
        if nova_senha:
            data["nova_senha"] = nova_senha
        
        try:
            response = requests.post(
                f"{self.base_url}/api/usuarios/{usuario_id}/resetar-senha",
                json=data if data else None,
                headers=self.get_headers(),
                timeout=30
            )
            return response.status_code == 200
        except:
            return False
    
    def alterar_senha_usuario(self, usuario_id, nova_senha):
        """Altera a senha de um usuário"""
        try:
            response = requests.post(
                f"{self.base_url}/api/usuarios/{usuario_id}/alterar-senha",
                json={"nova_senha": nova_senha},
                headers=self.get_headers(),
                timeout=30
            )
            return response.status_code == 200
        except:
            return False

    def get_proximo_codigo(self):
        """Obtém o próximo código disponível para novo usuário"""
        try:
            response = requests.get(
                f"{self.base_url}/api/usuarios/proximo-codigo",
                headers=self.get_headers(),
                timeout=30
            )
            if response.status_code == 200:
                return response.json()
            return {"proximo_codigo": "1"}
        except Exception as e:
            print(f"❌ Erro ao buscar próximo código: {e}")
            return {"proximo_codigo": "1"}

    # =====================================================
    # CRUD para Empresas, Departamentos e Categorias
    # =====================================================

    def get_empresas(self):
        """Retorna lista de empresas do backend"""
        try:
            response = requests.get(
                f"{self.base_url}/api/configuracoes/empresas",
                headers=self.get_headers(),
                timeout=30
            )
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            print(f"❌ Erro ao carregar empresas: {e}")
            return []

    def add_empresa(self, nome):
        """Adiciona uma nova empresa"""
        try:
            response = requests.post(
                f"{self.base_url}/api/configuracoes/empresas",
                json={"nome": nome},
                headers=self.get_headers(),
                timeout=30
            )
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Erro ao adicionar empresa: {e}")
            return False

    def delete_empresa(self, nome):
        """Remove uma empresa"""
        try:
            response = requests.delete(
                f"{self.base_url}/api/configuracoes/empresas/{nome}",
                headers=self.get_headers(),
                timeout=30
            )
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Erro ao remover empresa: {e}")
            return False

    def get_departamentos(self):
        """Retorna lista de departamentos do backend"""
        try:
            response = requests.get(
                f"{self.base_url}/api/configuracoes/departamentos",
                headers=self.get_headers(),
                timeout=30
            )
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            print(f"❌ Erro ao carregar departamentos: {e}")
            return []

    def add_departamento(self, nome):
        """Adiciona um novo departamento"""
        try:
            response = requests.post(
                f"{self.base_url}/api/configuracoes/departamentos",
                json={"nome": nome},
                headers=self.get_headers(),
                timeout=30
            )
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Erro ao adicionar departamento: {e}")
            return False

    def delete_departamento(self, nome):
        """Remove um departamento"""
        try:
            response = requests.delete(
                f"{self.base_url}/api/configuracoes/departamentos/{nome}",
                headers=self.get_headers(),
                timeout=30
            )
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Erro ao remover departamento: {e}")
            return False

    def get_categorias(self):
        """Retorna lista de categorias do backend"""
        try:
            response = requests.get(
                f"{self.base_url}/api/configuracoes/categorias",
                headers=self.get_headers(),
                timeout=30
            )
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            print(f"❌ Erro ao carregar categorias: {e}")
            return []

    def add_categoria(self, nome):
        """Adiciona uma nova categoria"""
        try:
            response = requests.post(
                f"{self.base_url}/api/configuracoes/categorias",
                json={"nome": nome},
                headers=self.get_headers(),
                timeout=30
            )
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Erro ao adicionar categoria: {e}")
            return False

    def delete_categoria(self, nome):
        """Remove uma categoria"""
        try:
            response = requests.delete(
                f"{self.base_url}/api/configuracoes/categorias/{nome}",
                headers=self.get_headers(),
                timeout=30
            )
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Erro ao remover categoria: {e}")
            return False

    # =====================================================
    # Configurações Gerais do Sistema
    # =====================================================

    def get_configuracoes(self):
        """Obtém as configurações gerais do sistema"""
        try:
            response = requests.get(
                f"{self.base_url}/api/configuracoes",
                headers=self.get_headers(),
                timeout=30
            )
            if response.status_code == 200:
                return response.json()
            return {}
        except Exception as e:
            print(f"❌ Erro ao carregar configurações: {e}")
            return {}

    def salvar_configuracoes(self, configuracoes):
        """Salva as configurações gerais do sistema"""
        try:
            response = requests.post(
                f"{self.base_url}/api/configuracoes",
                json=configuracoes,
                headers=self.get_headers(),
                timeout=30
            )
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Erro ao salvar configurações: {e}")
            return False
        
    # =====================================================
    # Backup
    # =====================================================
     
    def executar_backup(self):
        """Executa backup manual do banco de dados"""
        try:
            response = requests.post(
                f"{self.base_url}/api/backup/executar",
                headers=self.get_headers(),
                timeout=60
            )
            if response.status_code == 200:
                return True, response.json()
            return False, None
        except Exception as e:
            print(f"❌ Erro ao executar backup: {e}")
            return False, None 
        
    def listar_backups(self):
        """Lista todos os backups disponíveis"""
        try:
            response = requests.get(
                f"{self.base_url}/api/backup/listar",
                headers=self.get_headers(),
                timeout=30
            )
            if response.status_code == 200:
                return response.json().get("backups", [])
            return []
        except Exception as e:
            print(f"❌ Erro ao listar backups: {e}")
            return []
        
    def restaurar_backup(self, filename):
        """Restaura um backup específico"""
        try:
            response = requests.post(
                f"{self.base_url}/api/backup/restaurar/{filename}",
                headers=self.get_headers(),
                timeout=120
            )
            return response.status_code == 200, response.json() if response.status_code == 200 else None
        except Exception as e:
            print(f"❌ Erro ao restaurar backup: {e}")
            return False, None
        
    def reconfigurar_backup(self):
        """Reconfigura o scheduler de backup"""
        try:
            response = requests.post(
                f"{self.base_url}/api/backup/configurar",
                headers=self.get_headers(),
                timeout=30
            )
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Erro ao reconfigurar backup: {e}")
            return False

    # =====================================================
    # Dashboard
    # =====================================================

    def get_dashboard_resumo(self):
        """Obtém resumo para o dashboard"""
        try:
            response = requests.get(
                f"{self.base_url}/api/dashboard/resumo",
                headers=self.get_headers(),
                timeout=30
            )
            if response.status_code == 200:
                return response.json()
            return {"resumo": {}}
        except:
            return {"resumo": {}}
        
    def get_status_internet(self):
        """Obtém o status da internet (latência e qualidade)"""
        try:
            response = requests.get(
                f'{self.base_url}/api/dashboard/status-internet',
                headers=self.get_headers(),
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
            return {'status': 'offline', 'qualidade': 'erro', 'latencia_ms': None}
        except Exception as e:
            print(f'❌ Erro ao obter status da internet: {e}')
            return {'status': 'offline', 'qualidade': 'erro', 'latencia_ms': None}
        
    # =====================================================
    # Departamentos (CRUD)
    # =====================================================

    def get_departamentos_lista(self):
        """Retorna lista de nomes de departamentos para combobox"""
        try:
            response = requests.get(
                f"{self.base_url}/api/departamentos/lista",
                headers=self.get_headers(),
                timeout=30
            )
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            print(f"❌ Erro ao carregar departamentos: {e}")
            return []

    def get_departamentos_completo(self):
        """Retorna lista completa de departamentos (com IDs)"""
        try:
            response = requests.get(
                f"{self.base_url}/api/departamentos",
                headers=self.get_headers(),
                timeout=30
            )
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            print(f"❌ Erro ao carregar departamentos: {e}")
            return []

    def criar_departamento(self, nome, descricao=None):
        """Cria um novo departamento"""
        try:
            response = requests.post(
                f"{self.base_url}/api/departamentos",
                json={"nome": nome, "descricao": descricao},
                headers=self.get_headers(),
                timeout=30
            )
            return response.status_code == 201
        except Exception as e:
            print(f"❌ Erro ao criar departamento: {e}")
            return False

    def atualizar_departamento(self, departamento_id, nome, descricao=None, ativo=True):
        """Atualiza um departamento"""
        try:
            response = requests.put(
                f"{self.base_url}/api/departamentos/{departamento_id}",
                json={"nome": nome, "descricao": descricao, "ativo": ativo},
                headers=self.get_headers(),
                timeout=30
            )
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Erro ao atualizar departamento: {e}")
            return False

    def deletar_departamento(self, departamento_id):
        """Deleta um departamento"""
        try:
            response = requests.delete(
                f"{self.base_url}/api/departamentos/{departamento_id}",
                headers=self.get_headers(),
                timeout=30
            )
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Erro ao deletar departamento: {e}")
            return False
        
    # =====================================================
    # Cargos (CRUD)
    # =====================================================

    def get_cargos_lista(self):
        """Retorna lista de nomes de cargos para combobox"""
        try:
            response = requests.get(
                f"{self.base_url}/api/cargos/lista",
                headers=self.get_headers(),
                timeout=30
            )
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            print(f"❌ Erro ao carregar cargos: {e}")
            return []

    def get_cargos_completo(self):
        """Retorna lista completa de cargos (com IDs)"""
        try:
            response = requests.get(
                f"{self.base_url}/api/cargos",
                headers=self.get_headers(),
                timeout=30
            )
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            print(f"❌ Erro ao carregar cargos: {e}")
            return []

    def criar_cargo(self, nome, descricao=None):
        """Cria um novo cargo"""
        try:
            response = requests.post(
                f"{self.base_url}/api/cargos",
                json={"nome": nome, "descricao": descricao},
                headers=self.get_headers(),
                timeout=30
            )
            return response.status_code == 201
        except Exception as e:
            print(f"❌ Erro ao criar cargo: {e}")
            return False

    def atualizar_cargo(self, cargo_id, nome, descricao=None, ativo=True):
        """Atualiza um cargo"""
        try:
            response = requests.put(
                f"{self.base_url}/api/cargos/{cargo_id}",
                json={"nome": nome, "descricao": descricao, "ativo": ativo},
                headers=self.get_headers(),
                timeout=30
            )
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Erro ao atualizar cargo: {e}")
            return False

    def deletar_cargo(self, cargo_id):
        """Deleta um cargo"""
        try:
            response = requests.delete(
                f"{self.base_url}/api/cargos/{cargo_id}",
                headers=self.get_headers(),
                timeout=30
            )
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Erro ao deletar cargo: {e}")
            return False


# Instância global do cliente
api_client = APIClient()