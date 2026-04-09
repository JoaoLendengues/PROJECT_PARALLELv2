import psutil
import requests
import time
import os
from datetime import datetime

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def check_server_status():
    """Verifica status do servidor"""
    
    # Verificar CPU e memória
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    
    # Verificar conexões de rede
    connections = len(psutil.net_connections())
    
    # Verificar backend
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            backend_status = data.get("status", "unknown")
            pool_status = data.get("pool_status", {})
        else:
            backend_status = "error"
            pool_status = {}
    except:
        backend_status = "offline"
        pool_status = {}
    
    clear_screen()
    print("=" * 60)
    print("   PROJECT PARALLEL - MONITORAMENTO DO SERVIDOR")
    print("=" * 60)
    print(f"📅 Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("=" * 60)
    print()
    print("📊 RECURSOS DO SERVIDOR:")
    print(f"   CPU: {cpu_percent}%")
    print(f"   Memória: {memory.percent}% ({memory.used // (1024**3)}GB / {memory.total // (1024**3)}GB)")
    print(f"   Conexões de rede: {connections}")
    print()
    print("🖥️ BACKEND STATUS:")
    print(f"   Status: {backend_status}")
    
    if pool_status:
        print(f"   Pool de conexões DB:")
        print(f"     - Tamanho: {pool_status.get('pool_size', 'N/A')}")
        print(f"     - Em uso: {pool_status.get('checked_out', 'N/A')}")
        print(f"     - Disponível: {pool_status.get('checked_in', 'N/A')}")
        print(f"     - Total: {pool_status.get('total', 'N/A')}")
    
    print()
    print("=" * 60)
    print("   Atualizando a cada 10 segundos... (Ctrl+C para sair)")
    print("=" * 60)

if __name__ == "__main__":
    try:
        while True:
            check_server_status()
            time.sleep(10)
    except KeyboardInterrupt:
        print("\n\n✅ Monitoramento encerrado.")
        