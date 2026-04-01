from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# URL de conexão com o banco de dados
DATABASE_URL = os.getenv('DATABASE_URL')

# Criar engine de conexão
engine = create_engine(
    DATABASE_URL,   
    pool_pre_ping=True, # Verifica se a conexão está ativa antes de usar
    pool_recycle=3600, # Reconecta após 1 hora
    echo=True   # Mostra os SQLs executados (útil para debug)
)

# Criar fábrica de sessões
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Criar classe base para os modelos
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
            result = conn.execute(text('SELECT version()'))
            version = result.fetchone()
            print(f"✅ Conexão bem sucedida!")
            print(f"📦 PostgreSQL: {version[0]}")
            return True
    except Exception as e:
        print(f"❌ Erro na conexão: {e}")
        return False
    