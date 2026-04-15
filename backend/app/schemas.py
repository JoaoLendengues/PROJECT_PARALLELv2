from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any
from datetime import datetime, date

# Schemas para Material
class MaterialBase(BaseModel):
    nome: str
    descricao: Optional[str] = None
    quantidade: int = 0
    categoria: Optional[str] = None
    empresa: str
    status: str = 'ativo'

class MaterialCreate(MaterialBase):
    pass

class MaterialUpdate(BaseModel):
    nome: Optional[str] = None
    descricao: Optional[str] = None
    quantidade: Optional[int] = None
    categoria: Optional[str] = None
    empresa: Optional[str] = None
    status: Optional[str] = None

class MaterialResponse(MaterialBase):
    id: int
    criado_em: datetime
    atualizado_em: datetime

    class Config:
        from_attributes = True
        


class MaquinaBase(BaseModel):
    nome: str
    modelo: Optional[str] = None
    empresa: str
    departamento: Optional[str] = None
    status: str = 'ativo'
    observacoes: Optional[str] = None
    mac_address: Optional[str] = None
    ip_address: Optional[str] = None

class MaquinaCreate(MaquinaBase):
    pass

class MaquinaUpdate(BaseModel):
    nome: Optional[str] = None
    modelo: Optional[str] = None
    empresa: Optional[str] = None
    departamento: Optional[str] = None
    status: Optional[str] = None
    observacoes: Optional[str] = None
    mac_address: Optional[str] = None
    ip_address: Optional[str] = None

class MaquinaResponse(MaquinaBase):
    id: int
    criado_em: datetime
    atualizado_em: datetime

    class Config:
        from_attributes = True


class ManutencaoBase(BaseModel):
    maquina_id: int
    tipo: str # preventiva, corretiva, emergencial
    descricao: str
    data_inicio: date
    data_fim: Optional[date] = None
    data_proxima: Optional[date] = None
    responsavel: Optional[str] = None
    status: str = "pedente" # pedente, andamento, concluida,cancelada
    custo: Optional[float] = None
    observacoes: Optional[str] = None


class ManutencaoCreate(ManutencaoBase):
    pass


class ManutencaoUpdate(BaseModel):
    tipo: Optional[str] = None
    descricao: Optional[str] = None
    data_fim: Optional[date] = None
    data_proxima: Optional[date] = None
    responsavel: Optional[str] = None
    status: Optional[str] = None 
    custo: Optional[float] = None
    observaçoes: Optional[str] = None


class ManutencaoResponse(ManutencaoBase):
    id: int
    criado_em: datetime
    atualizado_em: datetime
    maquina_nome: Optional[str] = None # Para exibir o nome da máquina

    class Config:
        from_attributes = True



class MovimentacaoBase(BaseModel):
    material_id: int
    tipo: str # entrada, saida
    quantidade: int
    empresa: str
    destinatario: Optional[str] = None
    observacao: Optional[str] = None
    assinatura_digital: Optional[str] = None
    ip_origem: Optional[str] = None


class MovimentacaoCreate(MovimentacaoBase):
    pass


class MovimentacaoUpdate(BaseModel):
    destinatario: Optional[str] = None
    observacao: Optional[str] = None
    assinatura_digital: Optional[str] = None


class MovimentacaoReponse(MovimentacaoBase):
    id: int
    usuario_id: Optional[int] = None
    data_hora: datetime
    material_nome: Optional[str] = None
    usuario_nome: Optional[str] = None


    class Config:
        from_attributes = True
 
    
class PedidoBase(BaseModel):
    material_id: int
    quantidade: int
    solicitante: str
    empresa: str
    departamento: Optional[str] = None
    data_conclusao: Optional[date] = None
    status: str = 'pendente'
    observacao: Optional[str] = None

class PedidoCreate(BaseModel):
    material_id: Optional[int] = None  # Pode ser None
    material_nome: Optional[str] = None  # Nome do material não cadastrado
    quantidade: int
    solicitante: str
    empresa: str
    departamento: Optional[str] = None
    status: str = "pendente"
    observacao: Optional[str] = None

class PedidoUpdate(BaseModel):
    quantidade: Optional[int] = None
    solicitante: Optional[str] = None
    departamento: Optional[str] = None
    data_conclusao: Optional[date] = None
    status: Optional[str] = None
    observacao: Optional[str] = None

class PedidoResponse(PedidoBase):
    id: int
    data_solicitacao: date
    criado_em: datetime
    material_nome: Optional[str] = None

    class Config:
        from_attributes = True

# =====================================================
# Schemas para Usuários do Sistema (login)
# =====================================================

class UsuarioSistemaBase(BaseModel):
    codigo: str
    nome: str
    cargo: str
    empresa: str
    nivel_acesso: str = 'usuario' # admin, gerente, usuario
    ativo: bool = True

class UsuarioSistemaCreate(UsuarioSistemaBase):
    senha: str # Senha em texto plano, será hasheada

class UsuarioSistemaUpdate(BaseModel):
    nome: Optional[str] = None
    cargo: Optional[str] = None
    empresa: Optional[str] = None
    nivel_acesso: Optional[str] = None
    ativo: Optional[bool] = None

class UsuarioSistemaResponse(UsuarioSistemaBase):
    id: int
    primeiro_acesso: bool
    criado_em: datetime
    atualizado_em: datetime

    class Config:
        from_attributes = True


# =====================================================
# Schemas para Login
# =====================================================

class LoginRequest(BaseModel):
    codigo: str
    senha: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    usuario: UsuarioSistemaResponse

class TrocarSenhaRequest(BaseModel):
    codigo: str
    senha_atual: str
    nova_senha: str


# =====================================================
# Schemas para Colaboradores
# =====================================================

class ColaboradorBase(BaseModel):
    nome: str
    cargo: Optional[str] = None
    departamento: Optional[str] = None
    empresa: str
    ativo: bool = True

class ColaboradorCreate(ColaboradorBase):
    pass

class ColaboradorUpdate(BaseModel):
    nome: Optional[str] = None
    cargo: Optional[str] = None
    departamento: Optional[str] = None
    empresa: Optional[str] = None
    ativo: Optional[bool] = None

class ColaboradorResponse(ColaboradorBase):
    id: int
    criado_em: datetime
    atualizado_em: datetime

    class Config:
        from_attributes = True
        

# =====================================================
# Schemas para Demandas
# =====================================================

class DemandaBase(BaseModel):
    titulo: str
    descricao: str
    solicitante: str
    departamento: Optional[str] = None
    empresa: str
    prioridade: str = "media"
    urgencia: str = "media"
    status: str = "aberto"
    data_prevista: Optional[date] = None
    responsavel: Optional[str] = None
    observacao: Optional[str] = None


class DemandaCreate(DemandaBase):
    pass


class DemandaUpdate(BaseModel):
    titulo: Optional[str] = None
    descricao: Optional[str] = None
    prioridade: Optional[str] = None
    urgencia: Optional[str] = None
    status: Optional[str] = None
    data_prevista: Optional[date] = None
    responsavel: Optional[str] = None
    observacao: Optional[str] = None


class DemandaResponse(DemandaBase):
    id: int
    data_abertura: datetime
    data_conclusao: Optional[date] = None
    criado_em: datetime
    atualizado_em: datetime

    class Config:
        from_attributes = True
        

# =====================================================
# Schemas para Departamentos
# =====================================================

class DepartamentoBase(BaseModel):
    nome: str
    descricao: Optional[str] = None
    ativo: bool = True

class DepartamentoCreate(DepartamentoBase):
    pass

class DepartamentoUpdate(BaseModel):
    nome: Optional[str] = None
    descricao: Optional[str] = None
    ativo: Optional[bool] = None

class DepartamentoResponse(DepartamentoBase):
    id: int
    criado_em: datetime
    atualizado_em: datetime

    class Config:
        from_attributes = True


# =====================================================
# Schemas para Cargos
# =====================================================

class CargoBase(BaseModel):
    nome: str
    descricao: Optional[str] = None
    ativo: bool = True

class CargoCreate(CargoBase):
    pass

class CargoUpdate(BaseModel):
    nome: Optional[str] = None
    descricao: Optional[str] = None
    ativo: Optional[bool] = None

class CargoResponse(CargoBase):
    id: int
    criado_em: datetime
    atualizado_em: datetime

    class Config:
        from_attributes = True

# =====================================================
# Schemas para Notificações
# =====================================================

class NotificacaoBase(BaseModel):
    tipo: str
    titulo: str
    mensagem: str
    prioridade: str  # 'alta', 'media', 'baixa'
    acao: Optional[str] = None
    acao_id: Optional[int] = None
    dados_extra: Optional[Dict[str, Any]] = None

class NotificacaoCreate(NotificacaoBase):
    pass

class NotificacaoUpdate(BaseModel):
    status: Optional[str] = None
    lida_em: Optional[datetime] = None

class NotificacaoResponse(NotificacaoBase):
    id: int
    usuario_id: int
    status: str
    criado_em: datetime
    lida_em: Optional[datetime] = None

    class Config:
        from_attributes = True