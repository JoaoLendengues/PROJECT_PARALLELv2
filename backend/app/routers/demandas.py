from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import date, datetime
from app.database import get_db
from app import models, schemas, auth

router = APIRouter(prefix='/api/demandas', tags=['Demandas'])


@router.get('/', response_model=List[schemas.DemandaResponse])
def listar_demandas(
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(auth.get_current_user),
    status: Optional[str] = Query(None, description="Filtrar por status"),
    prioridade: Optional[str] = Query(None, description="Filtrar por prioridade"),
    urgencia: Optional[str] = Query(None, description="Filtrar por urgência"),
    empresa: Optional[str] = Query(None, description="Filtrar por empresa"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    """Lista todas as demandas com filtros"""
    
    query = db.query(models.Demanda)
    
    if status:
        query = query.filter(models.Demanda.status == status)
    
    if prioridade:
        query = query.filter(models.Demanda.prioridade == prioridade)
    
    if urgencia:
        query = query.filter(models.Demanda.urgencia == urgencia)
    
    if empresa:
        query = query.filter(models.Demanda.empresa == empresa)
    
    demandas = query.order_by(models.Demanda.data_abertura.desc()).offset(offset).limit(limit).all()
    
    return demandas


@router.get('/{demanda_id}', response_model=schemas.DemandaResponse)
def obter_demanda(
    demanda_id: int,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(auth.get_current_user)
):
    """Obtém uma demanda específica"""
    
    demanda = db.query(models.Demanda).filter(models.Demanda.id == demanda_id).first()
    
    if not demanda:
        raise HTTPException(status_code=404, detail="Demanda não encontrada")
    
    return demanda


@router.post('/', response_model=schemas.DemandaResponse, status_code=201)
def criar_demanda(
    demanda: schemas.DemandaCreate,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(auth.get_current_user)
):
    """Cria uma nova demanda"""
    
    nova_demanda = models.Demanda(
        **demanda.model_dump(),
        criado_por=current_user.id
    )
    db.add(nova_demanda)
    db.commit()
    db.refresh(nova_demanda)
    
    return nova_demanda


@router.put('/{demanda_id}', response_model=schemas.DemandaResponse)
def atualizar_demanda(
    demanda_id: int,
    demanda: schemas.DemandaUpdate,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(auth.get_current_user)
):
    """Atualiza uma demanda"""
    
    demanda_existente = db.query(models.Demanda).filter(models.Demanda.id == demanda_id).first()
    
    if not demanda_existente:
        raise HTTPException(status_code=404, detail="Demanda não encontrada")
    
    update_data = demanda.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(demanda_existente, field, value)
    
    db.commit()
    db.refresh(demanda_existente)
    
    return demanda_existente


@router.put('/{demanda_id}/concluir')
def concluir_demanda(
    demanda_id: int,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(auth.get_current_user)
):
    """Conclui uma demanda"""
    
    demanda = db.query(models.Demanda).filter(models.Demanda.id == demanda_id).first()
    
    if not demanda:
        raise HTTPException(status_code=404, detail="Demanda não encontrada")
    
    demanda.status = "concluido"
    demanda.data_conclusao = date.today()
    db.commit()
    
    return {"message": "Demanda concluída com sucesso"}


@router.put('/{demanda_id}/cancelar')
def cancelar_demanda(
    demanda_id: int,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(auth.get_current_user)
):
    """Cancela uma demanda"""
    
    demanda = db.query(models.Demanda).filter(models.Demanda.id == demanda_id).first()
    
    if not demanda:
        raise HTTPException(status_code=404, detail="Demanda não encontrada")
    
    demanda.status = "cancelado"
    db.commit()
    
    return {"message": "Demanda cancelada com sucesso"}


@router.delete('/{demanda_id}')
def deletar_demanda(
    demanda_id: int,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(auth.get_current_user)
):
    """Remove uma demanda"""
    
    demanda = db.query(models.Demanda).filter(models.Demanda.id == demanda_id).first()
    
    if not demanda:
        raise HTTPException(status_code=404, detail="Demanda não encontrada")
    
    db.delete(demanda)
    db.commit()
    
    return {"message": "Demanda deletada com sucesso"}


@router.get('/status/lista')
def listar_status():
    """Lista todos os status de demanda"""
    return {
        'status': [
            {'value': 'aberto', 'label': 'Aberto', 'color': '#f4a261'},
            {'value': 'andamento', 'label': 'Em Andamento', 'color': '#2a9d8f'},
            {'value': 'concluido', 'label': 'Concluído', 'color': '#2c7da0'},
            {'value': 'cancelado', 'label': 'Cancelado', 'color': '#e76f51'}
        ]
    }


@router.get('/prioridades/lista')
def listar_prioridades():
    """Lista todas as prioridades"""
    return {
        'prioridades': [
            {'value': 'alta', 'label': 'Alta', 'color': '#e76f51'},
            {'value': 'media', 'label': 'Média', 'color': '#f4a261'},
            {'value': 'baixa', 'label': 'Baixa', 'color': '#2a9d8f'}
        ]
    }


@router.get('/urgencias/lista')
def listar_urgencias():
    """Lista todas as urgências"""
    return {
        'urgencias': [
            {'value': 'alta', 'label': 'Alta', 'color': '#e76f51'},
            {'value': 'media', 'label': 'Média', 'color': '#f4a261'},
            {'value': 'baixa', 'label': 'Baixa', 'color': '#2a9d8f'}
        ]
    }
