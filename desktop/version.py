# version.py
import json
import os

VERSION = "1.1.3"

def get_version():
    """Retorna a versão atual do sistema"""
    try:
        version_file = os.path.join(os.path.dirname(__file__), 'version.json')
        if os.path.exists(version_file):
            with open(version_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('version', VERSION)
    except Exception as e:
        print(f"Erro ao ler versão: {e}")
    return VERSION

def get_release_date():
    """Retorna a data da versão atual"""
    try:
        version_file = os.path.join(os.path.dirname(__file__), 'version.json')
        with open(version_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('release_date', '')
    except:
        return ''

def get_changelog():
    """Retorna o changelog da versão atual"""
    try:
        version_file = os.path.join(os.path.dirname(__file__), 'version.json')
        with open(version_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('changelog', '')
    except:
        return ''

CURRENT_VERSION = get_version()