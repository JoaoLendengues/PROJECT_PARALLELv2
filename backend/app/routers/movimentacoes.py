from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
from app.database import get_db
from app import models, schemas

router = APIRouter(prefix='/api/movimentacoes', tags=['Movimentações'])

@router.get('/', response_model=List[schemas.MovimentacaoResponse])
def listar_movimentacoes(
    db: Session = Depends(get_db),
    material_id: Optional[int] = Query(None, description='Filtrar por material'),
    tipo: Optional[str] = Query(None, description='Filtrar por tipo (entrada/saída)'),
    empresa: Optional[int] = Query(None, description='Filtrar por empresa'),
    data_inicio: Optional[int] = Query(None, description='Data inicial (YYYY-MM-DD)'),
    data_fim: Optional[int] = Query(None, description='Data final (YYYY-MM-DD)'),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    """Lista todas as movimentações com filtros opcionais"""
    print(f'🔎 GET api/movimentacoes - tipo: {tipo}, empresa: {empresa}')

    query = db.query(models.Movimentacao)

    if material_id:
        query = query.filter(models.Movimentacao.material_id == material_id)

    if tipo:
        query = query.filter(models.Movimentacao.tipo == tipo)

    if empresa:
        query = query.filter(models.Movimentacao.empresa == empresa)

    if data_inicio:
        query = query.filter(models.Movimentacao.data_hora >= data_inicio)

    if data_fim:
        query = query.filter(models.Movimentacao.data_hora <= f'{data_fim} 23:59:59')

    movimentacoes = query.order_by(models.Movimentacao.data_hora.desc()).offset(offset).limit(limit).all()

    