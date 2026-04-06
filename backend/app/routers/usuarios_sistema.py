from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from typing import Optional, List
from app.database import get_db
from app import models, schemas, auth

router = APIRouter(prefix='/api/usuarios', tags=['Usuários do Sistema'])


@router.get('/', response_model=List[schemas.UsuarioSistemaResponse])
def listar_usuarios(
    db: Session = Depends(get_db),
    admin: models.UsuarioSistema = Depends(auth.verificar_admin),
    ativo: Optional[bool] = Query(None, description="Filtrar por ativo"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    """Lista todos os usuários (apenas administradores)"""
    
    query = db.query(models.UsuarioSistema)
    
    if ativo is not None:
        query = query.filter(models.UsuarioSistema.ativo == ativo)
    
    usuarios = query.order_by(models.UsuarioSistema.nome).offset(offset).limit(limit).all()
    
    return usuarios


@router.get('/{usuario_id}', response_model=schemas.UsuarioSistemaResponse)
def obter_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    admin: models.UsuarioSistema = Depends(auth.verificar_admin)
):
    """Obtém um usuário específico"""
    
    usuario = db.query(models.UsuarioSistema).filter(models.UsuarioSistema.id == usuario_id).first()
    
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    return usuario


@router.post('/', response_model=schemas.UsuarioSistemaResponse, status_code=201)
def criar_usuario(
    usuario: schemas.UsuarioSistemaCreate,
    db: Session = Depends(get_db),
    admin: models.UsuarioSistema = Depends(auth.verificar_admin)
):
    """Cria um novo usuário (apenas administradores)"""
    
    # Verificar se código já existe
    existing = db.query(models.UsuarioSistema).filter(
        models.UsuarioSistema.codigo == usuario.codigo
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Código de usuário já existe")
    
    # Criar usuário com senha padrão
    senha_padrao = "123456"
    novo_usuario = models.UsuarioSistema(
        codigo=usuario.codigo,
        nome=usuario.nome,
        senha_hash=auth.gerar_hash_senha(senha_padrao),
        cargo=usuario.cargo,
        empresa=usuario.empresa,
        nivel_acesso=usuario.nivel_acesso,
        primeiro_acesso=True,
        ativo=usuario.ativo
    )
    db.add(novo_usuario)
    db.commit()
    db.refresh(novo_usuario)
    
    return novo_usuario


@router.put('/{usuario_id}', response_model=schemas.UsuarioSistemaResponse)
def atualizar_usuario(
    usuario_id: int,
    usuario: schemas.UsuarioSistemaUpdate,
    db: Session = Depends(get_db),
    admin: models.UsuarioSistema = Depends(auth.verificar_admin)
):
    """Atualiza um usuário (apenas administradores)"""
    
    usuario_existente = db.query(models.UsuarioSistema).filter(models.UsuarioSistema.id == usuario_id).first()
    
    if not usuario_existente:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    update_data = usuario.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(usuario_existente, field, value)
    
    db.commit()
    db.refresh(usuario_existente)
    
    return usuario_existente


@router.delete('/{usuario_id}')
def deletar_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    admin: models.UsuarioSistema = Depends(auth.verificar_admin)
):
    """Remove um usuário (apenas administradores)"""
    
    usuario = db.query(models.UsuarioSistema).filter(models.UsuarioSistema.id == usuario_id).first()
    
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    db.delete(usuario)
    db.commit()
    
    return {"message": "Usuário deletado com sucesso"}


@router.post('/{usuario_id}/resetar-senha')
def resetar_senha(
    usuario_id: int,
    db: Session = Depends(get_db),
    admin: models.UsuarioSistema = Depends(auth.verificar_admin)
):
    """Reseta a senha do usuário para o padrão (apenas administradores)"""
    
    usuario = db.query(models.UsuarioSistema).filter(models.UsuarioSistema.id == usuario_id).first()
    
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    senha_padrao = "123456"
    usuario.senha_hash = auth.gerar_hash_senha(senha_padrao)
    usuario.primeiro_acesso = True
    db.commit()
    
    return {"message": f"Senha resetada para padrão: {senha_padrao}"}


@router.post('/{usuario_id}/alterar-senha')
def alterar_senha(
    usuario_id: int,
    request: dict,
    db: Session = Depends(get_db),
    admin: models.UsuarioSistema = Depends(auth.verificar_admin)
):
    """Altera a senha de um usuário (apenas administradores)"""
    
    nova_senha = request.get("nova_senha")
    if not nova_senha:
        raise HTTPException(status_code=400, detail="Nova senha não fornecida")
    
    if len(nova_senha) < 6:
        raise HTTPException(status_code=400, detail="A senha deve ter no mínimo 6 caracteres")
    
    usuario = db.query(models.UsuarioSistema).filter(models.UsuarioSistema.id == usuario_id).first()
    
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    usuario.senha_hash = auth.gerar_hash_senha(nova_senha)
    usuario.primeiro_acesso = False  # Se o admin está alterando, não é primeiro acesso
    db.commit()
    
    return {"message": "Senha alterada com sucesso"}
