from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
from app.database import get_db
from app import models, schemas, auth

router = APIRouter(prefix='/api/movimentacoes', tags=['Movimentações'])

@router.get('/', response_model=List[schemas.MovimentacaoReponse])
def listar_movimentacoes(
    db: Session = Depends(get_db),
    material_id: Optional[int] = Query(None, description='Filtrar por material'),
    tipo: Optional[str] = Query(None, description='Filtrar por tipo (entrada/saída)'),
    empresa: Optional[int] = Query(None, description='Filtrar por empresa'),
    data_inicio: Optional[int] = Query(None, description='Data inicial (YYYY-MM-DD)'),
    data_fim: Optional[int] = Query(None, description='Data final (YYYY-MM-DD)'),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    """Lista todas as movimentações com filtros opcionais"""
    print(f'🔎 GET api/movimentacoes - tipo: {tipo}, empresa: {empresa}')

    query = db.query(models.Movimentacao)

    if material_id:
        query = query.filter(models.Movimentacao.material_id == material_id)

    if tipo:
        query = query.filter(models.Movimentacao.tipo == tipo)

    if empresa:
        query = query.filter(models.Movimentacao.empresa == empresa)

    if data_inicio:
        query = query.filter(models.Movimentacao.data_hora >= data_inicio)

    if data_fim:
        query = query.filter(models.Movimentacao.data_hora <= f'{data_fim} 23:59:59')

    movimentacoes = query.order_by(models.Movimentacao.data_hora.desc()).offset(offset).limit(limit).all()

    # Adicionar nome do material e usuário
    result = []
    for mov in movimentacoes:
        material = db.query(models.Material).filter(models.Material.id == mov.material_id).first()
        usuario = db.query(models.Usuario).filter(models.Usuario.id == mov.usuario_id).first() if mov.usuario_id else None
        
        result.append({
            **{key: getattr(mov, key) for key in mov.__dict__.keys() if not key.startswith('_')},
            'material_nome': material.nome if material else None,
            'usuario_nome': usuario.nome if usuario else None
        })
    
    print(f"📊 Encontradas {len(result)} movimentações")
    
    return result


@router.get('/{movimentacao_id}', response_model=schemas.MovimentacaoReponse)
def obter_movimentacao(movimentacao_id: int, db: Session = Depends(get_db)):
    """Obtém uma movimentação específica pelo ID"""
    movimentacao = db.query(models.Movimentacao).filter(models.Movimentacao.id == movimentacao_id).first()
    
    if not movimentacao:
        raise HTTPException(status_code=404, detail='Movimentação não encontrada')
    
    material = db.query(models.Material).filter(models.Material.id == movimentacao.material_id).first()
    usuario = db.query(models.Usuario).filter(models.Usuario.id == movimentacao.usuario_id).first() if mov.usuario_id else None
    
    result = {
        **{key: getattr(movimentacao, key) for key in movimentacao.__dict__.keys() if not key.startswith('_')},
        'material_nome': material.nome if material else None,
        'usuario_nome': usuario.nome if usuario else None
    }
    
    return result

@router.post('/', response_model=schemas.MovimentacaoReponse, status_code=201)
def criar_movimentacao(
    movimentacao: schemas.MovimentacaoCreate,
    db: Session = Depends(get_db),
    usuario_id: int = Query(1, description='ID do usuário logado')
):
    """Registra uma movimentação de entrada ou saída"""
    
    # Verificar se o material existe
    material = db.query(models.Material).filter(models.Material.id == movimentacao.material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail='Material não encontrado')
    
    # Validar tipo
    if movimentacao.tipo not in ['entrada', 'saida']:
        raise HTTPException(status_code=400, detail='Tipo inválido. Use "entrada" ou "saida"')
    
    # Para saída, verificar estoque (com material já verificado)
    if movimentacao.tipo == 'saida':
        if material.quantidade < movimentacao.quantidade:
            raise HTTPException(
                status_code=400, 
                detail=f'Estoque insuficiente. Disponível: {material.quantidade}'
            )
    
     # Criar dicionário com os dados
    dados_movimentacao = movimentacao.model_dump()
    # Adicionar campos extras
    dados_movimentacao['usuario_id'] = usuario_id
    dados_movimentacao['ip_origem'] = "127.0.0.1"
    
    # Criar movimentação (usando **dados_movimentacao uma única vez)
    nova_movimentacao = models.Movimentacao(**dados_movimentacao)
    db.add(nova_movimentacao)
    
    # ATUALIZAR ESTOQUE MANUALMENTE (temporário)
    if movimentacao.tipo == 'entrada':
        material.quantidade += movimentacao.quantidade
    else:
        material.quantidade -= movimentacao.quantidade
    
    db.commit()
    db.refresh(nova_movimentacao)
    
    # Buscar usuário
    usuario = db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()
    
    print(f"✅ Movimentação de {movimentacao.tipo} registrada: {movimentacao.quantidade} x {material.nome}")
    print(f"📦 Novo estoque: {material.quantidade}")
    
    result = {
        **{key: getattr(nova_movimentacao, key) for key in nova_movimentacao.__dict__.keys() if not key.startswith('_')},
        'material_nome': material.nome,
        'usuario_nome': usuario.nome if usuario else None
    }
    
    return result


@router.put('/{movimentacao_id}', response_model=schemas.MovimentacaoReponse)
def atualizar_movimentacao(
    movimentacao_id: int,
    movimentacao: schemas.MovimentacaoUpdate,
    db: Session = Depends(get_db)
):
    """Atualiza uma movimentação existente (apenas campos não relacionados ao estoque)"""
    
    movimentacao_existente = db.query(models.Movimentacao).filter(models.Movimentacao.id == movimentacao_id).first()
    
    if not movimentacao_existente:
        raise HTTPException(status_code=404, detail='Movimentação não encontrada')
    
    # Não permitir alterar tipo, quantidade ou material_id pois isso afetaria o estoque
    update_data = movimentacao.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(movimentacao_existente, field, value)
    
    db.commit()
    db.refresh(movimentacao_existente)
    
    material = db.query(models.Material).filter(models.Material.id == movimentacao_existente.material_id).first()
    usuario = db.query(models.Usuario).filter(models.Usuario.id == movimentacao_existente.usuario_id).first() if movimentacao_existente.usuario_id else None
    
    result = {
        **{key: getattr(movimentacao_existente, key) for key in movimentacao_existente.__dict__.keys() if not key.startswith('_')},
        'material_nome': material.nome if material else None,
        'usuario_nome': usuario.nome if usuario else None
    }
    
    return result


@router.delete('/{movimentacao_id}')
def deletar_movimentacao(
    movimentacao_id: int,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(auth.verificar_admin)
):
    """Remove uma movimentação (NÃO REVERTE o estoque - apenas registro)
       Apenas administradores podem deletar movimentações"""
    
    print(f"=" * 50)
    print(f"🔧 Deletando movimentação ID: {movimentacao_id}")
    print(f"👤 Usuário: {current_user.nome} (ID: {current_user.id}, Nível: {current_user.nivel_acesso})")
    
    try:
        # Buscar a movimentação
        movimentacao = db.query(models.Movimentacao).filter(models.Movimentacao.id == movimentacao_id).first()
        
        if not movimentacao:
            print(f"❌ Movimentação {movimentacao_id} não encontrada")
            raise HTTPException(status_code=404, detail='Movimentação não encontrada')
        
        print(f"✅ Movimentação encontrada: ID={movimentacao.id}, Tipo={movimentacao.tipo}, Qtd={movimentacao.quantidade}")
        
        # Tentar registrar log de auditoria (se a tabela existir)
        try:
            log = models.LogAuditoria(
                usuario_id=current_user.id,
                acao='DELETE',
                tabela_afetada='movimentacoes',
                registro_id=movimentacao_id,
                dados_anteriores={
                    'material_id': movimentacao.material_id,
                    'tipo': movimentacao.tipo,
                    'quantidade': movimentacao.quantidade,
                    'data_hora': str(movimentacao.data_hora)
                },
                ip_origem="127.0.0.1"
            )
            db.add(log)
            print(f"✅ Log de auditoria adicionado")
        except Exception as log_error:
            print(f"⚠️ Erro ao criar log (continuando): {log_error}")
        
        # Deletar a movimentação
        db.delete(movimentacao)
        db.commit()
        
        print(f"✅ Movimentação {movimentacao_id} deletada com sucesso!")
        print(f"=" * 50)
        
        return {'message': 'Movimentação deletada com sucesso'}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ ERRO INESPERADO: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        print(f"=" * 50)
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")
    


@router.get('/resumo/por-periodo')
def resumo_por_periodo(
    db: Session = Depends(get_db),
    data_inicio: str = Query(..., description='Data inicial (YYYY-MM-DD)'),
    data_fim: str = Query(..., description='Data final (YYYY-MM-DD)'),
    empresa: Optional[str] = Query(None, description='Filtrar por empresa')
):
    """Retorna resumo de movimentações por período"""
    
    query = db.query(models.Movimentacao).filter(
        models.Movimentacao.data_hora >= data_inicio,
        models.Movimentacao.data_hora <= f"{data_fim} 23:59:59"
    )
    
    if empresa:
        query = query.filter(models.Movimentacao.empresa == empresa)
    
    movimentacoes = query.all()
    
    total_entradas = sum(m.quantidade for m in movimentacoes if m.tipo == 'entrada')
    total_saidas = sum(m.quantidade for m in movimentacoes if m.tipo == 'saida')
    
    return {
        'periodo': {'inicio': data_inicio, 'fim': data_fim},
        'total_movimentacoes': len(movimentacoes),
        'total_entradas': total_entradas,
        'total_saidas': total_saidas,
        'saldo': total_entradas - total_saidas,
        'movimentacoes': [
            {
                'id': m.id,
                'material_id': m.material_id,
                'tipo': m.tipo,
                'quantidade': m.quantidade,
                'empresa': m.empresa,
                'data_hora': m.data_hora.isoformat()
            }
            for m in movimentacoes
        ]
    }
