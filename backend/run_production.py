from waitress import serve
from app.main import app
import os
from dotenv import load_dotenv

load_dotenv()

print("=" * 50)
print("🚀 Project Parallel Backend - PRODUÇÃO (Waitress)")
print("=" * 50)
print("📡 Servidor rodando em: http://0.0.0.0:8000")
print("📍 API Docs: http://localhost:8000/docs")
print("=" * 50)
print("⚙️ Configurações:")
print("   - Servidor: Waitress")
print("   - Threads: 4")
print("=" * 50)

serve(app, host='0.0.0.0', port=8000, threads=4)
