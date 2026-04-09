import uvicorn
import os
from dotenv import load_dotenv

load_dotenv()

if __name__ == "__main__":
    print("=" * 50)
    print("🚀 Project Parallel Backend - MODO PRODUÇÃO")
    print("=" * 50)
    print("📡 Servidor rodando em: http://0.0.0.0:8000")
    print("📍 API Docs: http://localhost:8000/docs")
    print("📍 Health Check: http://localhost:8000/health")
    print("=" * 50)
    print("⚙️ Configurações:")
    print("   - Reload: DESABILITADO")
    print("   - Workers: 4")
    print("   - Pool de conexões: 20")
    print("=" * 50)
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,           # Desabilitado para produção
        workers=4,              # 4 processos para múltiplos usuários
        limit_max_requests=1000 # Reinicia workers após 1000 requisições
    )
    