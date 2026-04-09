import os
import zipfile
import shutil
from datetime import datetime

def criar_pacote():
    """Cria o pacote de atualização"""
    
    # Arquivos a incluir
    arquivos = [
        'main.py',
        'api_client.py',
        'updater.py',
        'version.json',
        'widgets/',
        'styles/'
    ]
    
    # Criar pasta temporária
    temp_dir = 'temp_package'
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    # Copiar arquivos
    for item in arquivos:
        destino = os.path.join(temp_dir, item)
        if os.path.isfile(item):
            shutil.copy2(item, destino)
        elif os.path.isdir(item):
            shutil.copytree(item, destino)
    
    # Criar zip
    nome_zip = f'update_{datetime.now().strftime("%Y%m%d_%H%M%S")}.zip'
    with zipfile.ZipFile(nome_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, temp_dir)
                zipf.write(file_path, arcname)
    
    # Limpar
    shutil.rmtree(temp_dir)
    
    print(f"✅ Pacote criado: {nome_zip}")
    print(f"📦 Tamanho: {os.path.getsize(nome_zip) / 1024:.2f} KB")

if __name__ == '__main__':
    criar_pacote()
    