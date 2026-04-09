from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/project_parallel")

# Configuração para PRODUÇÃO - Pool de conexões otimizado
engine = create_engine(
    DATABASE_URL,
    pool_size=20,           # Número de conexões mantidas no pool
    max_overflow=10,        # Conexões extras quando todas estão em uso
    pool_pre_ping=True,     # Verifica se a conexão está ativa antes de usar
    pool_recycle=3600,      # Reconecta após 1 hora
    echo=False              # Não mostrar SQLs (melhor performance)
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """Função para obter uma sessão do banco de dados"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_connection():
    """Função para testar a conexão com o banco"""
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()
            print(f"✅ Conexão bem sucedida!")
            print(f"📦 PostgreSQL: {version[0]}")
            return True
    except Exception as e:
        print(f"❌ Erro na conexão: {e}")
        return False
    