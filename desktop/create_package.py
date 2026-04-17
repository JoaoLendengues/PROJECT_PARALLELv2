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
    
    # Versão
    version = "1.1.2"
    
    # Arquivos e pastas a incluir na atualização
    files_to_include = [
        # Backend
        ('../backend/app/models.py', 'backend/app/models.py'),
        ('../backend/app/schemas.py', 'backend/app/schemas.py'),
        ('../backend/app/main.py', 'backend/app/main.py'),
        ('../backend/app/auth.py', 'backend/app/auth.py'),
        ('../backend/app/routers/__init__.py', 'backend/app/routers/__init__.py'),
        ('../backend/app/routers/notificacoes.py', 'backend/app/routers/notificacoes.py'),
        ('../backend/app/routers/backup.py', 'backend/app/routers/backup.py'),
        ('../backend/app/routers/cargos.py', 'backend/app/routers/cargos.py'),
        ('../backend/app/routers/departamentos.py', 'backend/app/routers/departamentos.py'),
        ('../backend/app/routers/configuracoes.py', 'backend/app/routers/configuracoes.py'),
        ('../backend/requirements.txt', 'backend/requirements.txt'),
        
        # Desktop - Core
        ('core/notification_manager.py', 'desktop/core/notification_manager.py'),
        ('core/sound_manager.py', 'desktop/core/sound_manager.py'),
        ('core/alert_service.py', 'desktop/core/alert_service.py'),
        
        # Desktop - Widgets (CORRIGIDOS)
        ('widgets/toast_notification.py', 'desktop/widgets/toast_notification.py'),
        ('widgets/notification_center.py', 'desktop/widgets/notification_center.py'),
        ('widgets/notification_badge.py', 'desktop/widgets/notification_badge.py'),
        ('widgets/main_window.py', 'desktop/widgets/main_window.py'),
        ('widgets/parametros_widget.py', 'desktop/widgets/parametros_widget.py'),
        ('widgets/materiais_widget.py', 'desktop/widgets/materiais_widget.py'),
        ('widgets/maquinas_widget.py', 'desktop/widgets/maquinas_widget.py'),
        ('widgets/movimentacoes_widget.py', 'desktop/widgets/movimentacoes_widget.py'),  # CORRIGIDO
        ('widgets/manutencoes_widget.py', 'desktop/widgets/manutencoes_widget.py'),
        ('widgets/pedidos_widget.py', 'desktop/widgets/pedidos_widget.py'),
        ('widgets/colaboradores_widget.py', 'desktop/widgets/colaboradores_widget.py'),
        ('widgets/demandas_widget.py', 'desktop/widgets/demandas_widget.py'),
        ('widgets/relatorios_widget.py', 'desktop/widgets/relatorios_widget.py'),      # CORRIGIDO
        ('widgets/usuarios_widget.py', 'desktop/widgets/usuarios_widget.py'),
        
        # Desktop - Main
        ('api_client.py', 'desktop/api_client.py'),
        ('main.py', 'desktop/main.py'),
        ('updater.py', 'desktop/updater.py'),
        ('version.py', 'desktop/version.py'),
        ('version.json', 'desktop/version.json'),
    ]
    
    # Criar pasta temp
    temp_dir = 'temp_update'
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir, exist_ok=True)
    
    print("📦 Copiando arquivos...")
    print("-" * 40)
    
    # Copiar arquivos
    for src, dst in files_to_include:
        if os.path.exists(src):
            dst_path = os.path.join(temp_dir, dst)
            os.makedirs(os.path.dirname(dst_path), exist_ok=True)
            shutil.copy2(src, dst_path)
            print(f"✅ {src}")
        else:
            print(f"⚠️ Arquivo não encontrado: {src}")
    
    print("-" * 40)
    
    # Criar arquivo de changelog
    changelog = f"""
=== PROJECT PARALLEL - ATUALIZAÇÃO v{version} ===
Data: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}

🔧 CORREÇÕES NESTA VERSÃO:

1. 🐛 Corrigido erro 'NoneType' ao carregar movimentações com observação vazia
   - Arquivo: movimentacoes_widget.py
   - Arquivo: relatorios_widget.py

2. 🪟 Corrigido toast notification para aparecer dentro da janela do sistema
   - Removidas flags de janela independente
   - Notificações agora são widgets internos

3. ❌ Removida barra de título e botões de janela das notificações
   - Toast notification sem botões minimizar/maximizar/fechar

4. 🎨 Ajustado layout das notificações
   - Fundo sólido colorido (não mais transparente)
   - Tamanho otimizado e mais retangular

📋 INSTRUÇÕES DE ATUALIZAÇÃO:

1. Faça backup do banco de dados (recomendado)
2. Execute o script SQL no PostgreSQL (update_database.sql)
3. Substitua os arquivos do backend pelos da pasta 'backend/'
4. Substitua os arquivos do desktop pelos da pasta 'desktop/'
5. Reinicie o backend e o frontend

⚠️ ATENÇÃO:
- Esta é uma atualização de correção (bug fix)
- Versão anterior: 1.1.0
- Nova versão: {version}

✅ TESTADO E APROVADO!
"""
    
    changelog_path = os.path.join(temp_dir, 'CHANGELOG.txt')
    with open(changelog_path, 'w', encoding='utf-8') as f:
        f.write(changelog)
    print(f"✅ Criado: CHANGELOG.txt")
    
    # Criar script SQL para atualização do banco (se necessário)
    sql_script = """
-- PROJECT PARALLEL - ATUALIZAÇÃO DO BANCO DE DADOS
-- Versão: 1.1.1 (nenhuma alteração no banco, apenas correções de código)

-- Verificar versão atual
SELECT valor as versao_atual FROM configuracoes WHERE chave = 'versao_sistema';

-- Atualizar versão (opcional)
INSERT INTO configuracoes (chave, valor) VALUES ('versao_sistema', '1.1.1')
ON CONFLICT (chave) DO UPDATE SET valor = '1.1.1';

-- Nota: Esta versão não contém alterações na estrutura do banco,
-- apenas correções no código do frontend.
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
- update_database.sql → Scripts SQL (se necessário)

🚀 COMO ATUALIZAR:

1. BACKEND (servidor):
   - Parar o serviço do backend
   - Substituir os arquivos da pasta 'backend/'
   - Executar o script SQL no PostgreSQL (se houver alterações)
   - Reiniciar o backend

2. DESKTOP (clientes):
   - Substituir os arquivos da pasta 'desktop/'
   - Ou substituir apenas os arquivos modificados:
     * widgets/movimentacoes_widget.py
     * widgets/relatorios_widget.py
     * widgets/toast_notification.py
     * core/notification_manager.py
     * version.json
     * version.py

📞 SUPORTE:
Em caso de dúvidas, contate o suporte de TI.

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
    print("1. Execute o script SQL no banco de dados PostgreSQL (se necessário)")
    print("2. Substitua os arquivos do backend pelos da pasta 'backend/'")
    print("3. Substitua os arquivos do desktop pelos da pasta 'desktop/'")
    print("4. Reinicie o backend e o frontend")
    print("=" * 50)
    
    return zip_filename


if __name__ == '__main__':
    create_update_package()
