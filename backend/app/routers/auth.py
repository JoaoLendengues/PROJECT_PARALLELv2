from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas, auth
from app.audit import registrar_log_auditoria


router = APIRouter(prefix='/api/auth', tags=['Autenticação'])



@router.get('/usuario-preview/{codigo}', response_model=schemas.LoginUserPreviewResponse)
def get_usuario_preview(
    codigo: str,
    db: Session = Depends(get_db)
):
    """Retorna o nome do usuario ativo a partir do codigo informado."""
    usuario = db.query(models.UsuarioSistema).filter(
        models.UsuarioSistema.codigo == codigo,
        models.UsuarioSistema.ativo == True
    ).first()

    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario nao encontrado")

    return {
        "codigo": usuario.codigo,
        "nome": usuario.nome
    }


@router.post('/login', response_model=schemas.LoginResponse)
def login(
    request: Request,
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

    try:
        registrar_log_auditoria(
            db,
            usuario=usuario,
            acao="LOGIN",
            tabela_afetada="auth",
            registro_id=usuario.id,
            dados_novos={
                "codigo": usuario.codigo,
                "nome": usuario.nome,
                "nivel_acesso": usuario.nivel_acesso,
                "primeiro_acesso": usuario.primeiro_acesso,
            },
            request=request,
        )
        db.commit()
    except Exception as log_error:
        print(f"Erro ao registrar log de login: {log_error}")

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
    request: Request,
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
    
    dados_anteriores = {
        "codigo": usuario.codigo,
        "primeiro_acesso": usuario.primeiro_acesso,
    }

    #Atualizar senha
    usuario.senha_hash = auth.gerar_hash_senha(dados.nova_senha)
    usuario.primeiro_acesso = False
    db.commit()

    try:
        registrar_log_auditoria(
            db,
            usuario=usuario,
            acao="CHANGE_PASSWORD",
            tabela_afetada="usuarios_sistema",
            registro_id=usuario.id,
            dados_anteriores=dados_anteriores,
            dados_novos={
                "codigo": usuario.codigo,
                "primeiro_acesso": usuario.primeiro_acesso,
                "senha_alterada": True,
            },
            request=request,
        )
        db.commit()
    except Exception as log_error:
        print(f"Erro ao registrar log de troca de senha: {log_error}")

    return{"message":"Senha alterada com sucesso"}


@router.post('/primeiro-acesso')
def primeiro_acesso(
    dados: schemas.TrocarSenhaRequest,
    request: Request,
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
    
    dados_anteriores = {
        "codigo": usuario.codigo,
        "primeiro_acesso": usuario.primeiro_acesso,
    }

    # Atualizar senha
    usuario.senha_hash = auth.gerar_hash_senha(dados.nova_senha)
    usuario.primeiro_acesso = False
    db.commit()

    try:
        registrar_log_auditoria(
            db,
            usuario=usuario,
            acao="FIRST_ACCESS_PASSWORD_CHANGE",
            tabela_afetada="usuarios_sistema",
            registro_id=usuario.id,
            dados_anteriores=dados_anteriores,
            dados_novos={
                "codigo": usuario.codigo,
                "primeiro_acesso": usuario.primeiro_acesso,
                "senha_alterada": True,
            },
            request=request,
        )
        db.commit()
    except Exception as log_error:
        print(f"Erro ao registrar log de primeiro acesso: {log_error}")
    
    return {"message": "Senha alterada com sucesso. Faça login novamente."}

