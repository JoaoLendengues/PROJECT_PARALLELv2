import os
import shutil
from datetime import datetime

def criar_backup_automatico():
    """Cria um backup automático antes da atualização"""
    try:
        if getattr(sys, 'frozen', False):
            current_dir = os.path.dirname(sys.executable)
        else:
            current_dir = os.path.dirname(os.path.abspath(sys.argv[0]))

        backup_dir = os.path.join(current_dir, 'backup', datetime.now().strftime('%Y%m%d_%H%M%S'))
        os.makedirs(backup_dir, exist_ok=True)

        # Pastas críticas para backup
        pastas_criticas = ['widgets', 'core', 'styles']

        for pasta in pastas_criticas:
            src = os.path.join(current_dir, pasta)
            if os.path.exists(src):
                dst = os.path.join(backup_dir, pasta)
                shutil.copytree(src, dst)
                print(f'✅ Backp de {pasta} criado')

        # Arquivos críticos
        arquivos_criticos = ['main.py', 'api_client.py', 'version.py', 'version.json']
        for arquivo in arquivos_criticos:
            src = os.path.join(current_dir, arquivo)
            if os.path.exists(src):
                dst = os.path.join(backup_dir, arquivo)
                shutil.copy2(src, dst)
                print(f'✅ Backup de {arquivo} criado')

        return backup_dir
    except Exception as e:
        print(f'⚠️ Erro ao criar backup: {e}')
        return None