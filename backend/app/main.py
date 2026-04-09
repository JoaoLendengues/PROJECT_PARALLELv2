from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from app.database import engine, Base, get_db, test_connection, get_pool_status
from app.routers import (materiais, maquinas, manutencoes, movimentacoes, pedidos,
                         auth, usuarios_sistema, colaboradores, dashboard, demandas)
from sqlalchemy import text
from datetime import datetime
from fastapi.responses import HTMLResponse, JSONResponse
import psutil
import os

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

# Configurar CORS para múltiplos clientes
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configurar segurança
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
app.include_router(dashboard.router)
app.include_router(demandas.router)

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
        db.execute(text("SELECT 1"))
        pool_status = get_pool_status()
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.now().isoformat(),
            "pool_status": pool_status
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }

@app.get("/status")
def system_status():
    """Retorna status detalhado do sistema para monitoramento"""
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        pool_status = get_pool_status()
        
        return {
            "server": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_used_gb": memory.used // (1024**3),
                "memory_total_gb": memory.total // (1024**3),
                "disk_percent": disk.percent,
                "disk_free_gb": disk.free // (1024**3)
            },
            "database_pool": pool_status,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/test-db")
def test_database():
    """Endpoint para testar a conexão com o banco"""
    success = test_connection()
    if success:
        return {"status": "success", "message": "Conexão com PostgreSQL OK!"}
    else:
        return {"status": "error", "message": "Falha na conexão com PostgreSQL"}

@app.get("/login", response_class=HTMLResponse)
def login_page():
    """Página simples para login e obter token"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Project Parallel - Login</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                background: #f0f2f5;
                margin: 0;
            }
            .container {
                background: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                width: 350px;
            }
            h2 {
                text-align: center;
                color: #2c7da0;
                margin-top: 0;
            }
            input {
                width: 100%;
                padding: 10px;
                margin: 10px 0;
                border: 1px solid #ddd;
                border-radius: 5px;
                box-sizing: border-box;
            }
            button {
                width: 100%;
                padding: 10px;
                background: #2c7da0;
                color: white;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                font-size: 16px;
                margin-top: 10px;
            }
            button:hover {
                background: #1f5e7a;
            }
            #result {
                margin-top: 20px;
                padding: 10px;
                background: #f8f9fa;
                border-radius: 5px;
                font-size: 12px;
                word-break: break-all;
            }
            .success { color: #2a9d8f; }
            .error { color: #e76f51; }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>🔐 Project Parallel</h2>
            <input type="text" id="codigo" placeholder="Código" value="1001">
            <input type="password" id="senha" placeholder="Senha" value="admin123">
            <button onclick="fazerLogin()">Entrar</button>
            <div id="result"></div>
        </div>

        <script>
            async function fazerLogin() {
                const codigo = document.getElementById('codigo').value;
                const senha = document.getElementById('senha').value;
                const resultDiv = document.getElementById('result');
                
                resultDiv.innerHTML = '🔄 Carregando...';
                
                try {
                    const response = await fetch('/api/auth/login', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({codigo: codigo, senha: senha})
                    });
                    
                    const data = await response.json();
                    
                    if (response.ok) {
                        resultDiv.innerHTML = `
                            ✅ <strong>Login realizado!</strong><br><br>
                            📋 <strong>Token:</strong><br>
                            <code>${data.access_token}</code><br><br>
                            🔗 <a href="/docs?token=${data.access_token}" target="_blank">Abrir Swagger com Token</a>
                        `;
                    } else {
                        resultDiv.innerHTML = `❌ Erro: ${data.detail || 'Login inválido'}`;
                    }
                } catch (error) {
                    resultDiv.innerHTML = `❌ Erro de conexão: ${error.message}`;
                }
            }
        </script>
    </body>
    </html>
    """
