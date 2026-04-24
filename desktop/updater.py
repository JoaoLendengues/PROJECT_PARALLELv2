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
    def _get_short_path(path: Path):
        """Retorna um caminho curto do Windows para uso em scripts CMD."""
        try:
            import ctypes

            target = str(path)
            required_size = ctypes.windll.kernel32.GetShortPathNameW(target, None, 0)
            if not required_size:
                return None

            buffer = ctypes.create_unicode_buffer(required_size)
            result = ctypes.windll.kernel32.GetShortPathNameW(target, buffer, required_size)
            if result:
                return buffer.value
        except Exception:
            return None

        return None

    @staticmethod
    def _to_cmd_safe_path(path: Path) -> str:
        """
        Converte caminhos para uma forma ASCII segura em arquivos .bat.
        Isso evita falhas em perfis do Windows com acentos no nome do usuario.
        """
        path = Path(path)

        try:
            resolved = path.resolve(strict=False)
        except Exception:
            resolved = path

        short_path = UpdateInstaller._get_short_path(resolved)
        if short_path:
            return short_path

        parent_short_path = UpdateInstaller._get_short_path(resolved.parent)
        if parent_short_path:
            return str(Path(parent_short_path) / resolved.name)

        return str(resolved)

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

        if script_path.suffix.lower() == ".ps1":
            command = [
                "powershell.exe",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(script_path),
            ]
        else:
            command = ["cmd", "/c", str(script_path)]

        subprocess.Popen(command, creationflags=flags, close_fds=True)

    @staticmethod
    def _write_installer_update_script(app_dir: Path, installer_file: Path, process_id: int):
        script_path = Path(tempfile.gettempdir()) / (
            f"project_parallel_apply_update_{datetime.now().strftime('%Y%m%d_%H%M%S')}.ps1"
        )

        script_content = "\n".join(
            [
                "$ErrorActionPreference = 'Stop'",
                f"$AppDir = '{app_dir}'",
                f"$InstallerFile = '{installer_file}'",
                f"$ProcessIdToWait = {process_id}",
                "$LogFile = Join-Path $AppDir 'update.log'",
                "$InstallerDir = Split-Path -Parent $InstallerFile",
                "",
                "function Write-UpdateLog {",
                "    param([string]$Message)",
                "    $timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'",
                "    Add-Content -Path $LogFile -Value \"[$timestamp] $Message\" -Encoding UTF8",
                "}",
                "",
                "New-Item -ItemType Directory -Path $AppDir -Force | Out-Null",
                "Set-Content -Path $LogFile -Value '' -Encoding UTF8",
                "Write-UpdateLog 'Iniciando atualizacao pelo setup'",
                "",
                "while (Get-Process -Id $ProcessIdToWait -ErrorAction SilentlyContinue) {",
                "    Start-Sleep -Seconds 1",
                "}",
                "",
                "Write-UpdateLog 'Processo principal encerrado'",
                "Start-Sleep -Seconds 2",
                "",
                "if (-not (Test-Path $InstallerFile)) {",
                "    Write-UpdateLog 'Falha ao localizar o instalador baixado'",
                "    exit 1",
                "}",
                "",
                "Write-UpdateLog 'Executando instalador silencioso'",
                "$arguments = @(",
                "    '/SP-',",
                "    '/VERYSILENT',",
                "    '/SUPPRESSMSGBOXES',",
                "    '/NORESTART',",
                "    '/CLOSEAPPLICATIONS',",
                "    '/FORCECLOSEAPPLICATIONS',",
                "    '/LOG',",
                "    '/LOGCLOSEAPPLICATIONS',",
                "    \"/DIR=$AppDir\"",
                ")",
                "$process = Start-Process -FilePath $InstallerFile -ArgumentList $arguments -PassThru -Wait -WindowStyle Hidden",
                "$installExit = $process.ExitCode",
                "Write-UpdateLog \"Instalador retornou $installExit\"",
                "if ($installExit -ne 0) {",
                "    Write-UpdateLog 'Falha ao instalar a atualizacao'",
                "    exit 1",
                "}",
                "if (-not (Test-Path (Join-Path $AppDir 'main.exe'))) {",
                "    Write-UpdateLog 'main.exe nao encontrado apos a instalacao'",
                "    exit 1",
                "}",
                "",
                "Write-UpdateLog 'Instalacao concluida. Reiniciando aplicativo'",
                "Start-Process -FilePath (Join-Path $AppDir 'main.exe') -WorkingDirectory $AppDir",
                "if (Test-Path $InstallerDir) {",
                "    Remove-Item $InstallerDir -Recurse -Force -ErrorAction SilentlyContinue",
                "}",
                "Remove-Item $PSCommandPath -Force -ErrorAction SilentlyContinue",
                "exit 0",
            ]
        )

        script_path.write_text(script_content, encoding="utf-8-sig", newline="\r\n")
        return script_path

    @staticmethod
    def _write_portable_update_script(
        app_dir: Path, staging_dir: Path, payload_dir: Path, process_id: int
    ):
        script_path = Path(tempfile.gettempdir()) / (
            f"project_parallel_apply_update_{datetime.now().strftime('%Y%m%d_%H%M%S')}.ps1"
        )

        script_content = "\n".join(
            [
                "$ErrorActionPreference = 'Stop'",
                f"$AppDir = '{app_dir}'",
                f"$StagingDir = '{staging_dir}'",
                f"$PayloadDir = '{payload_dir}'",
                f"$ProcessIdToWait = {process_id}",
                "$LogFile = Join-Path $AppDir 'update.log'",
                "$ProtectedFiles = @('.env', 'config.ini', 'database.db')",
                "$ProtectedDirs = @('backup', 'logs', 'temp_update', '__pycache__')",
                "",
                "function Write-UpdateLog {",
                "    param([string]$Message)",
                "    $timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'",
                "    Add-Content -Path $LogFile -Value \"[$timestamp] $Message\" -Encoding UTF8",
                "}",
                "",
                "New-Item -ItemType Directory -Path $AppDir -Force | Out-Null",
                "Set-Content -Path $LogFile -Value '' -Encoding UTF8",
                "Write-UpdateLog 'Iniciando atualizacao'",
                "",
                "while (Get-Process -Id $ProcessIdToWait -ErrorAction SilentlyContinue) {",
                "    Start-Sleep -Seconds 1",
                "}",
                "",
                "Write-UpdateLog 'Processo principal encerrado'",
                "Start-Sleep -Seconds 2",
                "",
                "if (Test-Path (Join-Path $AppDir 'main.exe')) {",
                "    Remove-Item (Join-Path $AppDir 'main.exe') -Force -ErrorAction SilentlyContinue",
                "}",
                "if (Test-Path (Join-Path $AppDir '_internal')) {",
                "    Remove-Item (Join-Path $AppDir '_internal') -Recurse -Force -ErrorAction SilentlyContinue",
                "}",
                "",
                "foreach ($item in Get-ChildItem $PayloadDir -Force) {",
                "    if ($ProtectedFiles -contains $item.Name) { continue }",
                "    if ($item.PSIsContainer -and ($ProtectedDirs -contains $item.Name)) { continue }",
                "",
                "    $destination = Join-Path $AppDir $item.Name",
                "    Copy-Item -Path $item.FullName -Destination $destination -Recurse -Force",
                "}",
                "",
                "if (-not (Test-Path (Join-Path $AppDir 'main.exe'))) {",
                "    Write-UpdateLog 'Falha ao copiar os arquivos da atualizacao'",
                "    exit 1",
                "}",
                "",
                "Write-UpdateLog 'Arquivos copiados com sucesso'",
                "Start-Process -FilePath (Join-Path $AppDir 'main.exe') -WorkingDirectory $AppDir",
                "Write-UpdateLog 'Aplicativo reiniciado'",
                "if (Test-Path $StagingDir) {",
                "    Remove-Item $StagingDir -Recurse -Force -ErrorAction SilentlyContinue",
                "}",
                "Remove-Item $PSCommandPath -Force -ErrorAction SilentlyContinue",
                "exit 0",
            ]
        )

        script_path.write_text(script_content, encoding="utf-8-sig", newline="\r\n")
        return script_path
