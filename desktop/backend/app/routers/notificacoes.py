from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
from app.database import get_db
from app import models, schemas, auth

router = APIRouter(prefix='/api/notificacoes', tags=['Notificações'])


@router.get('/', response_model=List[schemas.NotificacaoResponse])
def listar_notificacoes(
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(auth.get_current_user),
    status: Optional[str] = Query(None, description="Filtrar por status (nao_lida, lida, ignorada)"),
    prioridade: Optional[str] = Query(None, description="Filtrar por prioridade (alta, media, baixa)"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0)
):
    """Lista notificações do usuário atual"""
    
    query = db.query(models.Notificacao).filter(
        models.Notificacao.usuario_id == current_user.id
    )
    
    if status:
        query = query.filter(models.Notificacao.status == status)
    
    if prioridade:
        query = query.filter(models.Notificacao.prioridade == prioridade)
    
    notificacoes = query.order_by(
        models.Notificacao.criado_em.desc()
    ).offset(offset).limit(limit).all()
    
    return notificacoes


@router.get('/nao-lidas/count')
def contar_nao_lidas(
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(auth.get_current_user)
):
    """Retorna a quantidade de notificações não lidas"""
    
    count = db.query(models.Notificacao).filter(
        models.Notificacao.usuario_id == current_user.id,
        models.Notificacao.status == 'nao_lida'
    ).count()
    
    return {"count": count}


@router.post('/')
def criar_notificacao(
    notificacao: schemas.NotificacaoCreate,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(auth.get_current_user)
):
    """Cria uma nova notificação (para uso interno do sistema)"""
    
    nova_notificacao = models.Notificacao(
        **notificacao.model_dump(),
        usuario_id=current_user.id)
    db.add(nova_notificacao)
    db.commit()
    db.refresh(nova_notificacao)
    
    return {"message": "Notificação criada com sucesso", "id": nova_notificacao.id}


@router.put('/{notificacao_id}/marcar-lida')
def marcar_como_lida(
    notificacao_id: int,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(auth.get_current_user)
):
    """Marca uma notificação como lida"""
    
    notificacao = db.query(models.Notificacao).filter(
        models.Notificacao.id == notificacao_id,
        models.Notificacao.usuario_id == current_user.id
    ).first()
    
    if not notificacao:
        raise HTTPException(status_code=404, detail="Notificação não encontrada")
    
    notificacao.status = 'lida'
    notificacao.lida_em = datetime.now()
    db.commit()
    
    return {"message": "Notificação marcada como lida"}


@router.put('/marcar-todas-lidas')
def marcar_todas_como_lidas(
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(auth.get_current_user)
):
    """Marca todas as notificações do usuário como lidas"""
    
    db.query(models.Notificacao).filter(
        models.Notificacao.usuario_id == current_user.id,
        models.Notificacao.status == 'nao_lida'
    ).update({"status": "lida", "lida_em": datetime.now()})
    
    db.commit()
    
    return {"message": "Todas as notificações foram marcadas como lidas"}


@router.delete('/{notificacao_id}')
def deletar_notificacao(
    notificacao_id: int,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(auth.get_current_user)
):
    """Deleta uma notificação"""
    
    notificacao = db.query(models.Notificacao).filter(
        models.Notificacao.id == notificacao_id,
        models.Notificacao.usuario_id == current_user.id
    ).first()
    
    if not notificacao:
        raise HTTPException(status_code=404, detail="Notificação não encontrada")
    
    db.delete(notificacao)
    db.commit()
    
    return {"message": "Notificação deletada com sucesso"}


@router.delete('/limpar-antigas')
def limpar_notificacoes_antigas(
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(auth.get_current_user),
    dias: int = Query(30, description="Idade em dias para manter")
):
    """Remove notificações mais antigas que X dias"""
    
    from datetime import timedelta
    data_limite = datetime.now() - timedelta(days=dias)
    
    resultado = db.query(models.Notificacao).filter(
        models.Notificacao.usuario_id == current_user.id,
        models.Notificacao.criado_em < data_limite,
        models.Notificacao.status == 'lida'
    ).delete()
    
    db.commit()
    
    return {"message": f"{resultado} notificações antigas removidas"}
