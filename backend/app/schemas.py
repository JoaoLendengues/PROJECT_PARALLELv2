from pydantic import BaseModel
from datetime import datetime
from typing import Optional
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

class MaquinaCreate(MaquinaBase):
    pass

class MaquinaUpdate(BaseModel):
    nome: Optional[str] = None
    modelo: Optional[str] = None
    empresa: Optional[str] = None
    departamento: Optional[str] = None
    status: Optional[str] = None
    observacoes: Optional[str] = None

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
 
    

