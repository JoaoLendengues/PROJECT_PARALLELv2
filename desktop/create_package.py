import os
import zipfile
import json
import shutil
from datetime import datetime

def create_update_package():
    """Cria o pacote de atualização com todos os arquivos modificados"""
    
    # Arquivos e pastas a incluir na atualização
    files_to_include = [
        # Backend
        ('backend/app/models.py', 'backend/app/models.py'),
        ('backend/app/schemas.py', 'backend/app/schemas.py'),
        ('backend/app/main.py', 'backend/app/main.py'),
        ('backend/app/auth.py', 'backend/app/auth.py'),
        ('backend/app/routers/__init__.py', 'backend/app/routers/__init__.py'),
        ('backend/app/routers/notificacoes.py', 'backend/app/routers/notificacoes.py'),
        ('backend/app/routers/backup.py', 'backend/app/routers/backup.py'),
        ('backend/app/routers/cargos.py', 'backend/app/routers/cargos.py'),
        ('backend/app/routers/departamentos.py', 'backend/app/routers/departamentos.py'),
        ('backend/app/routers/configuracoes.py', 'backend/app/routers/configuracoes.py'),
        ('backend/requirements.txt', 'backend/requirements.txt'),
        
        # Desktop - Core
        ('desktop/core/notification_manager.py', 'desktop/core/notification_manager.py'),
        ('desktop/core/sound_manager.py', 'desktop/core/sound_manager.py'),
        ('desktop/core/alert_service.py', 'desktop/core/alert_service.py'),
        
        # Desktop - Widgets
        ('desktop/widgets/toast_notification.py', 'desktop/widgets/toast_notification.py'),
        ('desktop/widgets/notification_center.py', 'desktop/widgets/notification_center.py'),
        ('desktop/widgets/notification_badge.py', 'desktop/widgets/notification_badge.py'),
        ('desktop/widgets/main_window.py', 'desktop/widgets/main_window.py'),
        ('desktop/widgets/parametros_widget.py', 'desktop/widgets/parametros_widget.py'),
        ('desktop/widgets/materiais_widget.py', 'desktop/widgets/materiais_widget.py'),
        ('desktop/widgets/maquinas_widget.py', 'desktop/widgets/maquinas_widget.py'),
        ('desktop/widgets/movimentacoes_widget.py', 'desktop/widgets/movimentacoes_widget.py'),
        ('desktop/widgets/manutencoes_widget.py', 'desktop/widgets/manutencoes_widget.py'),
        ('desktop/widgets/pedidos_widget.py', 'desktop/widgets/pedidos_widget.py'),
        ('desktop/widgets/colaboradores_widget.py', 'desktop/widgets/colaboradores_widget.py'),
        ('desktop/widgets/demandas_widget.py', 'desktop/widgets/demandas_widget.py'),
        ('desktop/widgets/relatorios_widget.py', 'desktop/widgets/relatorios_widget.py'),
        ('desktop/widgets/usuarios_widget.py', 'desktop/widgets/usuarios_widget.py'),
        
        # Desktop - Main
        ('desktop/api_client.py', 'desktop/api_client.py'),
        ('desktop/main.py', 'desktop/main.py'),
        ('desktop/updater.py', 'desktop/updater.py'),
        ('desktop/version.py', 'desktop/version.py'),
        ('desktop/version.json', 'desktop/version.json'),
    ]
    
    # Criar pasta temp
    temp_dir = 'temp_update'
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir, exist_ok=True)
    
    # Copiar arquivos
    for src, dst in files_to_include:
        if os.path.exists(src):
            dst_path = os.path.join(temp_dir, dst)
            os.makedirs(os.path.dirname(dst_path), exist_ok=True)
            shutil.copy2(src, dst_path)
            print(f"✅ Copiado: {src}")
        else:
            print(f"⚠️ Arquivo não encontrado: {src}")
    
    # Criar arquivo de changelog
    changelog = """
=== PROJECT PARALLEL - ATUALIZAÇÃO v1.1.0 ===

NOVAS FUNCIONALIDADES:
✅ Sistema completo de notificações
✅ Central de Notificações com histórico
✅ Alertas automáticos (estoque, manutenções, pedidos, demandas)
✅ Backup automático e manual
✅ CRUD de Cargos e Departamentos
✅ Filtros de empresa em todas as telas
✅ Campo MAC Address em máquinas
✅ Ícone de notificações no sidebar com badge
✅ Toast notifications com prioridades (cores e sons)

CORREÇÕES:
✅ Removida aba redundante de Alertas
✅ Melhorias de performance em filtros
✅ Correção de bugs em conclusão de pedidos
✅ Correção de exclusão de movimentações

ATUALIZAÇÃO RECOMENDADA:
✅ Execute o instalador ou substitua os arquivos manualmente
✅ Execute os scripts SQL no banco de dados (backup do backend)
    """
    
    changelog_path = os.path.join(temp_dir, 'CHANGELOG.txt')
    with open(changelog_path, 'w', encoding='utf-8') as f:
        f.write(changelog)
    
    # Criar script SQL para atualização do banco
    sql_script = """
-- PROJECT PARALLEL - ATUALIZAÇÃO DO BANCO DE DADOS
-- Versão: 1.1.0

-- Tabela de notificações
CREATE TABLE IF NOT EXISTS notificacoes (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER NOT NULL REFERENCES usuarios_sistema(id) ON DELETE CASCADE,
    tipo VARCHAR(50) NOT NULL,
    titulo VARCHAR(200) NOT NULL,
    mensagem TEXT NOT NULL,
    prioridade VARCHAR(20) NOT NULL,
    status VARCHAR(20) DEFAULT 'nao_lida',
    acao VARCHAR(100),
    acao_id INTEGER,
    dados_extra JSONB,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    lida_em TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_notificacoes_usuario_id ON notificacoes(usuario_id);
CREATE INDEX IF NOT EXISTS idx_notificacoes_status ON notificacoes(status);
CREATE INDEX IF NOT EXISTS idx_notificacoes_criado_em ON notificacoes(criado_em);

-- Tabela de cargos
CREATE TABLE IF NOT EXISTS cargos (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) UNIQUE NOT NULL,
    descricao TEXT,
    ativo BOOLEAN DEFAULT TRUE,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Inserir cargos padrão
INSERT INTO cargos (nome) VALUES 
('Analista'), ('Coordenador'), ('Gerente'), ('Supervisor'), ('Assistente'), ('Técnico'), ('Diretor')
ON CONFLICT (nome) DO NOTHING;

-- Tabela de departamentos
CREATE TABLE IF NOT EXISTS departamentos (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) UNIQUE NOT NULL,
    descricao TEXT,
    ativo BOOLEAN DEFAULT TRUE,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Inserir departamentos padrão
INSERT INTO departamentos (nome) VALUES 
('TI'), ('Administrativo'), ('Financeiro'), ('RH'), ('Comercial'), ('Marketing'), ('Logística')
ON CONFLICT (nome) DO NOTHING;

-- Tabela de configurações (se não existir)
CREATE TABLE IF NOT EXISTS configuracoes (
    id SERIAL PRIMARY KEY,
    chave VARCHAR(100) UNIQUE NOT NULL,
    valor TEXT,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Adicionar coluna MAC address em máquinas
ALTER TABLE maquinas ADD COLUMN IF NOT EXISTS mac_address VARCHAR(17);
ALTER TABLE maquinas ADD COLUMN IF NOT EXISTS ip_address VARCHAR(15);

-- Atualizar versão
INSERT INTO configuracoes (chave, valor) VALUES ('versao_sistema', '1.1.0')
ON CONFLICT (chave) DO UPDATE SET valor = '1.1.0';
"""
    
    sql_path = os.path.join(temp_dir, 'update_database.sql')
    with open(sql_path, 'w', encoding='utf-8') as f:
        f.write(sql_script)
    
    # Criar arquivo zip
    version = "1.1.0"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_filename = f'project_parallel_update_v{version}_{timestamp}.zip'
    
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, temp_dir)
                zipf.write(file_path, arcname)
    
    # Limpar temp
    shutil.rmtree(temp_dir)
    
    print(f"\n{'='*50}")
    print(f"✅ Pacote de atualização criado: {zip_filename}")
    print(f"📦 Tamanho: {os.path.getsize(zip_filename) / 1024:.2f} KB")
    print(f"📌 Versão: {version}")
    print(f"{'='*50}")
    print("\n📋 INSTRUÇÕES:")
    print("1. Execute o script SQL no banco de dados PostgreSQL")
    print("2. Substitua os arquivos do backend pelos da pasta 'backend/'")
    print("3. Substitua os arquivos do desktop pelos da pasta 'desktop/'")
    print("4. Reinicie o backend e o frontend")
    print(f"{'='*50}")
    
    return zip_filename

if __name__ == '__main__':
    create_update_package()