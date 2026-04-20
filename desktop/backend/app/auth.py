from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import get_db
from app import models
import os

# Configurações
SECRET_KEY = os.getenv("SECRET_KEY", "project-parallel-secret-key-2024")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480  # 8 horas

# Contexto de criptografia para senhas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security
security = HTTPBearer()


def verificar_senha(senha_plana: str, senha_hash: str) -> bool:
    """Verifica se a senha corresponde ao hash"""
    return pwd_context.verify(senha_plana, senha_hash)


def gerar_hash_senha(senha: str) -> str:
    """Gera o hash da senha"""
    return pwd_context.hash(senha)


def criar_token_acesso(data: dict, expires_delta: timedelta = None):
    """Cria um token JWT"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def autenticar_usuario(db: Session, codigo: str, senha: str):
    """Autentica um usuário pelo código e senha"""
    usuario = db.query(models.UsuarioSistema).filter(
        models.UsuarioSistema.codigo == codigo,
        models.UsuarioSistema.ativo == True
    ).first()
    
    if not usuario:
        return None
    
    if not verificar_senha(senha, usuario.senha_hash):
        return None
    
    return usuario


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Obtém o usuário atual a partir do token JWT"""
    token = credentials.credentials
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        codigo: str = payload.get("sub")
        if codigo is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido"
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido"
        )
    
    usuario = db.query(models.UsuarioSistema).filter(
        models.UsuarioSistema.codigo == codigo,
        models.UsuarioSistema.ativo == True
    ).first()
    
    if usuario is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não encontrado"
        )
    
    return usuario


def verificar_admin(usuario: models.UsuarioSistema = Depends(get_current_user)):
    """Verifica se o usuário é administrador"""
    if usuario.nivel_acesso != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado. Apenas administradores."
        )
    return usuario


def verificar_gerente(usuario: models.UsuarioSistema = Depends(get_current_user)):
    """Verifica se o usuário é gerente ou administrador"""
    if usuario.nivel_acesso not in ["admin", "gerente"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado. Apenas gerentes e administradores."
        )
    return usuario
