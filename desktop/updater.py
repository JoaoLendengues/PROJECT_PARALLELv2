import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path

import requests
from PySide6.QtCore import QThread, Signal

from version import CURRENT_VERSION


def _parse_version(version: str) -> tuple[int, ...]:
    parts = [int(part) for part in re.findall(r"\d+", version or "0")]
    return tuple(parts or [0])


def _find_portable_asset(assets):
    zip_assets = [asset for asset in assets if asset.get("name", "").lower().endswith(".zip")]
    if not zip_assets:
        return None

    preferred_markers = ("portable", "windows", "win64")

    for marker in preferred_markers:
        for asset in zip_assets:
            asset_name = asset.get("name", "").lower()
            if marker in asset_name:
                return asset

    return zip_assets[0]


def _find_installer_asset(assets):
    exe_assets = [asset for asset in assets if asset.get("name", "").lower().endswith(".exe")]
    if not exe_assets:
        return None

    preferred_markers = ("setup", "installer")

    for marker in preferred_markers:
        for asset in exe_assets:
            asset_name = asset.get("name", "").lower()
            if marker in asset_name:
                return asset

    return exe_assets[0]


class UpdateChecker(QThread):
    """Verifica se ha atualizacoes disponiveis no GitHub Releases."""

    update_available = Signal(dict)
    no_update = Signal()
    error = Signal(str)

    def __init__(self):
        super().__init__()
        self.current_version = CURRENT_VERSION
        self.update_url = (
            "https://api.github.com/repos/JoaoLendengues/PROJECT_PARALLELv2/releases/latest"
        )

    def run(self):
        try:
            response = requests.get(
                self.update_url,
                timeout=15,
                headers={
                    "Accept": "application/vnd.github+json",
                    "User-Agent": "ProjectParallel-Updater",
                },
            )
            response.raise_for_status()

            data = response.json()
            latest_version = (data.get("tag_name") or "0.0.0").lstrip("vV")

            if _parse_version(latest_version) <= _parse_version(self.current_version):
                self.no_update.emit()
                return

            assets = data.get("assets", [])
            installer_asset = _find_installer_asset(assets)
            portable_asset = _find_portable_asset(assets)
            selected_asset = installer_asset or portable_asset

            if not selected_asset:
                self.error.emit(
                    "A release mais recente nao possui um instalador nem um ZIP compativel."
                )
                return

            self.update_available.emit(
                {
                    "version": latest_version,
                    "download_url": selected_asset.get("browser_download_url"),
                    "asset_name": selected_asset.get("name", ""),
                    "asset_kind": "installer" if selected_asset == installer_asset else "portable",
                    "changelog": data.get("body", "Nova versao disponivel."),
                    "release_date": data.get("published_at", ""),
                    "release_name": data.get("name", ""),
                }
            )
        except Exception as error:
            self.error.emit(str(error))


class UpdateDownloader(QThread):
    """Baixa o pacote da atualizacao."""

    progress = Signal(int)
    finished = Signal(str)
    error = Signal(str)

    def __init__(self, download_url, asset_name=""):
        super().__init__()
        self.download_url = download_url
        self.asset_name = Path(asset_name).name or "update.bin"

    def run(self):
        try:
            temp_dir = Path(tempfile.mkdtemp(prefix="project_parallel_download_"))
            download_path = temp_dir / self.asset_name

            response = requests.get(
                self.download_url,
                stream=True,
                timeout=60,
                headers={"User-Agent": "ProjectParallel-Updater"},
            )
            response.raise_for_status()

            total_size = int(response.headers.get("content-length", 0))
            downloaded = 0

            with open(download_path, "wb") as file:
                for chunk in response.iter_content(chunk_size=8192):
                    if not chunk:
                        continue

                    file.write(chunk)
                    downloaded += len(chunk)

                    if total_size > 0:
                        self.progress.emit(int((downloaded / total_size) * 100))

            if total_size == 0:
                self.progress.emit(100)

            self.finished.emit(str(download_path))
        except Exception as error:
            self.error.emit(str(error))


class UpdateInstaller:
    """Instala atualizacoes para o build empacotado do Windows."""

    PROTECTED_FILES = (".env", "config.ini", "database.db")
    PROTECTED_DIRS = ("backup", "logs", "temp_update", "__pycache__")

    @staticmethod
    def install_update(update_file):
        try:
            if not getattr(sys, "frozen", False):
                return (
                    False,
                    "A atualizacao automatica do beta funciona apenas no executavel instalado.",
                )

            app_dir = Path(sys.executable).resolve().parent
            backup_dir = UpdateInstaller._create_backup(app_dir)

            update_path = Path(update_file)
            if update_path.suffix.lower() == ".exe":
                script_path = UpdateInstaller._write_installer_update_script(
                    app_dir=app_dir,
                    installer_file=update_path,
                    process_id=os.getpid(),
                )
            else:
                staging_dir = Path(tempfile.mkdtemp(prefix="project_parallel_stage_"))
                with zipfile.ZipFile(update_path, "r") as archive:
                    archive.extractall(staging_dir)

                payload_dir = UpdateInstaller._find_payload_dir(staging_dir)
                if payload_dir is None:
                    shutil.rmtree(staging_dir, ignore_errors=True)
                    return False, "O ZIP da release nao contem o build empacotado esperado."

                script_path = UpdateInstaller._write_portable_update_script(
                    app_dir=app_dir,
                    staging_dir=staging_dir,
                    payload_dir=payload_dir,
                    process_id=os.getpid(),
                )

            UpdateInstaller._launch_update_script(script_path)

            return (
                True,
                "Atualizacao pronta. O sistema sera fechado para concluir a instalacao "
                f"e reabrir em seguida.\n\nBackup: {backup_dir}",
            )
        except Exception as error:
            return False, str(error)

    @staticmethod
    def _create_backup(app_dir: Path) -> str:
        backup_dir = app_dir / "backup" / datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir.mkdir(parents=True, exist_ok=True)

        for item_name in ("main.exe", "_internal"):
            source = app_dir / item_name
            destination = backup_dir / item_name

            if not source.exists():
                continue

            if source.is_dir():
                shutil.copytree(source, destination, dirs_exist_ok=True)
            else:
                shutil.copy2(source, destination)

        return str(backup_dir)

    @staticmethod
    def _find_payload_dir(staging_dir: Path):
        for root, _, _ in os.walk(staging_dir):
            root_path = Path(root)
            if (root_path / "main.exe").exists() and (root_path / "_internal").exists():
                return root_path
        return None

    @staticmethod
    def _launch_update_script(script_path: Path):
        flags = 0
        for flag_name in ("CREATE_NEW_PROCESS_GROUP", "DETACHED_PROCESS", "CREATE_NO_WINDOW"):
            flags |= getattr(subprocess, flag_name, 0)

        subprocess.Popen(
            ["cmd", "/c", str(script_path)],
            creationflags=flags,
            close_fds=True,
        )

    @staticmethod
    def _write_installer_update_script(app_dir: Path, installer_file: Path, process_id: int):
        script_path = Path(tempfile.gettempdir()) / (
            f"project_parallel_apply_update_{datetime.now().strftime('%Y%m%d_%H%M%S')}.bat"
        )
        log_path = app_dir / "update.log"

        script_content = "\n".join(
            [
                "@echo off",
                "setlocal enableextensions",
                f'set "APP_DIR={app_dir}"',
                f'set "INSTALLER_FILE={installer_file}"',
                f'set "PROCESS_ID={process_id}"',
                f'set "LOG_FILE={log_path}"',
                'for %%I in ("%INSTALLER_FILE%") do set "INSTALLER_DIR=%%~dpI"',
                'echo [%DATE% %TIME%] Iniciando atualizacao pelo setup > "%LOG_FILE%"',
                "",
                ":wait_for_exit",
                'tasklist /FI "PID eq %PROCESS_ID%" | find "%PROCESS_ID%" >nul',
                "if not errorlevel 1 (",
                "    timeout /t 1 /nobreak >nul",
                "    goto wait_for_exit",
                ")",
                "",
                'echo [%DATE% %TIME%] Processo principal encerrado >> "%LOG_FILE%"',
                "timeout /t 2 /nobreak >nul",
                'if not exist "%INSTALLER_FILE%" goto install_error',
                'echo [%DATE% %TIME%] Executando instalador silencioso >> "%LOG_FILE%"',
                '"%INSTALLER_FILE%" /SP- /VERYSILENT /SUPPRESSMSGBOXES /NORESTART /CLOSEAPPLICATIONS /FORCECLOSEAPPLICATIONS /LOG /LOGCLOSEAPPLICATIONS /DIR="%APP_DIR%" >> "%LOG_FILE%" 2>&1',
                'set "INSTALL_EXIT=%ERRORLEVEL%"',
                'echo [%DATE% %TIME%] Instalador retornou %INSTALL_EXIT% >> "%LOG_FILE%"',
                'if not "%INSTALL_EXIT%"=="0" goto install_error',
                'if not exist "%APP_DIR%\\main.exe" goto install_error',
                'echo [%DATE% %TIME%] Instalacao concluida. Reiniciando aplicativo >> "%LOG_FILE%"',
                'start "" /D "%APP_DIR%" "%APP_DIR%\\main.exe"',
                'rmdir /s /q "%INSTALLER_DIR%" >> "%LOG_FILE%" 2>&1',
                'del "%~f0"',
                "exit /b 0",
                "",
                ":install_error",
                'echo [%DATE% %TIME%] Falha ao instalar a atualizacao >> "%LOG_FILE%"',
                "exit /b 1",
            ]
        )

        script_path.write_text(script_content, encoding="utf-8", newline="\r\n")
        return script_path

    @staticmethod
    def _write_portable_update_script(
        app_dir: Path, staging_dir: Path, payload_dir: Path, process_id: int
    ):
        script_path = Path(tempfile.gettempdir()) / (
            f"project_parallel_apply_update_{datetime.now().strftime('%Y%m%d_%H%M%S')}.bat"
        )
        log_path = app_dir / "update.log"

        exclude_files = " ".join(f"/XF {name}" for name in UpdateInstaller.PROTECTED_FILES)
        exclude_dirs = " ".join(f"/XD {name}" for name in UpdateInstaller.PROTECTED_DIRS)

        script_content = "\n".join(
            [
                "@echo off",
                "setlocal enableextensions",
                f'set "APP_DIR={app_dir}"',
                f'set "STAGING_DIR={staging_dir}"',
                f'set "PAYLOAD_DIR={payload_dir}"',
                f'set "PROCESS_ID={process_id}"',
                f'set "LOG_FILE={log_path}"',
                'echo [%DATE% %TIME%] Iniciando atualizacao > "%LOG_FILE%"',
                "",
                ":wait_for_exit",
                'tasklist /FI "PID eq %PROCESS_ID%" | find "%PROCESS_ID%" >nul',
                "if not errorlevel 1 (",
                "    timeout /t 1 /nobreak >nul",
                "    goto wait_for_exit",
                ")",
                "",
                'echo [%DATE% %TIME%] Processo principal encerrado >> "%LOG_FILE%"',
                "timeout /t 2 /nobreak >nul",
                'set /a COPY_ATTEMPT=0',
                "",
                ":copy_files",
                'set /a COPY_ATTEMPT+=1',
                'echo [%DATE% %TIME%] Tentativa de copia %COPY_ATTEMPT% >> "%LOG_FILE%"',
                'if exist "%APP_DIR%\\main.exe" del /f /q "%APP_DIR%\\main.exe" >> "%LOG_FILE%" 2>&1',
                'if exist "%APP_DIR%\\_internal" rmdir /s /q "%APP_DIR%\\_internal" >> "%LOG_FILE%" 2>&1',
                "",
                f'robocopy "%PAYLOAD_DIR%" "%APP_DIR%" /E /R:2 /W:1 /NFL /NDL /NJH /NJS /NP {exclude_files} {exclude_dirs} >> "%LOG_FILE%" 2>&1',
                'set "ROBOCOPY_EXIT=%ERRORLEVEL%"',
                'echo [%DATE% %TIME%] Robocopy retornou %ROBOCOPY_EXIT% >> "%LOG_FILE%"',
                "if %ROBOCOPY_EXIT% GEQ 8 (",
                "    if %COPY_ATTEMPT% LSS 6 (",
                "        timeout /t 2 /nobreak >nul",
                "        goto copy_files",
                "    )",
                "    goto copy_error",
                ")",
                'if not exist "%APP_DIR%\\main.exe" goto copy_error',
                "",
                'echo [%DATE% %TIME%] Arquivos copiados com sucesso >> "%LOG_FILE%"',
                'start "" /D "%APP_DIR%" "%APP_DIR%\\main.exe"',
                'echo [%DATE% %TIME%] Aplicativo reiniciado >> "%LOG_FILE%"',
                'rmdir /s /q "%STAGING_DIR%"',
                'del "%~f0"',
                "exit /b 0",
                "",
                ":copy_error",
                'echo [%DATE% %TIME%] Falha ao copiar os arquivos da atualizacao >> "%LOG_FILE%"',
                "exit /b 1",
            ]
        )

        script_path.write_text(script_content, encoding="utf-8", newline="\r\n")
        return script_path
