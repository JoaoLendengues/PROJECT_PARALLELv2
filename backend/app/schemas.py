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
        