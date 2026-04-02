from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import date
from app.database import get_db
from app import models, schemas

router = APIRouter(prefix='/api/pedidos', tags=['Pedidos'])


@router.get('/', response_model=List[schemas.PedidoResponse])
def listar_pedidos(
    db: Session = Depends(get_db),
    status: Optional[str] = Query(None, description='Filtrar por status'),
    solicitante: Optional[str] = Query(None, description='Filtrar por solicitante'),
    empresa: Optional[str] = Query(None, description='Filtrar por empresa'),
    departamento: Optional[str] = Query(None, description='Filtrar por departamento'),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    """Lista todos os pedidos com filtros opcionais"""
    print(f'📋 GET /api/pedidos - status: {status}, empresa: {empresa}')

    query = db.query(models.Pedido)

    if status:
        query = query.filter(models.Pedido.status == status)

    if solicitante:
        query = query.filter(models.Pedido.solicitante.ilike(f'%{solicitante}%'))

    if empresa:
        query = query.filter(models.Pedido.empresa == empresa)

    if departamento:
        query = query.filter(models.Pedido.departamento == departamento)

    pedidos = query.order_by(models.Pedido.data_solicitacao.desc()).offset(offset).limit(limit).all()

    # Adicionar nome do material
    result = []
    for pedido in pedidos:
        material = db.query(models.Material).filter(models.Material.id == pedido.material_id).first()
        result.append({
            **{key: getattr(pedido, key) for key in pedido.__dict__.keys() if not key.startswith('_')},
            'material_nome': material.nome if material else None
        })

    print(f'📦 Encontrados {len(result)} pedidos')

    return result


@router.get('/{pedido_id}', response_model=schemas.PedidoResponse)
def obter_pedido(pedido_id: int, db: Session = Depends(get_db)):
    """Obtém um pedido específico pelo ID"""
    pedido = db.query(models.Pedido).filter(models.Pedido.id == pedido_id).first()

    if not pedido:
        raise HTTPException(status_code=404, detail='Pedido não encontrado')
    
    material = db.query(models.Material).filter(models.Material.id == pedido.material_id).first()

    result = {
        **{key: getattr(pedido, key) for key in pedido.__dict__.keys() if not key.startswith('_')},
        'material_nome': material.nome if material else None
    }

    return result


@router.post('/', response_model=schemas.PedidoResponse, status_code=201)
def criar_pedido(
    pedido: schemas.PedidoCreate,
    db: Session = Depends(get_db),
    usuario_id: int = Query(1, description='ID do usuário logado')
):
    """Cria um novo pedido"""

    # Verificar se o material existe
    material = db.query(models.Material).filter(models.Material.id == pedido.material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail='Material não encontrado')
    
    # Verificar se tem estoque suficiente para pedido pendente?
    # Por ora, apenas registra o pedido sem verificar estoque

    # Criar pedido
    novo_pedido = models.Pedido(
        **pedido.model_dump(),
        usuario_id=usuario_id
    )
    db.add(novo_pedido)
    db.commit()
    db.refresh(novo_pedido)

    print(f'✅ Pedido criado: {pedido.quantidade} x {material.nome} - Solicitante: {pedido.solicitante}')

    result = {
        **{key: getattr(novo_pedido, key) for key in novo_pedido.__dict__.keys() if not key.startswith('_')},
        'material_nome': material.nome
    }

    return result


@router.put('/{pedido_id}', response_model=schemas.PedidoResponse)
def atualizar_pedido(
    pedido_id: int, 
    pedido: schemas.PedidoUpdate,
    db: Session = Depends(get_db)
):
    """Atualiza um pedido existente"""

    pedido_existente = db.query(models.Pedido).filter(models.Pedido.id == pedido_id).first()

    if not pedido_existente:
        raise HTTPException(status_code=404, detail='Pedido não encontrado')
    
    update_data = pedido.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(pedido_existente, field, value)

    db.commit()
    db.refresh(pedido_existente)

    material = db.query(models.Material).filter(models.Material.id == pedido_existente.material_id).first()

    result = {
        **{key: getattr(pedido_existente, key) for key in pedido_existente.__dict__.keys() if not key.startswith('_')},
        'material_nome': material.nome if material else None
    }

    return result


@router.put('/{pedido_id}/aprovar')
def aprovar_pedido(
    pedido_id: int,
    db: Session = Depends(get_db)
):
    """Aprova um pedido (altera status para 'aprovado')"""
    pedido = db.query(models.Pedido).filter(models.Pedido.id == pedido_id).first()

    if not pedido:
        raise HTTPException(status_code=404, detail='Pedido não encontrado')
    
    if pedido.status != 'pendente':
        raise HTTPException(status_code=400, detail='Apenas pedidos pendentes podem ser aprovados')
    
    pedido.status = 'aprovado'
    db.commit()

    return {'message': 'Pedido aprovado com sucesso', 'pedido_id': pedido_id}


@router.put('/{pedido_id}/concluir')
def concluir_pedido(
    pedido_id: int,
    db: Session = Depends(get_db),
    usuario_id: int = Query(1, description='ID do usuário logado')
):
    """Conclui um pedido e atualiza o estoque (saída do material)"""

    pedido = db.query(models.Pedido).filter(models.Pedido.id == pedido_id).first()

    if not pedido:
        raise HTTPException(status_code=404, detail='Pedido não encontrado')
    
    if pedido.status != 'aprovado':
        raise HTTPException(status_code=400, detail='Apenas pedidos aprovados podem ser concluídos')
    
    # Verificar estoque
    material = db.query(models.Material).filter(models.Material.id == pedido.material_id).first()
    if material.quantidade < pedido.quantidade:
        raise HTTPException(
            status_code=400,
            detail=f'Estoque insuficiente. Disponível {material.quantidade}'
        )
    
    # Atualizar status do pedido
    pedido.status = 'concluido'
    pedido.data_conclusao = date.today()

    # Criar movimentação de saída
    movimentacao = models.Movimentacao(
        material_id=pedido.material_id,
        tipo='saida',
        quantidade=pedido.quantidade,
        usuario_id=usuario_id,
        empresa=pedido.empresa,
        destinatario=pedido.solicitante,
        observacao=f'Pedido #{pedido_id} - {pedido.observacao}'
    )
    db.add(movimentacao)

    db.commit()

    print(f'✅ Pedido {pedido_id} concluído. Estoque atualizado: {material.nome} -> {material.quantidade - pedido.quantidade}')

    return {'message': 'Pedido concluído com sucesso', 'pedido_id': pedido_id}


@router.put('/{pedido_id}/cancelar')
def cancelar_pedido(
    pedido_id: int,
    db: Session = Depends(get_db)
):
    """Cancela um pedido"""
    pedido = db.query(models.Pedido).filter(models.Pedido.id == pedido_id).first()

    if not pedido:
        raise HTTPException(status_code=404, detail='Pedido não encontrado')
    
    if pedido.status not in ['pendente', 'aprovado']:
        raise HTTPException(status_code=400, detail='Apenas pedidos pendentes ou aprovados podem ser cancelados')
    
    pedido.status = 'cancelado'
    db.commit()

    return {'message': 'Pedido cancelado com sucesso', 'pedido_id': pedido_id}


@router.delete('/{pedido_id}')
def deletar_pedido(
    pedido_id: int,
    db: Session = Depends(get_db)
):
    """Remove um pedido"""
    pedido = db.query(models.Pedido).filter(models.Pedido.id == pedido_id).first()

    if not pedido:
        raise HTTPException(status_code=404, detail='Pedido não encontrado')
    
    db.delete(pedido)
    db.commit()

    return {'message': 'Pedido deletado com sucesso'}


@router.get('/status/lsta')
def listar_status():
    """Lista todos os status de pedido"""
    return {
        'status': [
            {'value': 'pendente', 'label': 'Pendente', 'color': '#f4a261'},
            {'value': 'aprovado', 'label': 'Aprovado', 'color': '#2a9d8f'},
            {'value': 'concluido', 'label': 'Concluído', 'color': '#2c7da0'},
            {'value': 'cancelado', 'label': 'Cancelado', 'color': '#e76f51'}
        ]
    }
