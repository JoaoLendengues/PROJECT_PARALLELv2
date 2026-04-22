import requests
import json
import os
import sys
import shutil
import zipfile
from datetime import datetime
from PySide6.QtCore import QThread, Signal
from version import CURRENT_VERSION


class UpdateChecker(QThread):
    """Verifica se há atualizações disponíveis no GitHub"""
    
    update_available = Signal(dict)
    no_update = Signal()
    error = Signal(str)
    
    def __init__(self):
        super().__init__()
        self.current_version = CURRENT_VERSION
        # URL da API do GitHub - SUBSTITUA PELO SEU REPOSITORIO
        self.update_url = "https://api.github.com/repos/JoaoLendengues/PROJECT_PARALLELv2/releases/latest"
    
    def run(self):
        try:
            print(f"🔍 Verificando atualizações em: {self.update_url}")
            
            response = requests.get(self.update_url, timeout=10, headers={
                "Accept": "application/vnd.github.v3+json"
            })
            
            print(f"📡 Status code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                latest_version = data.get("tag_name", "0.0.0").replace("v", "")
                
                print(f"📦 Versão atual: {self.current_version}")
                print(f"📦 Versão disponível: {latest_version}")
                
                if latest_version > self.current_version:
                    # Encontrar o asset (arquivo zip)
                    assets = data.get("assets", [])
                    download_url = None
                    
                    for asset in assets:
                        if asset.get("name", "").endswith(".zip"):
                            download_url = asset.get("browser_download_url")
                            break
                    
                    print(f"✅ Atualização disponível! Download: {download_url}")
                    
                    self.update_available.emit({
                        "version": latest_version,
                        "download_url": download_url,
                        "changelog": data.get("body", "Nova versão disponível"),
                        "release_date": data.get("published_at", ""),
                        "release_name": data.get("name", "")
                    })
                else:
                    print("ℹ️ Sistema já está atualizado")
                    self.no_update.emit()
            else:
                print(f"❌ GitHub retornou status: {response.status_code}")
                self.no_update.emit()
                
        except Exception as e:
            print(f"❌ Erro ao verificar: {e}")
            self.error.emit(str(e))


class UpdateDownloader(QThread):
    """Baixa a atualização"""
    
    progress = Signal(int)
    finished = Signal(str)
    error = Signal(str)
    
    def __init__(self, download_url):
        super().__init__()
        self.download_url = download_url
    
    def run(self):
        try:
            print(f"📥 Baixando de: {self.download_url}")
            
            temp_dir = os.path.join(os.environ.get('TEMP', '/tmp'), 'project_parallel_update')
            os.makedirs(temp_dir, exist_ok=True)
            
            download_path = os.path.join(temp_dir, 'update.zip')
            
            response = requests.get(self.download_url, stream=True)
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(download_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        progress = int((downloaded / total_size) * 100)
                        self.progress.emit(progress)
            
            print(f"✅ Download concluído: {download_path}")
            self.finished.emit(download_path)
            
        except Exception as e:
            print(f"❌ Erro no download: {e}")
            self.error.emit(str(e))


class UpdateInstaller:
    """Instala a atualização - Versão SEGURA com Backup Completo"""
    
    PROTECTED_ITEMS = [
        'backup', 'logs', 'config.ini', '.env', 'database.db', 
        'temp_update', '__pycache__'
    ]
    
    @staticmethod
    def criar_backup_automatico():
        """Cria um backup completo da pasta de instalação"""
        try:
            # Onde o programa está rodando
            if getattr(sys, 'frozen', False):
                current_dir = os.path.dirname(sys.executable)
            else:
                current_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
            
            # Criar pasta de backup com timestamp
            backup_dir = os.path.join(current_dir, 'backup', datetime.now().strftime("%Y%m%d_%H%M%S"))
            os.makedirs(backup_dir, exist_ok=True)
            
            print(f"📦 Criando backup completo em: {backup_dir}")
            
            # Itens a serem excluídos do backup
            itens_para_excluir = [
                'backup', 'temp_update', '__pycache__', 'logs'
            ]
            
            # Copiar tudo do diretório atual para o backup
            for item in os.listdir(current_dir):
                src_path = os.path.join(current_dir, item)
                
                if item in itens_para_excluir:
                    print(f"   ⏭️ Pulando: {item}")
                    continue
                
                if item.endswith('.pyc') or item.endswith('.log'):
                    print(f"   ⏭️ Pulando: {item}")
                    continue
                
                dst_path = os.path.join(backup_dir, item)
                
                try:
                    if os.path.isdir(src_path):
                        shutil.copytree(src_path, dst_path)
                        print(f"   ✅ Pasta: {item}")
                    else:
                        shutil.copy2(src_path, dst_path)
                        print(f"   ✅ Arquivo: {item}")
                except Exception as e:
                    print(f"   ⚠️ Erro ao copiar {item}: {e}")
            
            print(f"✅ Backup completo concluído em: {backup_dir}")
            return backup_dir
            
        except Exception as e:
            print(f"❌ Erro ao criar backup: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    @staticmethod
    def install_update(update_file):
        try:
            print("📦 Criando backup de segurança completo...")
            backup_dir = UpdateInstaller.criar_backup_automatico()
            if backup_dir:
                print(f"📦 Backup criado em: {backup_dir}")
            
            # Pasta atual do programa
            if getattr(sys, 'frozen', False):
                current_dir = os.path.dirname(sys.executable)
            else:
                current_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
            
            print(f"📁 Instalando em: {current_dir}")
            
            # Criar pasta temporária
            temp_dir = os.path.join(current_dir, 'temp_update')
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            os.makedirs(temp_dir)
            
            # Extrair o ZIP
            with zipfile.ZipFile(update_file, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            # Procurar a pasta 'desktop'
            desktop_dir = None
            for root, dirs, files in os.walk(temp_dir):
                if 'desktop' in dirs:
                    desktop_dir = os.path.join(root, 'desktop')
                    break
            
            if desktop_dir and os.path.exists(desktop_dir):
                print(f"📁 Atualizando arquivos de: {desktop_dir}")
                
                arquivos_atualizados = 0
                for root, dirs, files in os.walk(desktop_dir):
                    for file in files:
                        if file in UpdateInstaller.PROTECTED_ITEMS:
                            print(f"   ⚠️ Pulando arquivo protegido: {file}")
                            continue
                        
                        src_file = os.path.join(root, file)
                        rel_path = os.path.relpath(src_file, desktop_dir)
                        dst_file = os.path.join(current_dir, rel_path)
                        
                        dst_dir_protegido = False
                        for protected in UpdateInstaller.PROTECTED_ITEMS:
                            if protected in dst_file:
                                dst_dir_protegido = True
                                break
                        
                        if dst_dir_protegido:
                            print(f"   ⚠️ Pulando arquivo em pasta protegida: {rel_path}")
                            continue
                        
                        os.makedirs(os.path.dirname(dst_file), exist_ok=True)
                        shutil.copy2(src_file, dst_file)
                        print(f"   ✅ {rel_path}")
                        arquivos_atualizados += 1
                
                print(f"📊 Total de arquivos atualizados: {arquivos_atualizados}")
            else:
                print("⚠️ Pasta 'desktop' não encontrada no ZIP")
            
            # Limpar pasta temporária
            shutil.rmtree(temp_dir)
            
            # Remover arquivo ZIP da atualização
            if os.path.exists(update_file):
                os.remove(update_file)
            
            print("✅ Instalação concluída")
            return True, f"Atualização instalada com sucesso! Backup em: {backup_dir}"
            
        except Exception as e:
            print(f"❌ Erro na instalação: {e}")
            import traceback
            traceback.print_exc()
            return False, str(e)
        