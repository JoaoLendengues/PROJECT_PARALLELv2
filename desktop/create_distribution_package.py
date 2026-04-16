import os
import zipfile
import shutil
import subprocess
import sys
from datetime import datetime
import json

def criar_executavel():
    """Gera o executável usando PyInstaller"""
    print("🔧 Gerando executável...")
    
    # Verificar se o PyInstaller está instalado
    try:
        import PyInstaller
    except ImportError:
        print("📦 Instalando PyInstaller...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyinstaller'], check=True)
    
    # Limpar builds anteriores
    if os.path.exists('build'):
        shutil.rmtree('build')
    if os.path.exists('dist'):
        shutil.rmtree('dist')
    
    # Executar PyInstaller
    result = subprocess.run([
        sys.executable, '-m', 'PyInstaller',
        'ProjectParallel.spec',
        '--clean',
        '--noconfirm'
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ Erro ao gerar executável: {result.stderr}")
        return False
    
    print("✅ Executável gerado com sucesso!")
    return True


def criar_pacote_distribuicao():
    """Cria o pacote de distribuição completo com executável"""
    
    print("\n📦 Criando pacote de distribuição...")
    
    # Obter versão
    version = "1.1.0"
    try:
        with open('version.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            version = data.get('version', version)
    except:
        pass
    
    # Nome do pacote
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    package_dir = f'ProjectParallel_v{version}'
    zip_filename = f'ProjectParallel_v{version}_{timestamp}.zip'
    
    # Verificar se o executável existe
    exe_path = os.path.join('dist', 'ProjectParallel.exe')
    if not os.path.exists(exe_path):
        print("❌ Executável não encontrado! Gerando...")
        if not criar_executavel():
            return None
    
    # Criar pasta do pacote
    if os.path.exists(package_dir):
        shutil.rmtree(package_dir)
    os.makedirs(package_dir)
    
    # Criar subpastas
    os.makedirs(os.path.join(package_dir, 'styles'))
    
    # Copiar executável
    shutil.copy2(exe_path, package_dir)
    print(f"✅ Copiado: ProjectParallel.exe")
    
    # Copiar arquivos de configuração
    files_to_copy = [
        ('version.json', 'version.json'),
        ('version.py', 'version.py'),
        ('configurar.bat', 'configurar.bat'),
        ('instalar.bat', 'instalar.bat'),
        ('LEIA-ME.txt', 'LEIA-ME.txt'),
    ]
    
    for src, dst in files_to_copy:
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(package_dir, dst))
            print(f"✅ Copiado: {src}")
    
    # Copiar pasta styles
    if os.path.exists('styles'):
        shutil.copytree('styles', os.path.join(package_dir, 'styles'))
        print(f"✅ Copiado: styles/")
    
    # Criar README
    readme_content = f"""PROJECT PARALLEL v{version}
================================

📦 PACOTE DE DISTRIBUIÇÃO COMPLETA

Este pacote contém o executável pronto para uso do sistema Project Parallel.

📁 CONTEÚDO:
- ProjectParallel.exe - Executável principal
- styles/ - Arquivos de estilo
- version.json - Informações da versão
- configurar.bat - Script de configuração do servidor
- instalar.bat - Script de instalação rápida

🚀 COMO INSTALAR:

OPÇÃO 1 (Recomendada):
1. Extraia todos os arquivos para uma pasta no Desktop
2. Execute configurar.bat e digite o IP do servidor
3. Execute ProjectParallel.exe

OPÇÃO 2 (Instalação automática):
1. Execute instalar.bat
2. O programa será copiado para o Desktop
3. Configure o servidor e execute

🔧 CONFIGURAÇÃO DO SERVIDOR:
- IP Padrão: 10.1.1.151
- Porta: 8000

👤 LOGIN PADRÃO:
- Código: 1001
- Senha: admin123

⚠️ REQUISITOS:
- Windows 10 ou superior
- Conexão com o servidor (backend rodando)
- PostgreSQL configurado no servidor

🐛 PROBLEMAS COMUNS:

1. "Erro de conexão com a API"
   → Verifique se o servidor está rodando
   → Verifique o IP no arquivo .env

2. "Token inválido"
   → Faça login novamente
   → Verifique suas credenciais

3. "Erro ao carregar dados"
   → Verifique a conexão com o banco de dados

📞 SUPORTE:
Email: ti@pinheiroferragens.com.br

Versão: {version}
Data: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}
"""
    
    readme_path = os.path.join(package_dir, 'INSTRUCOES.txt')
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    print(f"✅ Criado: INSTRUCOES.txt")
    
    # Criar arquivo .env.example
    env_example = """# Configuração do servidor
API_URL=http://10.1.1.151:8000

# Para alterar o IP, edite esta linha ou execute configurar.bat
"""
    env_path = os.path.join(package_dir, '.env.example')
    with open(env_path, 'w', encoding='utf-8') as f:
        f.write(env_example)
    print(f"✅ Criado: .env.example")
    
    # Criar arquivo ZIP
    print(f"\n📦 Criando arquivo ZIP...")
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(package_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, package_dir)
                zipf.write(file_path, arcname)
    
    # Limpar pasta temporária
    shutil.rmtree(package_dir)
    
    # Tamanho do arquivo
    size_mb = os.path.getsize(zip_filename) / (1024 * 1024)
    
    print(f"\n{'='*50}")
    print(f"✅ PACOTE DE DISTRIBUIÇÃO CRIADO!")
    print(f"{'='*50}")
    print(f"📦 Arquivo: {zip_filename}")
    print(f"📏 Tamanho: {size_mb:.2f} MB")
    print(f"📌 Versão: {version}")
    print(f"{'='*50}")
    print("\n📋 PARA DISTRIBUIR:")
    print("1. Envie o arquivo ZIP para os usuários")
    print("2. Eles devem extrair e executar ProjectParallel.exe")
    print(f"{'='*50}")
    
    return zip_filename


if __name__ == '__main__':
    print("="*50)
    print("  PROJECT PARALLEL - DISTRIBUTION PACKAGE")
    print("="*50)
    print("\n1. Criar pacote de ATUALIZAÇÃO (apenas arquivos)")
    print("2. Criar pacote de DISTRIBUIÇÃO (com executável)")
    print("3. Criar ambos")
    print("\n0. Sair")
    
    opcao = input("\nEscolha uma opção: ").strip()
    
    if opcao == '1':
        from create_package import create_update_package
        create_update_package()
    elif opcao == '2':
        criar_pacote_distribuicao()
    elif opcao == '3':
        from create_package import create_update_package
        print("\n📦 Criando pacote de ATUALIZAÇÃO...")
        create_update_package()
        print("\n📦 Criando pacote de DISTRIBUIÇÃO...")
        criar_pacote_distribuicao()
    else:
        print("Saindo...")
        