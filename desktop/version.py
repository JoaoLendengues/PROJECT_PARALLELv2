# version.py
import json

from app_paths import get_resource_path


def _load_version_data():
    version_file = get_resource_path("version.json")
    with open(version_file, "r", encoding="utf-8") as file:
        return json.load(file)


def get_version():
    """Retorna apenas o numero da versao."""
    try:
        return _load_version_data().get("version", "1.0.0")
    except Exception as error:
        print(f"Erro ao ler versao: {error}")
        return "1.0.0"


def get_release_date():
    """Retorna a data da versao."""
    try:
        return _load_version_data().get("release_date", "")
    except Exception:
        return ""


def get_changelog():
    """Retorna o changelog."""
    try:
        return _load_version_data().get("changelog", "")
    except Exception:
        return ""


CURRENT_VERSION = get_version()
