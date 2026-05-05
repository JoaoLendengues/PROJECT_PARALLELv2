from pathlib import Path
import os
import sys


APP_DIR = Path(__file__).resolve().parent


def get_runtime_dir() -> Path:
    """Retorna a pasta onde os recursos empacotados estao disponiveis."""
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
    return APP_DIR


def get_install_dir() -> Path:
    """Retorna a pasta da instalacao do aplicativo."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return APP_DIR


def get_resource_path(*parts: str) -> Path:
    """Monta o caminho de um recurso incluido no build."""
    return get_runtime_dir().joinpath(*parts)


def get_env_file_path() -> Path:
    """Prefere o .env externo da instalacao e usa o empacotado como fallback."""
    install_env = get_install_dir() / ".env"
    if install_env.exists():
        return install_env
    return get_resource_path(".env")


def get_user_config_dir() -> Path:
    """Retorna a pasta de configuracoes do usuario para dados persistentes locais."""
    base_dir = (
        os.getenv("LOCALAPPDATA")
        or os.getenv("APPDATA")
        or str(get_install_dir())
    )
    return Path(base_dir) / "ProjectParallel"


def get_accessibility_config_path() -> Path:
    """Retorna o arquivo local usado para persistir a acessibilidade entre sessoes."""
    return get_user_config_dir() / "accessibility.json"
