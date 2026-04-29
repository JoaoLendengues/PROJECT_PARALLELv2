from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas, auth


router = APIRouter(prefix='/api/auth', tags=['Autenticação'])



@router.post('/login', response_model=schemas.LoginResponse)
def login(
    login_data: schemas.LoginRequest,
    db: Session = Depends(get_db)
):
    """Login do usuário"""
    usuario = auth.autenticar_usuario(db, login_data.codigo, login_data.senha)

    if not usuario:
        raise HTTPException(
            status_code=401,
            detail="código ou senha inválidos"
        )
    
    # Criar token
    access_token = auth.criar_token_acesso(data={"sub":usuario.codigo})

    return{
        "access_token": access_token,
        "token_type": "bearer",
        "usuario": usuario
    }


@router.post('/confirmar-senha')
def confirmar_senha(
    dados: schemas.ConfirmarSenhaRequest,
    current_user: models.UsuarioSistema = Depends(auth.get_current_user)
):
    """Confirma a senha do usuario autenticado para acoes sensiveis."""
    if not auth.verificar_senha(dados.senha, current_user.senha_hash):
        raise HTTPException(status_code=401, detail="Senha incorreta")

    return {"message": "Senha confirmada com sucesso"}


@router.post('/trocar-senha')
def trocar_senha(
    dados: schemas.TrocarSenhaRequest,
    db: Session = Depends(get_db)
):
    """Troca a senha do usuário"""
    usuario= db.query(models.UsuarioSistema).filter(
        models.UsuarioSistema.codigo == dados.codigo
    ).first()

    if not usuario:
        raise HTTPException(status_code=404,detail="Usuário não encontrado")
    
    # Verificar senha atual 
    if not auth.verificar_senha(dados.senha_atual, usuario.senha_hash):
        raise HTTPException(status_code=401, detail="Senha atual incorreta")
    
    #Atualizar senha
    usuario.senha_hash = auth.gerar_hash_senha(dados.nova_senha)
    usuario.primeiro_acesso = False
    db.commit()

    return{"message":"Senha alterada com sucesso"}


@router.post('/primeiro-acesso')
def primeiro_acesso(
    dados: schemas.TrocarSenhaRequest,
    db: Session = Depends(get_db)
):
    """Primeiro acesso - troca a senha padrão"""
    usuario = db.query(models.UsuarioSistema).filter(
        models.UsuarioSistema.codigo == dados.codigo,
        models.UsuarioSistema.primeiro_acesso == True
    ).first()


    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado ou já realizou primeiro acesso")
    
    # Verificar senha atual (senha padrão)
    if not auth.verificar_senha(dados.senha_atual, usuario.senha_hash):
        raise HTTPException(status_code=401, detail="Senha atual incorreta")
    
    # Atualizar senha
    usuario.senha_hash = auth.gerar_hash_senha(dados.nova_senha)
    usuario.primeiro_acesso = False
    db.commit()
    
    return {"message": "Senha alterada com sucesso. Faça login novamente."}

