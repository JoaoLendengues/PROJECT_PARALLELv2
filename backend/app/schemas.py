import unicodedata

from pydantic import BaseModel, field_validator
from typing import Optional, Dict, Any
from datetime import datetime, date


ACCESS_LEVEL_ALIASES = {
    "admin": "admin",
    "administrador": "admin",
    "gerente": "gerente",
    "gerencia": "gerente",
    "manager": "gerente",
    "usuario": "usuario",
    "comum": "usuario",
    "solicitante": "solicitante",
    "funcionario": "solicitante",
    "vendedor": "solicitante",
}


def normalize_access_level_value(value: Optional[str]) -> str:
    normalized = unicodedata.normalize("NFKD", str(value or "usuario").strip().lower())
    normalized = "".join(char for char in normalized if not unicodedata.combining(char))
    access_level = ACCESS_LEVEL_ALIASES.get(normalized)
    if access_level is None:
        raise ValueError("Nivel de acesso invalido. Use admin, gerente, usuario ou solicitante.")
    return access_level

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


class MaquinaMonitoramentoResponse(BaseModel):
    id: int
    nome: str
    empresa: str
    departamento: Optional[str] = None
    status: str
    mac_address: Optional[str] = None
    ip_address: Optional[str] = None
    alvo_monitoramento: Optional[str] = None
    monitor_status: str
    monitor_label: str
    latencia_ms: Optional[int] = None
    detalhe: Optional[str] = None
    atualizado_em: datetime


class MaquinaHeartbeatRequest(BaseModel):
    hostname: Optional[str] = None
    ip_address: Optional[str] = None
    mac_address: Optional[str] = None


class MaquinaHeartbeatResponse(BaseModel):
    matched: bool
    machine_id: Optional[int] = None
    machine_name: Optional[str] = None
    matched_by: Optional[str] = None
    heartbeat_at: datetime


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
    link_compra: Optional[str] = None

class PedidoCreate(BaseModel):
    material_id: Optional[int] = None  # Pode ser None
    material_nome: Optional[str] = None  # Nome do material não cadastrado
    quantidade: int
    solicitante: str
    empresa: str
    departamento: Optional[str] = None
    status: str = "pendente"
    observacao: Optional[str] = None
    link_compra: Optional[str] = None

class PedidoUpdate(BaseModel):
    quantidade: Optional[int] = None
    solicitante: Optional[str] = None
    departamento: Optional[str] = None
    data_conclusao: Optional[date] = None
    status: Optional[str] = None
    observacao: Optional[str] = None
    link_compra: Optional[str] = None

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
    cargo: Optional[str] = None
    empresa: str
    nivel_acesso: str = 'usuario' # admin, gerente, usuario, solicitante
    ativo: bool = True

    @field_validator("nivel_acesso")
    @classmethod
    def validate_nivel_acesso(cls, value: str) -> str:
        return normalize_access_level_value(value)

class UsuarioSistemaCreate(UsuarioSistemaBase):
    senha: str # Senha em texto plano, será hasheada

class UsuarioSistemaUpdate(BaseModel):
    nome: Optional[str] = None
    cargo: Optional[str] = None
    empresa: Optional[str] = None
    nivel_acesso: Optional[str] = None
    ativo: Optional[bool] = None

    @field_validator("nivel_acesso")
    @classmethod
    def validate_nivel_acesso(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        return normalize_access_level_value(value)

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

class LoginUserPreviewResponse(BaseModel):
    codigo: str
    nome: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    usuario: UsuarioSistemaResponse

class ConfirmarSenhaRequest(BaseModel):
    senha: str

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
    solicitante: Optional[str] = None
    departamento: Optional[str] = None
    empresa: Optional[str] = None
    prioridade: Optional[str] = None
    urgencia: Optional[str] = None
    status: Optional[str] = None
    data_prevista: Optional[date] = None
    responsavel: Optional[str] = None
    observacao: Optional[str] = None


class DemandaResponse(DemandaBase):
    id: int
    criado_por: Optional[int] = None
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
