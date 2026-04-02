from fastapi import FastAPI, Depends
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from app.database import engine, Base, get_db, test_connection
from app.routers import (materiais, maquinas, manutencoes, movimentacoes, pedidos,
                         auth, usuarios_sistema, colaboradores)
from sqlalchemy import text
from datetime import datetime

# Criar as tabelas no banco (se não existirem)
print("📦 Criando/verificando tabelas no banco de dados...")
Base.metadata.create_all(bind=engine)
print("✅ Tabelas criadas/verificadas com sucesso!")

# Criar aplicação FastAPI
app = FastAPI(
    title="Project Parallel API",
    description="Sistema de Controle de Estoque e Manutenções",
    version="1.0.0"
)

# Configurar segurança para o Swagger
security = HTTPBearer()

# Incluir routers
app.include_router(materiais.router)
app.include_router(maquinas.router)
app.include_router(manutencoes.router)
app.include_router(movimentacoes.router)
app.include_router(pedidos.router)
app.include_router(auth.router)
app.include_router(usuarios_sistema.router)
app.include_router(colaboradores.router)


@app.get("/")
def read_root():
    return {
        "message": "Project Parallel API",
        "status": "online",
        "version": "1.0.0"
    }

@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    """Verifica a saúde da aplicação e conexão com o banco"""
    try:
        # Testar conexão com o banco
        db.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }

@app.get("/test-db")
def test_database():
    """Endpoint para testar a conexão com o banco"""
    success = test_connection()
    if success:
        return {"status": "success", "message": "Conexão com PostgreSQL OK!"}
    else:
        return {"status": "error", "message": "Falha na conexão com PostgreSQL"}
    