from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
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


@router.get('/{manutencao_id}', response_model=schemas.ManutencaoResponse)
def obter_manutencao(manutencao_id: int, db: Session = Depends(get_db)):
    """Obtém uma manutenção específica pelo ID"""
    manutencao = db.query(models.Manutencao).filter(models.Manutencao.id == manutencao_id).first()

    if not manutencao:
        raise HTTPException(status_code=404, detail='Manutenção não encontrada')
    
    maquina = db.query(models.Maquina).filter(models.Maquina.id == manutencao_id).first()
    result = {
        **{key: getattr(manutencao, key) for key in manutencao.__dict__.keys() if not key.startswith('_')},
        'maquina_nome': maquina.nome if maquina else None
    }

    return result

@router.post('/', response_model=schemas.ManutencaoResponse, status_code=201)
def criar_manutencao(
    manutencao: schemas.ManutencaoCreate,
    db: Session = Depends(get_db)
):
    """Cria uma nova manutenção"""
    
    # Verificar se a máquina existe
    maquina = db.query(models.Maquina).filter(models.Maquina.id == manutencao.maquina_id).first()
    if not maquina:
        raise HTTPException(status_code=404, detail='Máquina não encontrada')
    
    # Criar nova manutenção
    nova_manutencao = models.Manutencao(**manutencao.model_dump())
    db.add(nova_manutencao)
    
    # Atualizar status da máquina - USANDO update DIRETO NO BANCO
    db.execute(
        text("UPDATE maquinas SET status = :status WHERE id = :id"),
        {"status": "manutencao", "id": manutencao.maquina_id}
    )
    
    db.commit()
    db.refresh(nova_manutencao)
    
    print(f"✅ Manutenção criada para máquina ID: {manutencao.maquina_id} (ID: {nova_manutencao.id})")
    
    # Buscar o nome da máquina para resposta
    maquina_atualizada = db.query(models.Maquina).filter(models.Maquina.id == manutencao.maquina_id).first()
    maquina_nome = maquina_atualizada.nome if maquina_atualizada else "Máquina não encontrada"
    
    result = {
        **{key: getattr(nova_manutencao, key) for key in nova_manutencao.__dict__.keys() if not key.startswith('_')},
        'maquina_nome': maquina_nome
    }
    
    return result


@router.put('/{manutencao_id}', response_model=schemas.ManutencaoResponse)
def atualizar_manutencao(
    manutencao_id: int,
    manutencao: schemas.ManutencaoUpdate,
    db: Session = Depends(get_db)
):
    """Atualiza uma manutenção existente"""

    manutencao_existente = db.query(models.Manutencao).filter(models.Manutencao.id == manutencao_id).first()

    if not manutencao_existente:
        raise HTTPException(status_code=404, detail='Manutenção não encontrada')
    
    update_data = manutencao.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(manutencao_existente, field, value)

    db.commit()
    db.refresh(manutencao_existente)

    maquina = db.query(models.Maquina).filter(models.Maquina.id == manutencao_existente.maquina_id).first()

    result = {
        **{key: getattr(manutencao_existente, key) for key in manutencao_existente.__dict__.keys() if not key.startswith('_')},
        'maquina_nome': maquina.nome if maquina else None
    }

    return result

@router.put('/{manutencao_id}/concluir')
def concluir_manutencao(
    manutencao_id: int,
    db: Session = Depends(get_db)
):
    """Conclui uma manutenção e atualiza o status da máquina"""
    
    manutencao = db.query(models.Manutencao).filter(models.Manutencao.id == manutencao_id).first()

    if not manutencao:
        raise HTTPException(status_code=404, detail='Manutenção não encontrada')
    
    if manutencao.status == 'concluida':
        raise HTTPException(status_code=400, detail='Manutenção já está concluída')
    
    # Atualizar status da manutenção
    manutencao.status = 'concluida'
    manutencao.data_fim = date.today()
    db.commit()

    # Atualizar status da máquina para "ativo"
    maquina = db.query(models.Maquina).filter(models.Maquina.id == manutencao.maquina_id).first()
    if maquina:
        maquina.status = 'ativo'
        db.commit()

    print(f'✅ Manutenção {manutencao_id} concluída. Máquina {maquina.nome} está ativa novamente')

    return {'message': 'Manutenção concluída com sucesso', 'manutencao_id': manutencao_id}


@router.delete('/{manutencao_id}')
def deletar_manutencao(
    manutencao_id: int,
    db: Session = Depends(get_db)
):
    """Remove uma manutenção"""

    manutencao = db.query(models.Manutencao).filter(models.Manutencao.id == manutencao_id).first()

    if not manutencao:
        raise HTTPException(status_code=404, detail='Manutenção não encontrada')
    
    db.delete(manutencao)
    db.commit()

    return {'message': 'Manutenção deletada com sucesso'}


@router.get('/tipos/lista')
def listar_tipos():
    """Lista todos os tipos de manutenção"""
    return {'tipos': ['preventiva', 'corretiva', 'emergencial']}


@router.get('/status/lista')
def listar_status():
    """Lista todos os status de manutenção"""
    return {'status': ['pendente', 'andamento', 'concluida', 'cancelada']}

