import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from app_paths import get_env_file_path

load_dotenv(get_env_file_path())

API_URL = os.getenv('API_URL', 'http://10.1.1.151:8000').rstrip('/')


class APIClient:
    """Cliente para comunicação com a API do Project Parallel"""

    def __init__(self):
        self.base_url = API_URL
        self.token = None
        # ✅ CACHE para dados estáticos
        self._cache = {}
        self._cache_time = {}
        self._cache_ttl = 300  # 5 minutos

    def _get_cache(self, key):
        """Obtém valor do cache se ainda válido"""
        if key in self._cache and key in self._cache_time:
            if datetime.now() - self._cache_time[key] < timedelta(seconds=self._cache_ttl):
                return self._cache[key]
        return None

    def _set_cache(self, key, value):
        """Armazena valor no cache"""
        self._cache[key] = value
        self._cache_time[key] = datetime.now()

    def _clear_cache(self, key=None):
        """Limpa o cache (tudo ou uma chave específica)"""
        if key:
            self._cache.pop(key, None)
            self._cache_time.pop(key, None)
        else:
            self._cache.clear()
            self._cache_time.clear()

    def set_token(self, token):
        """Define o token de autenticação"""
        self.token = token
        # ✅ Limpar cache ao trocar de usuário
        self._clear_cache()

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
                # ✅ Limpar cache ao fazer login
                self._clear_cache()
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

    def confirmar_senha_atual(self, senha):
        """Confirma a senha do usuario autenticado para acoes sensiveis."""
        try:
            response = requests.post(
                f"{self.base_url}/api/auth/confirmar-senha",
                json={"senha": senha},
                headers=self.get_headers(),
                timeout=30
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Erro ao confirmar senha: {e}")
            return False

    # =====================================================
    # Materiais
    # =====================================================

    def listar_materiais(self, search=None, categoria=None, empresa=None, status="", page=1, page_size=200):
        """Lista materiais com filtros e paginação"""
        params = {"page": page, "limit": page_size}
        if status is not None:
            params["status"] = status
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
                # ✅ Limpar cache de materiais
                self._clear_cache("materiais_lista")
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
                # ✅ Limpar cache
                self._clear_cache("materiais_lista")
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
            if response.status_code == 200:
                # ✅ Limpar cache
                self._clear_cache("materiais_lista")
            return response.status_code == 200
        except:
            return False

    def listar_categorias(self, use_cache=True):
        """Lista categorias de materiais com cache"""
        if use_cache:
            cached = self._get_cache("categorias")
            if cached is not None:
                return cached

        try:
            response = requests.get(
                f"{self.base_url}/api/materiais/categorias/lista",
                headers=self.get_headers(),
                timeout=30
            )
            if response.status_code == 200:
                data = response.json()
                categorias = data.get("categorias", [])
                self._set_cache("categorias", categorias)
                return categorias
            return []
        except:
            return []

    # =====================================================
    # Máquinas
    # =====================================================

    def listar_maquinas(self, search=None, empresa=None, departamento=None, status=""):
        """Lista máquinas com filtros"""
        params = {}
        if status is not None:
            params["status"] = status
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
                self._clear_cache("maquinas_lista")
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
                self._clear_cache("maquinas_lista")
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
            if response.status_code == 200:
                self._clear_cache("maquinas_lista")
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
        return self.listar_materiais(status="ativo")

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
        return self.listar_materiais(status="ativo")

    # =====================================================
    # Colaboradores
    # =====================================================

    def listar_colaboradores(self, empresa=None):
        """Lista colaboradores"""
        params = {"limit": 500}
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
                if isinstance(data, dict) and "items" in data:
                    return data["items"]
                if isinstance(data, list):
                    return data
            else:
                print(f"Erro ao listar colaboradores: {response.status_code} - {response.text[:200]}")
            return []
        except Exception as e:
            print(f"Erro ao listar colaboradores: {e}")
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
                self._clear_cache("colaboradores_lista")
                return response.json()
            print(f"Erro ao criar colaborador: {response.status_code} - {response.text[:200]}")
            return None
        except Exception as e:
            print(f"Erro ao criar colaborador: {e}")
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
                self._clear_cache("colaboradores_lista")
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
            if response.status_code == 200:
                self._clear_cache("colaboradores_lista")
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
            print(f"Erro ao criar demanda: {response.status_code} - {response.text[:200]}")
            return None
        except Exception as e:
            print(f"Erro ao criar demanda: {e}")
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
                elif isinstance(data, dict) and "items" in data:
                    return data["items"]
                else:
                    print(f"⚠️ Formato inesperado: {type(data)}")
                    return []
            else:
                print(f"❌ Erro {response.status_code}: {response.text[:100]}")
                return []
        except Exception as e:
            print(f"❌ Erro ao listar usuários: {e}")
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
                self._clear_cache("usuarios_lista")
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
                self._clear_cache("usuarios_lista")
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
            if response.status_code == 200:
                self._clear_cache("usuarios_lista")
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
            print(f"Erro ao buscar proximo codigo: {response.status_code} - {response.text[:200]}")
        except Exception as e:
            print(f"❌ Erro ao buscar próximo código: {e}")
        return {"proximo_codigo": self.calcular_proximo_codigo_local()}

    def calcular_proximo_codigo_local(self):
        """Calcula o proximo codigo usando a lista de usuarios disponivel."""
        max_codigo = 0
        for usuario in self.listar_usuarios():
            try:
                codigo = int(str(usuario.get("codigo", "")).strip())
            except ValueError:
                continue
            max_codigo = max(max_codigo, codigo)
        return str(max_codigo + 1)

    # =====================================================
    # CRUD para Empresas, Departamentos e Categorias (COM CACHE)
    # =====================================================

    def get_empresas(self, use_cache=True):
        """Retorna lista de empresas do backend com cache"""
        if use_cache:
            cached = self._get_cache("empresas")
            if cached is not None:
                return cached

        try:
            response = requests.get(
                f"{self.base_url}/api/configuracoes/empresas",
                headers=self.get_headers(),
                timeout=30
            )
            if response.status_code == 200:
                data = response.json()
                self._set_cache("empresas", data)
                return data
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
            if response.status_code == 200:
                self._clear_cache("empresas")  # ✅ Limpar cache
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Erro ao adicionar empresa: {e}")
            return False

    def update_empresa(self, nome_atual, novo_nome):
        """Atualiza o nome de uma empresa."""
        try:
            response = requests.put(
                f"{self.base_url}/api/configuracoes/empresas/{nome_atual}",
                json={"nome": novo_nome},
                headers=self.get_headers(),
                timeout=30
            )
            if response.status_code == 200:
                self._clear_cache("empresas")
            return response.status_code == 200
        except Exception as e:
            print(f"Erro ao atualizar empresa: {e}")
            return False

    def delete_empresa(self, nome):
        """Remove uma empresa"""
        try:
            response = requests.delete(
                f"{self.base_url}/api/configuracoes/empresas/{nome}",
                headers=self.get_headers(),
                timeout=30
            )
            if response.status_code == 200:
                self._clear_cache("empresas")  # ✅ Limpar cache
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Erro ao remover empresa: {e}")
            return False

    def get_departamentos(self, use_cache=True):
        """Retorna lista de departamentos do backend com cache"""
        if use_cache:
            cached = self._get_cache("departamentos")
            if cached is not None:
                return cached

        try:
            response = requests.get(
                f"{self.base_url}/api/departamentos/lista",
                headers=self.get_headers(),
                timeout=30
            )
            if response.status_code == 200:
                data = response.json()
                self._set_cache("departamentos", data)
                return data
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
            if response.status_code == 200:
                self._clear_cache("departamentos")  # ✅ Limpar cache
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
            if response.status_code == 200:
                self._clear_cache("departamentos")  # ✅ Limpar cache
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Erro ao remover departamento: {e}")
            return False

    def get_categorias(self, use_cache=True):
        """Retorna lista de categorias do backend com cache"""
        if use_cache:
            cached = self._get_cache("categorias")
            if cached is not None:
                return cached

        try:
            response = requests.get(
                f"{self.base_url}/api/configuracoes/categorias",
                headers=self.get_headers(),
                timeout=30
            )
            if response.status_code == 200:
                data = response.json()
                self._set_cache("categorias", data)
                return data
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
            if response.status_code == 200:
                self._clear_cache("categorias")  # ✅ Limpar cache
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Erro ao adicionar categoria: {e}")
            return False

    def update_categoria(self, nome_atual, novo_nome):
        """Atualiza o nome de uma categoria."""
        try:
            response = requests.put(
                f"{self.base_url}/api/configuracoes/categorias/{nome_atual}",
                json={"nome": novo_nome},
                headers=self.get_headers(),
                timeout=30
            )
            if response.status_code == 200:
                self._clear_cache("categorias")
            return response.status_code == 200
        except Exception as e:
            print(f"Erro ao atualizar categoria: {e}")
            return False

    def delete_categoria(self, nome):
        """Remove uma categoria"""
        try:
            response = requests.delete(
                f"{self.base_url}/api/configuracoes/categorias/{nome}",
                headers=self.get_headers(),
                timeout=30
            )
            if response.status_code == 200:
                self._clear_cache("categorias")  # ✅ Limpar cache
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

    def get_departamentos_lista(self, use_cache=True):
        """Retorna lista de nomes de departamentos para combobox com cache"""
        if use_cache:
            cached = self._get_cache("departamentos_lista")
            if cached is not None:
                return cached

        try:
            response = requests.get(
                f"{self.base_url}/api/departamentos/lista",
                headers=self.get_headers(),
                timeout=30
            )
            if response.status_code == 200:
                data = response.json()
                self._set_cache("departamentos_lista", data)
                return data
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
            if response.status_code == 201:
                self._clear_cache("departamentos_lista")
                self._clear_cache("departamentos")
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
            if response.status_code == 200:
                self._clear_cache("departamentos_lista")
                self._clear_cache("departamentos")
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
            if response.status_code == 200:
                self._clear_cache("departamentos_lista")
                self._clear_cache("departamentos")
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Erro ao deletar departamento: {e}")
            return False

    # =====================================================
    # Cargos (CRUD)
    # =====================================================

    def get_cargos_lista(self, use_cache=True):
        """Retorna lista de nomes de cargos para combobox com cache"""
        if use_cache:
            cached = self._get_cache("cargos_lista")
            if cached is not None:
                return cached

        try:
            response = requests.get(
                f"{self.base_url}/api/cargos/lista",
                headers=self.get_headers(),
                timeout=30
            )
            if response.status_code == 200:
                data = response.json()
                self._set_cache("cargos_lista", data)
                return data
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
            if response.status_code == 201:
                self._clear_cache("cargos_lista")
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
            if response.status_code == 200:
                self._clear_cache("cargos_lista")
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
            if response.status_code == 200:
                self._clear_cache("cargos_lista")
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Erro ao deletar cargo: {e}")
            return False


    # =====================================================
    # Notificações
    # =====================================================

    def listar_notificacoes(self, status=None, prioridade=None, limit=50, offset=0):
        """Lista notificações do usuário"""
        try:
            params = {"limit": limit, "offset": offset}
            if status:
                params["status"] = status
            if prioridade:
                params["prioridade"] = prioridade

            response = requests.get(
                f"{self.base_url}/api/notificacoes",
                headers=self.get_headers(),
                params=params,
                timeout=30
            )
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            print(f"❌ Erro ao listar notificações: {e}")
            return []

    def contar_notificacoes_nao_lidas(self):
        """Retorna a quantidade de notificações não lidas"""
        try:
            response = requests.get(
                f"{self.base_url}/api/notificacoes/nao-lidas/count",
                headers=self.get_headers(),
                timeout=30
            )
            if response.status_code == 200:
                return response.json().get("count", 0)
            return 0
        except Exception as e:
            print(f"❌ Erro ao contar notificações: {e}")
            return 0

    def marcar_notificacao_lida(self, notificacao_id):
        """Marca uma notificação como lida"""
        try:
            response = requests.put(
                f"{self.base_url}/api/notificacoes/{notificacao_id}/marcar-lida",
                headers=self.get_headers(),
                timeout=30
            )
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Erro ao marcar notificação: {e}")
            return False

    def marcar_todas_notificacoes_lidas(self):
        """Marca todas as notificações como lidas"""
        try:
            response = requests.put(
                f"{self.base_url}/api/notificacoes/marcar-todas-lidas",
                headers=self.get_headers(),
                timeout=30
            )
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Erro ao marcar todas notificações: {e}")
            return False

    def deletar_notificacao(self, notificacao_id):
        """Deleta uma notificação"""
        try:
            response = requests.delete(
                f"{self.base_url}/api/notificacoes/{notificacao_id}",
                headers=self.get_headers(),
                timeout=30
            )
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Erro ao deletar notificação: {e}")
            return False

    def criar_notificacao_backend(self, notificacao):
        """Cria uma nova notificação no backend"""
        try:
            response = requests.post(
                f"{self.base_url}/api/notificacoes",
                json=notificacao,
                headers=self.get_headers(),
                timeout=30
            )
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"❌ Erro ao criar notificação: {e}")
            return None


# Instância global do cliente
api_client = APIClient()
