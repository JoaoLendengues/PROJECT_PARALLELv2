from pydantic import BaseModel
from datetime import datetime
from typing import Optional

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
