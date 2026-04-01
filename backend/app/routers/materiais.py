from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional, List
from app.database import get_db
from app import models, schemas

router = APIRouter(prefix='/api/materiais', tags=['Materiais'])


@router.get('/', response_model=List[schemas.MaterialResponse])
def listar_materiais(
    db: Session = Depends(get_db),
    search: Optional[str] = Query(None, description='Termo de busca'),
    categoria: Optional[str] = Query(None, description='Filtrar por categoria'),
    empresa: Optional[str] = Query(None, description='Filtrar por empresa'),
    status: Optional[str] = Query('Ativo', description='Filtrar por status'),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    print("🔍 Endpoint GET /api/materiais foi chamado!")
    """Lista todos os materiais com filtros opcionais"""

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

    materiais = query.order_by(models.Material.nome).offset(offset).limit(limit).all()

    return materiais

@router.get('/{material_id}', response_model=schemas.MaterialResponse)
def obter_material(material_id: int, db: Session = Depends(get_db)):
    """Obtém um material específico pelo ID"""

    material = db.query(models.Material).filter(models.Material.id == material_id).first()

    if not material:
        raise HTTPException(status_code=404, detail='Material não encontrado')
    
    return material


@router.post('/', response_model=schemas.MaterialResponse, status_code=201)
def criar_material(
    material: schemas.MaterialCreate,
    db: Session = Depends(get_db)
):
    """Cria um novo material no estoque"""

    # Verificar se já existe material com mesmo nome
    existing = db.query(models.Material).filter(
        models.Material.nome == material.nome,
        models.Material.empresa == material.empresa
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail='Já existe um material com este nome nesta empresa')
    
    # Criar novo material
    novo_material = novo_material = models.Material(**material.model_dump())
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
    """Atualiza um material existente"""

    # Verificar se material existe
    material_existente = db.query(models.Material).filter(models.Material.id == material_id).first()

    if not material_existente:
        raise HTTPException(status_code=404, detail='Material não encontrado')
    
    # Atualizar apenas com os campos fornecidos
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
    """Remove um material (apenas se não tiver movimentações)"""

    # Verificar se material existe
    material = db.query(models.Material).filter(models.Material.id == material_id).first()

    if not material:
        raise HTTPException(status_code=404, detail='Material não encontrado')
    
    # Verificar se existem movimentações
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
    """Lista todas as categorias de materiais"""

    categorias = db.query(models.Material.categoria).distinct().filter(
        models.Material.categoria.isnot(None),
        models.Material.categoria !=''
    ).all()

    return {'categorias': [cat[0] for cat in categorias if cat[0]]}

