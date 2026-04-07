from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from app.database import get_db
from app import models, schemas, auth

router = APIRouter(prefix='/api/colaboradores', tags=['Colaboradores'])


@router.get('/', response_model=List[schemas.ColaboradorResponse])
def listar_colaboradores(
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(auth.get_current_user),
    ativo: Optional[bool] = Query(None, description="Filtrar por ativo"),
    empresa: Optional[str] = Query(None, description="Filtrar por empresa"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    """Lista todos os colaboradores"""
    
    query = db.query(models.Colaborador)
    
    if ativo is not None:
        query = query.filter(models.Colaborador.ativo == ativo)
    
    if empresa:
        query = query.filter(models.Colaborador.empresa == empresa)
    
    colaboradores = query.order_by(models.Colaborador.nome).offset(offset).limit(limit).all()
    
    return colaboradores


@router.get('/{colaborador_id}', response_model=schemas.ColaboradorResponse)
def obter_colaborador(
    colaborador_id: int,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(auth.get_current_user)
):
    """Obtém um colaborador específico"""
    
    colaborador = db.query(models.Colaborador).filter(models.Colaborador.id == colaborador_id).first()
    
    if not colaborador:
        raise HTTPException(status_code=404, detail="Colaborador não encontrado")
    
    return colaborador


@router.post('/', response_model=schemas.ColaboradorResponse, status_code=201)
def criar_colaborador(
    colaborador: schemas.ColaboradorCreate,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(auth.get_current_user)
):
    """Cria um novo colaborador"""
    
    novo_colaborador = models.Colaborador(**colaborador.model_dump())
    db.add(novo_colaborador)
    db.commit()
    db.refresh(novo_colaborador)
    
    return novo_colaborador


@router.put('/{colaborador_id}', response_model=schemas.ColaboradorResponse)
def atualizar_colaborador(
    colaborador_id: int,
    colaborador: schemas.ColaboradorUpdate,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(auth.get_current_user)
):
    """Atualiza um colaborador"""
    
    colaborador_existente = db.query(models.Colaborador).filter(models.Colaborador.id == colaborador_id).first()
    
    if not colaborador_existente:
        raise HTTPException(status_code=404, detail="Colaborador não encontrado")
    
    update_data = colaborador.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(colaborador_existente, field, value)
    
    db.commit()
    db.refresh(colaborador_existente)
    
    return colaborador_existente


@router.delete('/{colaborador_id}')
def deletar_colaborador(
    colaborador_id: int,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(auth.get_current_user)
):
    """Remove um colaborador"""
    
    colaborador = db.query(models.Colaborador).filter(models.Colaborador.id == colaborador_id).first()
    
    if not colaborador:
        raise HTTPException(status_code=404, detail="Colaborador não encontrado")
    
    db.delete(colaborador)
    db.commit()
    
    return {"message": "Colaborador deletado com sucesso"}
