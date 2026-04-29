from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from app.database import get_db
from app import models, schemas, auth

router = APIRouter(prefix='/api/departamentos', tags=['Departamentos'])


@router.get('/', response_model=List[schemas.DepartamentoResponse])
def listar_departamentos(
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(auth.get_current_user),
    ativo: Optional[bool] = Query(True, description="Filtrar por ativo"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    """Lista todos os departamentos"""
    
    query = db.query(models.Departamento)
    
    if ativo is not None:
        query = query.filter(models.Departamento.ativo == ativo)
    
    departamentos = query.order_by(models.Departamento.nome).offset(offset).limit(limit).all()
    
    return departamentos


@router.get('/lista')
def get_lista_departamentos(
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(auth.get_current_user)
):
    """Retorna apenas os nomes dos departamentos para combobox"""
    
    departamentos = db.query(models.Departamento.nome).filter(
        models.Departamento.ativo == True
    ).order_by(models.Departamento.nome).all()
    
    return [d[0] for d in departamentos]


@router.post('/', response_model=schemas.DepartamentoResponse, status_code=201)
def criar_departamento(
    departamento: schemas.DepartamentoCreate,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(auth.verificar_admin)
):
    """Cria um novo departamento (apenas admin)"""
    
    # Verificar se ja existe
    existing = db.query(models.Departamento).filter(
        models.Departamento.nome == departamento.nome
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Departamento ja existe")
    
    novo_departamento = models.Departamento(**departamento.model_dump())
    db.add(novo_departamento)
    db.commit()
    db.refresh(novo_departamento)
    
    return novo_departamento


@router.put('/{departamento_id}', response_model=schemas.DepartamentoResponse)
def atualizar_departamento(
    departamento_id: int,
    departamento: schemas.DepartamentoUpdate,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(auth.verificar_admin)
):
    """Atualiza um departamento (apenas admin)"""
    
    departamento_existente = db.query(models.Departamento).filter(
        models.Departamento.id == departamento_id
    ).first()
    
    if not departamento_existente:
        raise HTTPException(status_code=404, detail="Departamento nao encontrado")
    
    update_data = departamento.model_dump(exclude_unset=True)

    novo_nome = update_data.get("nome")
    if novo_nome is not None:
        novo_nome = novo_nome.strip()
        if not novo_nome:
            raise HTTPException(status_code=400, detail="Nome do departamento nao pode estar vazio")
        update_data["nome"] = novo_nome

    nome_anterior = departamento_existente.nome
    if novo_nome and novo_nome != nome_anterior:
        existente_com_nome = db.query(models.Departamento).filter(
            models.Departamento.nome == novo_nome,
            models.Departamento.id != departamento_id
        ).first()

        if existente_com_nome:
            raise HTTPException(status_code=400, detail="Departamento ja existe")

    for field, value in update_data.items():
        setattr(departamento_existente, field, value)

    if novo_nome and novo_nome != nome_anterior:
        db.query(models.Maquina).filter(
            models.Maquina.departamento == nome_anterior
        ).update({models.Maquina.departamento: novo_nome}, synchronize_session=False)

        db.query(models.Colaborador).filter(
            models.Colaborador.departamento == nome_anterior
        ).update({models.Colaborador.departamento: novo_nome}, synchronize_session=False)

        db.query(models.Pedido).filter(
            models.Pedido.departamento == nome_anterior
        ).update({models.Pedido.departamento: novo_nome}, synchronize_session=False)

        db.query(models.Demanda).filter(
            models.Demanda.departamento == nome_anterior
        ).update({models.Demanda.departamento: novo_nome}, synchronize_session=False)
    
    db.commit()
    db.refresh(departamento_existente)
    
    return departamento_existente


@router.delete('/{departamento_id}')
def deletar_departamento(
    departamento_id: int,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(auth.verificar_admin)
):
    """Remove um departamento (apenas admin)"""
    
    departamento = db.query(models.Departamento).filter(
        models.Departamento.id == departamento_id
    ).first()
    
    if not departamento:
        raise HTTPException(status_code=404, detail="Departamento nao encontrado")
    
    # Verificar se estÃ¡ sendo usado em mÃ¡quinas
    maquina_uso = db.query(models.Maquina).filter(
        models.Maquina.departamento == departamento.nome
    ).first()
    
    # Verificar se estÃ¡ sendo usado em colaboradores
    colaborador_uso = db.query(models.Colaborador).filter(
        models.Colaborador.departamento == departamento.nome
    ).first()

    pedido_uso = db.query(models.Pedido).filter(
        models.Pedido.departamento == departamento.nome
    ).first()

    demanda_uso = db.query(models.Demanda).filter(
        models.Demanda.departamento == departamento.nome
    ).first()
    
    if maquina_uso or colaborador_uso or pedido_uso or demanda_uso:
        raise HTTPException(
            status_code=400,
            detail="Departamento estÃ¡ sendo usado em outros registros do sistema"
        )
    
    db.delete(departamento)
    db.commit()
    
    return {"message": "Departamento deletado com sucesso"}
