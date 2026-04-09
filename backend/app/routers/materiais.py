from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from app.database import get_db
from app import models, schemas

router = APIRouter(prefix='/api/materiais', tags=['Materiais'])


@router.get('/')
def listar_materiais(
    db: Session = Depends(get_db),
    search: Optional[str] = Query(None, description='Termo de busca'),
    categoria: Optional[str] = Query(None, description='Filtrar por categoria'),
    empresa: Optional[str] = Query(None, description='Filtrar por empresa'),
    status: Optional[str] = Query('ativo', description='Filtrar por status'),
    limit: int = Query(50, ge=1, le=200, description='Itens por página'),
    offset: int = Query(0, ge=0, description='Página inicial'),
    order_by: str = Query('nome', description='Ordenar por (nome, quantidade, criado_em)')
):
    """Lista materiais com paginação otimizada"""
    
    query = db.query(models.Material)

    if search:
        query = query.filter(
            (models.Material.nome.ilike(f'%{search}%')) |
            (models.Material.descricao.ilike(f'%{search}%'))
        )

    if categoria:
        query = query.filter(models.Material.categoria == categoria)

    if empresa:
        query = query.filter(models.Material.empresa == empresa)

    if status:
        query = query.filter(models.Material.status == status)
    
    # Ordenação otimizada
    if order_by == 'nome':
        query = query.order_by(models.Material.nome)
    elif order_by == 'quantidade':
        query = query.order_by(models.Material.quantidade.desc())
    elif order_by == 'criado_em':
        query = query.order_by(models.Material.criado_em.desc())
    else:
        query = query.order_by(models.Material.nome)
    
    # Total para paginação
    total = query.count()
    
    # Paginação
    materiais = query.offset(offset).limit(limit).all()
    
    return {
        "items": materiais,
        "total": total,
        "limit": limit,
        "offset": offset,
        "next_offset": offset + limit if offset + limit < total else None
    }


@router.get('/{material_id}', response_model=schemas.MaterialResponse)
def obter_material(material_id: int, db: Session = Depends(get_db)):
    material = db.query(models.Material).filter(models.Material.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail='Material não encontrado')
    return material


@router.post('/', response_model=schemas.MaterialResponse, status_code=201)
def criar_material(
    material: schemas.MaterialCreate,
    db: Session = Depends(get_db)
):
    existing = db.query(models.Material).filter(
        models.Material.nome == material.nome,
        models.Material.empresa == material.empresa
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail='Já existe um material com este nome nesta empresa')
    
    novo_material = models.Material(**material.model_dump())
    db.add(novo_material)
    db.commit()
    db.refresh(novo_material)

    return novo_material


@router.put('/{material_id}', response_model=schemas.MaterialResponse)
def atualizar_material(
    material_id: int,
    material: schemas.MaterialUpdate,
    db: Session = Depends(get_db)
):
    material_existente = db.query(models.Material).filter(models.Material.id == material_id).first()

    if not material_existente:
        raise HTTPException(status_code=404, detail='Material não encontrado')
    
    update_data = material.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(material_existente, field, value)

    db.commit()
    db.refresh(material_existente)

    return material_existente


@router.delete('/{material_id}')
def deletar_material(
    material_id: int,
    db: Session = Depends(get_db)
):
    material = db.query(models.Material).filter(models.Material.id == material_id).first()

    if not material:
        raise HTTPException(status_code=404, detail='Material não encontrado')
    
    movimentacoes = db.query(models.Movimentacao).filter(
        models.Movimentacao.material_id == material_id).first()
    
    if movimentacoes:
        raise HTTPException(
            status_code=400,
            detail='Não é possível deletar material com movimentações registradas'
        )
    
    db.delete(material)
    db.commit()

    return {'message': 'Material deletado com sucesso'}


@router.get('/categorias/lista')
def listar_categorias(db: Session = Depends(get_db)):
    categorias = db.query(models.Material.categoria).distinct().filter(
        models.Material.categoria.isnot(None),
        models.Material.categoria != ''
    ).all()
    return {'categorias': [cat[0] for cat in categorias if cat[0]]}
