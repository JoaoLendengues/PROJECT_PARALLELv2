from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from app.database import get_db
from app import models, schemas, auth

router = APIRouter(prefix='/api/cargos', tags=['Cargos'])


@router.get('/', response_model=List[schemas.CargoResponse])
def listar_cargos(
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(auth.get_current_user),
    ativo: Optional[bool] = Query(True, description="Filtrar por ativo"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    """Lista todos os cargos"""
    
    query = db.query(models.Cargo)
    
    if ativo is not None:
        query = query.filter(models.Cargo.ativo == ativo)
    
    cargos = query.order_by(models.Cargo.nome).offset(offset).limit(limit).all()
    
    return cargos


@router.get('/lista')
def get_lista_cargos(
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(auth.get_current_user)
):
    """Retorna apenas os nomes dos cargos para combobox"""
    
    cargos = db.query(models.Cargo.nome).filter(
        models.Cargo.ativo == True
    ).order_by(models.Cargo.nome).all()
    
    return [c[0] for c in cargos]


@router.post('/', response_model=schemas.CargoResponse, status_code=201)
def criar_cargo(
    cargo: schemas.CargoCreate,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(auth.verificar_admin)
):
    """Cria um novo cargo (apenas admin)"""
    
    existing = db.query(models.Cargo).filter(
        models.Cargo.nome == cargo.nome
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Cargo já existe")
    
    novo_cargo = models.Cargo(**cargo.model_dump())
    db.add(novo_cargo)
    db.commit()
    db.refresh(novo_cargo)
    
    return novo_cargo


@router.put('/{cargo_id}', response_model=schemas.CargoResponse)
def atualizar_cargo(
    cargo_id: int,
    cargo: schemas.CargoUpdate,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(auth.verificar_admin)
):
    """Atualiza um cargo (apenas admin)"""
    
    cargo_existente = db.query(models.Cargo).filter(
        models.Cargo.id == cargo_id
    ).first()
    
    if not cargo_existente:
        raise HTTPException(status_code=404, detail="Cargo não encontrado")
    
    update_data = cargo.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(cargo_existente, field, value)
    
    db.commit()
    db.refresh(cargo_existente)
    
    return cargo_existente


@router.delete('/{cargo_id}')
def deletar_cargo(
    cargo_id: int,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(auth.verificar_admin)
):
    """Remove um cargo (apenas admin)"""
    
    cargo = db.query(models.Cargo).filter(models.Cargo.id == cargo_id).first()
    
    if not cargo:
        raise HTTPException(status_code=404, detail="Cargo não encontrado")
    
    # Verificar se está sendo usado em colaboradores ou usuários
    colaborador_uso = db.query(models.Colaborador).filter(
        models.Colaborador.cargo == cargo.nome
    ).first()
    
    usuario_uso = db.query(models.UsuarioSistema).filter(
        models.UsuarioSistema.cargo == cargo.nome
    ).first()
    
    if colaborador_uso or usuario_uso:
        raise HTTPException(
            status_code=400,
            detail="Cargo está sendo usado em colaboradores ou usuários"
        )
    
    db.delete(cargo)
    db.commit()
    
    return {"message": "Cargo deletado com sucesso"}
