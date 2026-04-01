from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import date
from app.database import get_db
from app import models, schemas

router = APIRouter(prefix='/api/manutencoes', tags=['Manutenções'])


@router.get('/', response_model=List[schemas.ManutencaoResponse])
def listar_manutencoes(
    db: Session = Depends(get_db),
    status: Optional[str] = Query(None, description='Filtrar por status'),
    maquina_id: Optional[int] = Query(None, description='Filtrar por máquina'),
    tipo: Optional[str] = Query(None, description='Filtrar por tipo'),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    """Lista todas as manutenções com filtros opcionais"""
    print(f'🔎 GET /api/manutencoes - status: {status}, maquina_id: {maquina_id}')

    query = db.query(models.Manutencao)

    if status:
        query = query.filter(models.Manutencao.status == status)

    if maquina_id:
        query = query.filter(models.Manutencao.maquina_id == maquina_id)

    if tipo:
        query = query.filter(models.Manutencao.tipo == tipo)

    manutencoes = query.order_by(models.Manutencao.data_inicio.desc()).offset(offset).limit(limit).all()

    # Adicionar o nome da máquina para cada manutenção
    result = []
    for manut in manutencoes:
        maquina = db.query(models.Maquina).filter(models.Maquina.id == manut.maquina_id).first()
        manut_dict = {
            **{key: getattr(manut, key) for key in manut.__dict__.keys() if not key.startswith('_')},
            'maquina_nome': maquina.nome if maquina else None
        }
        result.append(manut_dict)

    print(f'🔧 Encontradas {len(result)} manutenções')

    return result


@router.get('/{manutencao_id}', response_model==schemas.ManutencaoResponse)

