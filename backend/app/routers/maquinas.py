from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from app.database import get_db
from app import models, schemas

router = APIRouter(prefix='/api/maquinas', tags=['Máquinas'])


@router.get('/', response_model=List[schemas.MaquinaResponse])
def listar_maquinas(
    db: Session = Depends(get_db),
    search: Optional[str] = Query(None, description='Termo de busca'),
    empresa: Optional[str] = Query(None, description='Filtrar por empresa'),
    departamento: Optional[str] = Query(None, description='Filtrar por departamento'),
    status: Optional[str] = Query('ativo', description='Filtrar por status'),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    """Lista todas as máquinas com filtros opcionais"""
    print(f'🔎 GET /api/maquinas - status filter: {status}')

    query = db.query(models.Maquina)

    if search:
        query = query.filter(
            (models.Maquina.nome.ilike(f'%{search}%')) |
            (models.Maquina.modelo.ilike(f'%{search}%'))
        )

    if empresa:
        query = query.filter(models.Maquina.empresa == empresa)

    if departamento:
        query = query.filter(models.Maquina.departamento == departamento)

    if status:
        query = query.filter(models.Maquina.status == status)

    maquinas = query.order_by(models.Maquina.nome).offset(offset).limit(limit).all()

    print(f'🖥️ Encontradas {len(maquinas)} máquinas')

    return maquinas


@router.get('/{maquina_id}', response_model=schemas.MaquinaResponse)
def obter_maquina(maquina_id: int, db: Session = Depends(get_db)):
    """Obtém uma máquina específica pelo ID"""
    maquina = db.query(models.Maquina).filter(models.Maquina.id == maquina_id).first()

    if not maquina:
        raise HTTPException(status_code=404, detail='Máquina não encontrada')
    
    return maquina


@router.post('/', response_model=schemas.MaquinaResponse, status_code=201)
def criar_maquina(
    maquina: schemas.MaquinaCreate,
    db: Session = Depends(get_db)
):
    """Cria uma nova máquina"""

    # Verificar se já existe máquina com mesmo nome e empresa
    existing = db.query(models.Maquina).filter(
        models.Maquina.nome == maquina.nome,
        models.Maquina.empresa == maquina.empresa
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail='Já existe uma máquina com este nome nesta empresa')
    
    # Criar nova máquina
    nova_maquina = models.Maquina(**maquina.model_dump())
    db.add(nova_maquina)
    db.commit()
    db.refresh(nova_maquina)

    print(f'✅ Máquina criada: {nova_maquina.nome} (ID: {nova_maquina.id})')

    return nova_maquina


@router.put('/{maquina_id}', response_model=schemas.MaquinaResponse)
def atualizar_maquina(
    maquina_id: int,
    maquina: schemas.MaquinaUpdate,
    db: Session = Depends(get_db)
):
    """Atualiza uma máquina existente"""

    maquina_existente = db.query(models.Maquina).filter(models.Maquina.id == maquina_id). first()

    if not maquina_existente:
        raise HTTPException(status_code=404, detail='Máquina não encontrada')
    
    update_data = maquina.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(maquina_existente, field, value)

    db.commit()
    db.refresh(maquina_existente)

    return maquina_existente


@router.delete('/{maquina_id}')
def deletar_maquina(
    maquina_id: int,
    db: Session = Depends(get_db)
):
    """Remove uma máquina (apenas se não tiver manutenções)"""

    maquina = db.query(models.Maquina).filter(models.Maquina.id == maquina_id).first()

    if not maquina:
        raise HTTPException(status_code=404, detail='Máquina não encontrada')
    
    # Verificar se existem manutenções
    manutencoes = db.query(models.Manutencao).filter(
        models.Manutencao.maquina_id == maquina_id
    ).first()

    if manutencoes:
        raise HTTPException(
            status_code=400,
            detail='Não é possível deletar máquina com manutenções registradas'
        )
    
    db.delete(maquina)
    db.commit()

    return {'message': 'Máquina deletada com sucesso'}


@router.get('/departamento/lista')
def listar_departamentos(db: Session = Depends(get_db)):
    """Lista todos os departamentos com máquinas"""

    departamentos = db.query(models.Maquina.departamento).distinct().filter(
        models.Maquina.departamento.isnot(None),
        models.Maquina.departamento != ''
    ).all()

    return {'departamentos': [dept[0] for dept in departamentos if dept[0]]}

# @router.patch('/{maquina_id}/status')
# def alterar_status_maquina(
#     maquina_id: int,
#     novo_status: str,
#     db: Session = Depends(get_db)
# ):
#     """Altera o status de uma máquina"""
#     maquina = db.query(models.Maquina).filter(models.Maquina.id == maquina_id).first()

#     if not maquina:
#         raise HTTPException(status_code=404, detail='Máquina não encontrada')
    
#     # Validar status
#     status_validos = ['ativo', 'manutencao', 'inativo']
#     if novo_status not in status_validos:
#         raise HTTPException(status_code=400, detail=f'status inválido. Use: {status_validos}')
    
#     maquina.status = novo_status
#     db.commit()
#     db.refresh(maquina)

#     return {'message': f'Status alterado para {novo_status}', 'maquina': maquina}