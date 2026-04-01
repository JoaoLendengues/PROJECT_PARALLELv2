import uvicorn
import os
from dotenv import load_dotenv

load_dotenv()

if __name__ == '__main__':
    print('=' * 50)
    print('🚀 Project Parallel Backend')
    print('=' * 50)
    print('📡 Servidor rodando em: http://localhost:8000')
    print('📍 API Docs: http://localhost:8000/health')
    print('📍 Health Check: http://localhost:8000/health')
    print('=' * 50)

    uvicorn.run(
        'app.main:app',
        host='0.0.0.0',
        port=8000,
        reload=True
    )
    