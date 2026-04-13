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
    """Cria um novo pedido (cria material automaticamente se não existir)"""
    
    material_id = pedido.material_id
    
    # Se não tem material_id mas tem material_nome, criar ou buscar o material
    if not material_id and pedido.material_nome:
        # Verificar se material já existe
        existing = db.query(models.Material).filter(
            models.Material.nome == pedido.material_nome,
            models.Material.empresa == pedido.empresa
        ).first()
        
        if existing:
            material_id = existing.id
            print(f"📦 Material existente encontrado: {pedido.material_nome}")
        else:
            # Criar novo material
            novo_material = models.Material(
                nome=pedido.material_nome,
                descricao=f"Material solicitado em pedido",
                quantidade=0,
                categoria="Não categorizado",
                empresa=pedido.empresa,
                status="ativo"
            )
            db.add(novo_material)
            db.flush()
            material_id = novo_material.id
            print(f"✅ Material '{pedido.material_nome}' criado automaticamente com ID {material_id}")
    
    if not material_id:
        raise HTTPException(status_code=400, detail="Material não identificado")
    
    # Verificar se o material existe
    material = db.query(models.Material).filter(models.Material.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail='Material não encontrado')
    
    # Criar pedido
    novo_pedido = models.Pedido(
        material_id=material_id,
        quantidade=pedido.quantidade,
        solicitante=pedido.solicitante,
        empresa=pedido.empresa,
        departamento=pedido.departamento,
        status=pedido.status,
        observacao=pedido.observacao,
        usuario_id=usuario_id
    )
    db.add(novo_pedido)
    db.commit()
    db.refresh(novo_pedido)
    
    # Buscar o material para resposta
    material = db.query(models.Material).filter(models.Material.id == material_id).first()
    
    result = {
        **{key: getattr(novo_pedido, key) for key in novo_pedido.__dict__.keys() if not key.startswith('_')},
        'material_nome': material.nome if material else pedido.material_nome
    }
    
    print(f"✅ Pedido criado: {pedido.quantidade} x {material.nome} - Solicitante: {pedido.solicitante}")
    
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
    """Conclui um pedido de COMPRA e atualiza o estoque (ENTRADA no estoque)"""

    print(f"🔧 Concluindo pedido de COMPRA ID: {pedido_id}")
    
    # Buscar o pedido
    pedido = db.query(models.Pedido).filter(models.Pedido.id == pedido_id).first()

    if not pedido:
        print(f"❌ Pedido {pedido_id} não encontrado")
        raise HTTPException(status_code=404, detail='Pedido não encontrado')
    
    print(f"📋 Pedido: status={pedido.status}, material_id={pedido.material_id}, quantidade={pedido.quantidade}")
    
    # Verificar se o pedido está aprovado
    if pedido.status != 'aprovado':
        print(f"❌ Status inválido: {pedido.status}")
        raise HTTPException(
            status_code=400,
            detail=f'Apenas pedidos aprovados podem ser concluídos. Status atual: {pedido.status}'
        )
    
    # Buscar o material
    material = db.query(models.Material).filter(models.Material.id == pedido.material_id).first()
    if not material:
        print(f"❌ Material ID {pedido.material_id} não encontrado")
        raise HTTPException(status_code=404, detail='Material não encontrado')
    
    print(f"📦 Material: {material.nome}, Estoque atual: {material.quantidade}")
    
    # ATUALIZAR ESTOQUE (ADICIONAR - pois é um pedido de COMPRA)
    material.quantidade += pedido.quantidade
    print(f"✅ Estoque atualizado (COMPRA): {material.quantidade - pedido.quantidade} -> {material.quantidade}")
    
    # ATUALIZAR STATUS DO PEDIDO
    pedido.status = 'concluido'
    pedido.data_conclusao = date.today()
    print(f"✅ Pedido status atualizado para 'concluido'")
    
    # CRIAR MOVIMENTAÇÃO DE ENTRADA
    movimentacao = models.Movimentacao(
        material_id=pedido.material_id,
        tipo='entrada',  # <--- MUDOU para 'entrada'
        quantidade=pedido.quantidade,
        usuario_id=usuario_id,
        empresa=pedido.empresa,
        destinatario=pedido.solicitante,
        observacao=f'Pedido de compra #{pedido_id} concluído - {pedido.observacao or ""}'
    )
    db.add(movimentacao)
    print(f"✅ Movimentação de ENTRADA criada")
    
    # COMMIT NO BANCO
    db.commit()
    print(f"🎉 Pedido de compra {pedido_id} concluído com sucesso! +{pedido.quantidade} unidades adicionadas ao estoque.")
    
    return {
        'message': 'Pedido de compra concluído com sucesso! Estoque atualizado.',
        'pedido_id': pedido_id,
        'material': material.nome,
        'quantidade_adicionada': pedido.quantidade,
        'novo_estoque': material.quantidade
    }


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


@router.get('/status/lista')
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
