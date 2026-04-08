import os
import zipfile
import json
import shutil
from datetime import datetime

def create_update_package():
    """Cria o pacote de atualização"""
    
    # Arquivos e pastas a incluir na atualização
    files_to_include = [
        'main.py',
        'api_client.py',
        'updater.py',
        'version.json',
        'widgets/',
        'styles/'
    ]
    
    # Criar pasta temp
    temp_dir = 'temp_update'
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir, exist_ok=True)
    
    # Copiar arquivos
    for item in files_to_include:
        src = item
        dst = os.path.join(temp_dir, item)
        
        if os.path.isfile(src):
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
        elif os.path.isdir(src):
            shutil.copytree(src, dst, dirs_exist_ok=True)
    
    # Criar arquivo zip
    zip_filename = f'project_parallel_update_{datetime.now().strftime("%Y%m%d_%H%M%S")}.zip'
    
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, temp_dir)
                zipf.write(file_path, arcname)
    
    # Limpar temp
    shutil.rmtree(temp_dir)
    
    print(f"✅ Pacote de atualização criado: {zip_filename}")
    print(f"📦 Tamanho: {os.path.getsize(zip_filename) / 1024:.2f} KB")
    return zip_filename

if __name__ == '__main__':
    create_update_package()
    