import uvicorn
import os
from dotenv import load_dotenv

load_dotenv()

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Project Parallel Backend - HIGH PERFORMANCE")
    print("=" * 60)
    print("📡 Servidor rodando em: http://0.0.0.0:8000")
    print("📍 API Docs: http://localhost:8000/docs")
    print("📍 Health Check: http://localhost:8000/health")
    print("=" * 60)
    print("⚙️ Configurações para 200 usuários simultâneos:")
    print("   - Workers: 8")
    print("   - Conexões máximas: 200")
    print("   - Backlog: 2048")
    print("   - Keep Alive: 65 segundos")
    print("=" * 60)
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        workers=8,
        limit_max_requests=10000,
        limit_concurrency=200,
        timeout_keep_alive=65,
        backlog=2048,
        loop="asyncio",
        http="httptools",
    )
    