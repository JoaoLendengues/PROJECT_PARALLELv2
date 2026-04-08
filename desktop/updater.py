import requests
import json
import os
import sys
import subprocess
import shutil
from datetime import datetime
from PySide6.QtCore import QThread, Signal


class UpdateChecker(QThread):
    """Thread para verificar atualizações em segundo plano"""
    
    update_available = Signal(dict)
    no_update = Signal()
    error = Signal(str)
    
    def __init__(self, current_version="1.0.0"):
        super().__init__()
        self.current_version = current_version
        # Altere para o seu repositório
        self.update_url = "https://api.github.com/repos/JoaoLendengues/PROJECT_PARALLELv2/releases/latest"
    
    def run(self):
        try:
            response = requests.get(self.update_url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                latest_version = data.get("tag_name", "0.0.0").replace("v", "")
                
                if self._compare_versions(latest_version, self.current_version) > 0:
                    # Nova versão disponível
                    self.update_available.emit({
                        "version": latest_version,
                        "download_url": data.get("assets", [{}])[0].get("browser_download_url", ""),
                        "changelog": data.get("body", "Melhorias e correções de bugs"),
                        "release_date": data.get("published_at", "")
                    })
                else:
                    self.no_update.emit()
            else:
                self.no_update.emit()
                
        except Exception as e:
            self.error.emit(str(e))
    
    def _compare_versions(self, v1, v2):
        v1_parts = [int(x) for x in v1.split('.')]
        v2_parts = [int(x) for x in v2.split('.')]
        
        for i in range(max(len(v1_parts), len(v2_parts))):
            v1_val = v1_parts[i] if i < len(v1_parts) else 0
            v2_val = v2_parts[i] if i < len(v2_parts) else 0
            
            if v1_val > v2_val:
                return 1
            elif v1_val < v2_val:
                return -1
        return 0


class UpdateDownloader(QThread):
    """Thread para baixar atualização"""
    
    progress = Signal(int)
    finished = Signal(str)
    error = Signal(str)
    
    def __init__(self, download_url):
        super().__init__()
        self.download_url = download_url
    
    def run(self):
        try:
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
            
            self.finished.emit(download_path)
            
        except Exception as e:
            self.error.emit(str(e))


class UpdateInstaller:
    """Gerencia a instalação de atualizações"""
    
    @staticmethod
    def install_update(update_file, backup=True):
        try:
            current_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(__file__)
            
            if backup:
                backup_dir = os.path.join(current_dir, 'backup_' + datetime.now().strftime('%Y%m%d_%H%M%S'))
                shutil.copytree(current_dir, backup_dir, dirs_exist_ok=True)
            
            import zipfile
            with zipfile.ZipFile(update_file, 'r') as zip_ref:
                zip_ref.extractall(current_dir)
            
            os.remove(update_file)
            
            return True, "Atualização instalada com sucesso!"
            
        except Exception as e:
            return False, str(e)