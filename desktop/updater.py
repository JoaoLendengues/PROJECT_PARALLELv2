import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
import json
from datetime import datetime
from pathlib import Path

import requests
from PySide6.QtCore import QThread, Signal

from version import CURRENT_VERSION
from app_paths import get_update_log_path, get_update_state_path


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


def _load_update_state():
    state_path = get_update_state_path()
    if not state_path.exists():
        return {}

    try:
        return json.loads(state_path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_update_state(state: dict):
    state_path = get_update_state_path()
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def finalize_pending_update():
    """Confirma o estado de uma atualização pendente no próximo startup."""
    state = _load_update_state()
    if not state:
        return None

    status = state.get("status")
    target_version = str(state.get("target_version", "")).strip()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if status == "applied" and target_version == CURRENT_VERSION:
        state["status"] = "completed"
        state["completed_at"] = timestamp
        _save_update_state(state)
        return {
            "status": "completed",
            "message": f"Atualização concluída com sucesso para a versão {CURRENT_VERSION}.",
        }

    if status in {"pending", "applying"} and target_version and target_version != CURRENT_VERSION:
        state["status"] = "failed"
        state["failed_at"] = timestamp
        state.setdefault(
            "last_error",
            "A atualização anterior não concluiu antes da reabertura do aplicativo.",
        )
        _save_update_state(state)
        return {
            "status": "failed",
            "message": (
                f"A atualização para a versão {target_version} não foi concluída. "
                f"Consulte o log em {get_update_log_path()}."
            ),
        }

    if status == "failed" and not state.get("startup_notified_at"):
        state["startup_notified_at"] = timestamp
        _save_update_state(state)

        last_error = state.get("last_error") or "Falha ao aplicar a atualização."
        rollback_applied = state.get("rollback_applied")
        rollback_note = ""
        if rollback_applied is True:
            rollback_note = " O sistema foi restaurado a partir do backup."
        elif rollback_applied is False:
            rollback_note = " O rollback não pôde ser concluído automaticamente."

        return {
            "status": "failed",
            "message": (
                f"A atualização para a versão {target_version or 'informada'} falhou. "
                f"{last_error}.{rollback_note} Consulte o log em {get_update_log_path()}."
            ).replace("..", "."),
        }

    return None


class UpdateChecker(QThread):
    """Verifica se há atualizações disponíveis no GitHub Releases."""

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
            # Prefer the portable package so legacy clients from 1.1.12 can
            # bridge safely without depending on the silent installer path.
            selected_asset = portable_asset or installer_asset

            if not selected_asset:
                self.error.emit(
                    "A release mais recente não possui um instalador nem um ZIP compatível."
                )
                return

            self.update_available.emit(
                {
                    "version": latest_version,
                    "download_url": selected_asset.get("browser_download_url"),
                    "asset_name": selected_asset.get("name", ""),
                    "asset_kind": "installer" if selected_asset == installer_asset else "portable",
                    "changelog": data.get("body", "Nova versão disponível."),
                    "release_date": data.get("published_at", ""),
                    "release_name": data.get("name", ""),
                }
            )
        except Exception as error:
            self.error.emit(str(error))


class UpdateDownloader(QThread):
    """Baixa o pacote da atualização."""

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
    def _append_update_log(log_path: Path, message: str):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a", encoding="utf-8") as log_file:
            log_file.write(f"[{timestamp}] {message}\n")

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
                    "A atualização automática do beta funciona apenas no executável instalado.",
                )

            app_dir = Path(sys.executable).resolve().parent
            backup_dir = UpdateInstaller._create_backup(app_dir)
            log_path = get_update_log_path()
            log_path.parent.mkdir(parents=True, exist_ok=True)
            log_path.write_text("", encoding="utf-8")
            UpdateInstaller._append_update_log(
                log_path,
                f"Iniciando atualização a partir do arquivo {update_file}.",
            )

            update_path = Path(update_file)
            if update_path.suffix.lower() == ".exe":
                UpdateInstaller._append_update_log(log_path, "Modo de atualização por instalador detectado.")
                script_path = UpdateInstaller._write_installer_update_script(
                    app_dir=app_dir,
                    installer_file=update_path,
                    process_id=os.getpid(),
                )
            else:
                UpdateInstaller._append_update_log(log_path, "Modo de atualização portátil detectado.")
                staging_dir = Path(tempfile.mkdtemp(prefix="project_parallel_stage_"))
                with zipfile.ZipFile(update_path, "r") as archive:
                    archive.extractall(staging_dir)
                UpdateInstaller._append_update_log(
                    log_path,
                    f"Pacote extraído para staging em {staging_dir}.",
                )

                payload_dir = UpdateInstaller._find_payload_dir(staging_dir)
                if payload_dir is None:
                    UpdateInstaller._append_update_log(
                        log_path,
                        "Falha ao localizar um payload válido dentro do ZIP baixado.",
                    )
                    shutil.rmtree(staging_dir, ignore_errors=True)
                    return False, "O ZIP da release não contém o build empacotado esperado."

                validation_error = UpdateInstaller._validate_payload(payload_dir)
                if validation_error:
                    UpdateInstaller._append_update_log(
                        log_path,
                        f"Falha de validação do payload: {validation_error}",
                    )
                    shutil.rmtree(staging_dir, ignore_errors=True)
                    return False, validation_error

                target_version = UpdateInstaller._extract_version_from_asset(update_path.name)
                UpdateInstaller._append_update_log(
                    log_path,
                    f"Payload validado com sucesso para a versão alvo {target_version}.",
                )
                UpdateInstaller._write_pending_state(
                    target_version=target_version,
                    backup_dir=backup_dir,
                    asset_name=update_path.name,
                )
                UpdateInstaller._launch_update_helper(
                    app_dir=app_dir,
                    staging_dir=staging_dir,
                    payload_dir=payload_dir,
                    backup_dir=Path(backup_dir),
                    process_id=os.getpid(),
                    target_version=target_version,
                )
                UpdateInstaller._append_update_log(
                    log_path,
                    "Helper de atualização iniciado com sucesso. A aplicação principal será encerrada.",
                )

                return (
                    True,
                    "Atualização pronta. O sistema será fechado para concluir a instalação "
                    f"e reabrir em seguida.\n\nBackup: {backup_dir}",
                )

            UpdateInstaller._launch_update_script(script_path)
            UpdateInstaller._append_update_log(
                log_path,
                "Script silencioso de atualização iniciado com sucesso.",
            )

            return (
                True,
                "Atualização pronta. O sistema será fechado para concluir a instalação "
                f"e reabrir em seguida.\n\nBackup: {backup_dir}",
            )
        except Exception as error:
            try:
                UpdateInstaller._append_update_log(
                    get_update_log_path(),
                    f"Falha antes da aplicação da atualização: {error}",
                )
            except Exception:
                pass
            return False, str(error)

    @staticmethod
    def _create_backup(app_dir: Path) -> str:
        backup_dir = app_dir / "backup" / datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir.mkdir(parents=True, exist_ok=True)

        for item_name in ("main.exe", "_internal", "update_helper.exe"):
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
    def _validate_payload(payload_dir: Path):
        required_entries = ("main.exe", "_internal", "update_helper.exe")
        missing_entries = [entry for entry in required_entries if not (payload_dir / entry).exists()]
        if missing_entries:
            return (
                "O pacote da atualização está incompleto. "
                f"Itens ausentes: {', '.join(missing_entries)}."
            )
        return None

    @staticmethod
    def _extract_version_from_asset(asset_name: str) -> str:
        match = re.search(r"v?(\d+(?:\.\d+)+)", asset_name or "")
        if match:
            return match.group(1)
        return CURRENT_VERSION

    @staticmethod
    def _write_pending_state(target_version: str, backup_dir: str, asset_name: str):
        state = {
            "status": "pending",
            "from_version": CURRENT_VERSION,
            "target_version": target_version,
            "asset_name": asset_name,
            "backup_dir": backup_dir,
            "started_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "startup_notified_at": None,
            "last_error": None,
            "rollback_applied": None,
        }
        _save_update_state(state)

    @staticmethod
    def _helper_executable_path(app_dir: Path) -> Path:
        return app_dir / "update_helper.exe"

    @staticmethod
    def _launch_update_helper(
        app_dir: Path,
        staging_dir: Path,
        payload_dir: Path,
        backup_dir: Path,
        process_id: int,
        target_version: str,
    ):
        payload_helper = payload_dir / "update_helper.exe"
        installed_helper = UpdateInstaller._helper_executable_path(app_dir)
        helper_source = payload_helper if payload_helper.exists() else installed_helper

        if not helper_source.exists():
            raise FileNotFoundError(
                "O helper de atualização não foi encontrado nem na instalação atual "
                f"({installed_helper}) nem no pacote baixado ({payload_helper})."
            )

        helper_runtime_dir = Path(tempfile.mkdtemp(prefix="project_parallel_helper_"))
        helper_runtime = helper_runtime_dir / "update_helper.exe"
        shutil.copy2(helper_source, helper_runtime)

        state_path = get_update_state_path()
        log_path = get_update_log_path()

        command = [
            str(helper_runtime),
            "--app-dir",
            str(app_dir),
            "--payload-dir",
            str(payload_dir),
            "--staging-dir",
            str(staging_dir),
            "--backup-dir",
            str(backup_dir),
            "--wait-pid",
            str(process_id),
            "--target-version",
            str(target_version),
            "--state-path",
            str(state_path),
            "--log-path",
            str(log_path),
        ]

        flags = 0
        for flag_name in ("CREATE_NEW_PROCESS_GROUP", "DETACHED_PROCESS", "CREATE_NO_WINDOW"):
            flags |= getattr(subprocess, flag_name, 0)

        subprocess.Popen(command, creationflags=flags, close_fds=True)

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
        app_dir_safe = UpdateInstaller._to_cmd_safe_path(app_dir)
        installer_file_safe = UpdateInstaller._to_cmd_safe_path(installer_file)

        script_content = "\n".join(
            [
                "$ErrorActionPreference = 'Stop'",
                f"$AppDir = '{app_dir_safe}'",
                f"$InstallerFile = '{installer_file_safe}'",
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
                "$waitCount = 0",
                "while (Get-Process -Id $ProcessIdToWait -ErrorAction SilentlyContinue) {",
                "    Start-Sleep -Milliseconds 500",
                "    $waitCount += 1",
                "    if ($waitCount -ge 40) {",
                "        Write-UpdateLog 'Processo principal ainda ativo apos 20 segundos. Forcando encerramento.'",
                "        Stop-Process -Id $ProcessIdToWait -Force -ErrorAction SilentlyContinue",
                "        Start-Sleep -Seconds 2",
                "        break",
                "    }",
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
                "try {",
                "    Start-Process -FilePath (Join-Path $AppDir 'main.exe') -WorkingDirectory $AppDir",
                "    Write-UpdateLog 'Aplicativo reiniciado com sucesso'",
                "} catch {",
                "    Write-UpdateLog \"Falha ao reiniciar aplicativo: $($_.Exception.Message)\"",
                "    exit 1",
                "}",
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
        app_dir_safe = UpdateInstaller._to_cmd_safe_path(app_dir)
        staging_dir_safe = UpdateInstaller._to_cmd_safe_path(staging_dir)
        payload_dir_safe = UpdateInstaller._to_cmd_safe_path(payload_dir)

        script_content = "\n".join(
            [
                "$ErrorActionPreference = 'Stop'",
                f"$AppDir = '{app_dir_safe}'",
                f"$StagingDir = '{staging_dir_safe}'",
                f"$PayloadDir = '{payload_dir_safe}'",
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
                "$waitCount = 0",
                "while (Get-Process -Id $ProcessIdToWait -ErrorAction SilentlyContinue) {",
                "    Start-Sleep -Milliseconds 500",
                "    $waitCount += 1",
                "    if ($waitCount -ge 40) {",
                "        Write-UpdateLog 'Processo principal ainda ativo apos 20 segundos. Forcando encerramento.'",
                "        Stop-Process -Id $ProcessIdToWait -Force -ErrorAction SilentlyContinue",
                "        Start-Sleep -Seconds 2",
                "        break",
                "    }",
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
                "try {",
                "    Start-Process -FilePath (Join-Path $AppDir 'main.exe') -WorkingDirectory $AppDir",
                "    Write-UpdateLog 'Aplicativo reiniciado'",
                "} catch {",
                "    Write-UpdateLog \"Falha ao reiniciar aplicativo: $($_.Exception.Message)\"",
                "    exit 1",
                "}",
                "if (Test-Path $StagingDir) {",
                "    Remove-Item $StagingDir -Recurse -Force -ErrorAction SilentlyContinue",
                "}",
                "Remove-Item $PSCommandPath -Force -ErrorAction SilentlyContinue",
                "exit 0",
            ]
        )

        script_path.write_text(script_content, encoding="utf-8-sig", newline="\r\n")
        return script_path
