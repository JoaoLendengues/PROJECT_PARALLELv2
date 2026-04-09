from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/project_parallel")

# Configuração para ALTA PERFORMANCE - 200 usuários
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=50,
    max_overflow=100,
    pool_pre_ping=True,
    pool_recycle=3600,
    pool_timeout=30,
    echo=False,
    connect_args={
        "connect_timeout": 10,
        "keepalives": 1,
        "keepalives_idle": 30,
        "keepalives_interval": 10,
        "keepalives_count": 5
    }
)

SessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine,
    expire_on_commit=False
)

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

def get_pool_status():
    """Retorna status do pool de conexões - CORRIGIDO"""
    pool = engine.pool
    return {
        "pool_size": pool.size(),
        "checked_in": pool.checkedin(),
        "checked_out": pool.checkedout(),
        "overflow": pool.overflow(),
        # "total" removido pois não existe no QueuePool
    }
