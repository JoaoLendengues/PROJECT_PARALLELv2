import os
import zipfile
import json
import shutil
from datetime import datetime

def create_update_package():
    """Cria o pacote de atualização com todos os arquivos modificados"""
    
    print("=" * 50)
    print("  PROJECT PARALLEL - CREATE UPDATE PACKAGE")
    print("=" * 50)
    print()
    
    # Obtém o diretório onde o script está rodando
    base_dir = os.path.dirname(os.path.abspath(__file__))
    desktop_dir = base_dir  # Já que você roda de dentro do desktop
    backend_dir = os.path.join(base_dir, '..', 'backend')
    
    # Versão
    version = "1.1.6"
    
    # Arquivos e pastas a incluir na atualização
    files_to_include = [
        # Backend
        (os.path.join(backend_dir, 'app', 'models.py'), 'backend/app/models.py'),
        (os.path.join(backend_dir, 'app', 'schemas.py'), 'backend/app/schemas.py'),
        (os.path.join(backend_dir, 'app', 'main.py'), 'backend/app/main.py'),
        (os.path.join(backend_dir, 'app', 'auth.py'), 'backend/app/auth.py'),
        (os.path.join(backend_dir, 'app', 'routers', '__init__.py'), 'backend/app/routers/__init__.py'),
        (os.path.join(backend_dir, 'app', 'routers', 'notificacoes.py'), 'backend/app/routers/notificacoes.py'),
        (os.path.join(backend_dir, 'app', 'routers', 'backup.py'), 'backend/app/routers/backup.py'),
        (os.path.join(backend_dir, 'app', 'routers', 'cargos.py'), 'backend/app/routers/cargos.py'),
        (os.path.join(backend_dir, 'app', 'routers', 'departamentos.py'), 'backend/app/routers/departamentos.py'),
        (os.path.join(backend_dir, 'app', 'routers', 'configuracoes.py'), 'backend/app/routers/configuracoes.py'),
        (os.path.join(backend_dir, 'requirements.txt'), 'backend/requirements.txt'),
        
        # Desktop - Core
        (os.path.join(desktop_dir, 'core', 'notification_manager.py'), 'desktop/core/notification_manager.py'),
        (os.path.join(desktop_dir, 'core', 'sound_manager.py'), 'desktop/core/sound_manager.py'),
        (os.path.join(desktop_dir, 'core', 'alert_service.py'), 'desktop/core/alert_service.py'),
        
        # Desktop - Widgets
        (os.path.join(desktop_dir, 'widgets', 'toast_notification.py'), 'desktop/widgets/toast_notification.py'),
        (os.path.join(desktop_dir, 'widgets', 'notification_center.py'), 'desktop/widgets/notification_center.py'),
        (os.path.join(desktop_dir, 'widgets', 'notification_badge.py'), 'desktop/widgets/notification_badge.py'),
        (os.path.join(desktop_dir, 'widgets', 'main_window.py'), 'desktop/widgets/main_window.py'),
        (os.path.join(desktop_dir, 'widgets', 'parametros_widget.py'), 'desktop/widgets/parametros_widget.py'),
        (os.path.join(desktop_dir, 'widgets', 'materiais_widget.py'), 'desktop/widgets/materiais_widget.py'),
        (os.path.join(desktop_dir, 'widgets', 'maquinas_widget.py'), 'desktop/widgets/maquinas_widget.py'),
        (os.path.join(desktop_dir, 'widgets', 'movimentacoes_widget.py'), 'desktop/widgets/movimentacoes_widget.py'),
        (os.path.join(desktop_dir, 'widgets', 'manutencoes_widget.py'), 'desktop/widgets/manutencoes_widget.py'),
        (os.path.join(desktop_dir, 'widgets', 'pedidos_widget.py'), 'desktop/widgets/pedidos_widget.py'),
        (os.path.join(desktop_dir, 'widgets', 'colaboradores_widget.py'), 'desktop/widgets/colaboradores_widget.py'),
        (os.path.join(desktop_dir, 'widgets', 'demandas_widget.py'), 'desktop/widgets/demandas_widget.py'),
        (os.path.join(desktop_dir, 'widgets', 'relatorios_widget.py'), 'desktop/widgets/relatorios_widget.py'),
        (os.path.join(desktop_dir, 'widgets', 'usuarios_widget.py'), 'desktop/widgets/usuarios_widget.py'),
        
        # Desktop - Main
        (os.path.join(desktop_dir, 'api_client.py'), 'desktop/api_client.py'),
        (os.path.join(desktop_dir, 'main.py'), 'desktop/main.py'),
        (os.path.join(desktop_dir, 'updater.py'), 'desktop/updater.py'),
        (os.path.join(desktop_dir, 'version.py'), 'desktop/version.py'),
        (os.path.join(desktop_dir, 'version.json'), 'desktop/version.json'),
    ]
    
    # Criar pasta temp
    temp_dir = 'temp_update'
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir, exist_ok=True)
    
    print("📦 Copiando arquivos...")
    print("-" * 40)
    
    # Copiar arquivos
    arquivos_copiados = 0
    arquivos_nao_encontrados = 0
    
    for src, dst in files_to_include:
        if os.path.exists(src):
            dst_path = os.path.join(temp_dir, dst)
            os.makedirs(os.path.dirname(dst_path), exist_ok=True)
            shutil.copy2(src, dst_path)
            print(f"✅ {os.path.basename(src)}")
            arquivos_copiados += 1
        else:
            print(f"⚠️ Arquivo não encontrado: {src}")
            arquivos_nao_encontrados += 1
    
    print("-" * 40)
    print(f"📊 Resumo: {arquivos_copiados} arquivos copiados, {arquivos_nao_encontrados} não encontrados")
    
    # Criar arquivo de changelog
    changelog = f"""
=== PROJECT PARALLEL - ATUALIZAÇÃO v{version} ===
Data: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}

🔧 CORREÇÕES NESTA VERSÃO:

1. 🐛 Corrigido erro 'NoneType' ao carregar movimentações com observação vazia
2. 🪟 Corrigido toast notification para aparecer dentro da janela do sistema
3. ❌ Removida barra de título e botões de janela das notificações
4. 🎨 Ajustado layout das notificações

📋 INSTRUÇÕES DE ATUALIZAÇÃO:

1. Faça backup do banco de dados (recomendado)
2. Substitua os arquivos do backend pelos da pasta 'backend/'
3. Substitua os arquivos do desktop pelos da pasta 'desktop/'
4. Reinicie o backend e o frontend

✅ TESTADO E APROVADO!
"""
    
    changelog_path = os.path.join(temp_dir, 'CHANGELOG.txt')
    with open(changelog_path, 'w', encoding='utf-8') as f:
        f.write(changelog)
    print(f"✅ Criado: CHANGELOG.txt")
    
    # Criar script SQL para atualização do banco
    sql_script = """
-- PROJECT PARALLEL - ATUALIZAÇÃO DO BANCO DE DADOS
-- Versão: 1.1.5

-- Verificar versão atual
SELECT valor as versao_atual FROM configuracoes WHERE chave = 'versao_sistema';

-- Atualizar versão
INSERT INTO configuracoes (chave, valor) VALUES ('versao_sistema', '1.1.5')
ON CONFLICT (chave) DO UPDATE SET valor = '1.1.5';
"""
    
    sql_path = os.path.join(temp_dir, 'update_database.sql')
    with open(sql_path, 'w', encoding='utf-8') as f:
        f.write(sql_script)
    print(f"✅ Criado: update_database.sql")
    
    # Criar arquivo README da atualização
    readme_content = f"""PROJECT PARALLEL - PACOTE DE ATUALIZAÇÃO v{version}
=============================================

📦 CONTEÚDO DO PACOTE:
- backend/     → Arquivos do servidor (FastAPI)
- desktop/     → Arquivos do cliente (PySide6)
- CHANGELOG.txt → Lista de mudanças
- update_database.sql → Scripts SQL

🚀 COMO ATUALIZAR:

1. BACKEND (servidor):
   - Parar o serviço do backend
   - Substituir os arquivos da pasta 'backend/'
   - Executar o script SQL no PostgreSQL
   - Reiniciar o backend

2. DESKTOP (clientes):
   - Substituir os arquivos da pasta 'desktop/'

Versão: {version}
Data: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}
"""
    
    readme_path = os.path.join(temp_dir, 'README_UPDATE.txt')
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    print(f"✅ Criado: README_UPDATE.txt")
    
    # Criar arquivo zip
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_filename = f'project_parallel_update_v{version}_{timestamp}.zip'
    
    print()
    print("📦 Criando arquivo ZIP...")
    
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, temp_dir)
                zipf.write(file_path, arcname)
    
    # Limpar temp
    shutil.rmtree(temp_dir)
    
    # Tamanho do arquivo
    size_mb = os.path.getsize(zip_filename) / (1024 * 1024)
    
    print()
    print("=" * 50)
    print(f"✅ PACOTE DE ATUALIZAÇÃO CRIADO COM SUCESSO!")
    print("=" * 50)
    print(f"📦 Arquivo: {zip_filename}")
    print(f"📏 Tamanho: {size_mb:.2f} MB")
    print(f"📌 Versão: {version}")
    print(f"📅 Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("=" * 50)
    print()
    print("📋 INSTRUÇÕES:")
    print("1. Execute o script SQL no banco de dados PostgreSQL")
    print("2. Substitua os arquivos do backend pelos da pasta 'backend/'")
    print("3. Substitua os arquivos do desktop pelos da pasta 'desktop/'")
    print("4. Reinicie o backend e o frontend")
    print("=" * 50)
    
    return zip_filename


if __name__ == '__main__':
    create_update_package()
