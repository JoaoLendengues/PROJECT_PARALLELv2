import argparse
import json
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

try:
    import psutil
except Exception:  # pragma: no cover - fallback simples
    psutil = None


PROTECTED_FILES = {".env", "config.ini", "database.db"}
PROTECTED_DIRS = {"backup", "logs", "temp_update", "__pycache__"}


def _timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def write_log(log_path: Path, message: str):
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as log_file:
        log_file.write(f"[{_timestamp()}] {message}\n")


def load_state(state_path: Path) -> dict:
    if not state_path.exists():
        return {}

    try:
        return json.loads(state_path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_state(state_path: Path, data: dict):
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def update_state(state_path: Path, **changes):
    state = load_state(state_path)
    state.update(changes)
    save_state(state_path, state)


def wait_for_process(process_id: int, timeout_seconds: int, log_path: Path):
    if not process_id:
        return

    if psutil is None:
        write_log(log_path, "psutil indisponível; aguardando tempo fixo antes de aplicar a atualização.")
        time.sleep(min(timeout_seconds, 5))
        return

    try:
        process = psutil.Process(process_id)
    except psutil.Error:
        write_log(log_path, f"Processo principal {process_id} já estava encerrado.")
        return

    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        if not process.is_running():
            write_log(log_path, f"Processo principal {process_id} encerrado normalmente.")
            return
        time.sleep(0.5)

    write_log(log_path, f"Processo principal {process_id} excedeu o timeout. Encerrando à força.")
    try:
        process.kill()
        process.wait(timeout=5)
        write_log(log_path, f"Processo principal {process_id} encerrado com sucesso após kill.")
    except psutil.Error as error:
        write_log(log_path, f"Falha ao encerrar o processo principal {process_id}: {error}")


def remove_target_files(app_dir: Path, log_path: Path):
    for item_name in ("main.exe", "_internal", "update_helper.exe"):
        target = app_dir / item_name
        if not target.exists():
            continue

        try:
            if target.is_dir():
                shutil.rmtree(target, ignore_errors=False)
            else:
                target.unlink()
            write_log(log_path, f"Item antigo removido: {target}")
        except Exception as error:
            write_log(log_path, f"Falha ao remover {target}: {error}")
            raise


def copy_payload(app_dir: Path, payload_dir: Path, log_path: Path):
    remove_target_files(app_dir, log_path)

    for item in payload_dir.iterdir():
        if item.name in PROTECTED_FILES:
            continue
        if item.is_dir() and item.name in PROTECTED_DIRS:
            continue

        destination = app_dir / item.name
        try:
            if item.is_dir():
                shutil.copytree(item, destination, dirs_exist_ok=True)
            else:
                shutil.copy2(item, destination)
            write_log(log_path, f"Item copiado: {item.name}")
        except Exception as error:
            write_log(log_path, f"Falha ao copiar {item.name}: {error}")
            raise

    if not (app_dir / "main.exe").exists():
        raise FileNotFoundError("main.exe não foi encontrado após a cópia do payload.")

    if not (app_dir / "_internal").exists():
        raise FileNotFoundError("A pasta _internal não foi encontrada após a cópia do payload.")


def restore_backup(app_dir: Path, backup_dir: Path, log_path: Path):
    if not backup_dir or not backup_dir.exists():
        write_log(log_path, "Rollback indisponível: backup não encontrado.")
        return False

    write_log(log_path, f"Iniciando rollback a partir de {backup_dir}")
    try:
        remove_target_files(app_dir, log_path)

        for item_name in ("main.exe", "_internal", "update_helper.exe"):
            source = backup_dir / item_name
            if not source.exists():
                continue

            destination = app_dir / item_name
            if source.is_dir():
                shutil.copytree(source, destination, dirs_exist_ok=True)
            else:
                shutil.copy2(source, destination)

        write_log(log_path, "Rollback concluído com sucesso.")
        return True
    except Exception as error:
        write_log(log_path, f"Falha no rollback: {error}")
        return False


def launch_application(app_dir: Path, log_path: Path):
    executable = app_dir / "main.exe"
    if not executable.exists():
        raise FileNotFoundError(f"Aplicativo não encontrado em {executable}")

    subprocess.Popen(
        [str(executable)],
        cwd=str(app_dir),
        creationflags=getattr(subprocess, "DETACHED_PROCESS", 0)
        | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
        | getattr(subprocess, "CREATE_NO_WINDOW", 0),
        close_fds=True,
    )
    write_log(log_path, "Aplicativo reiniciado com sucesso.")


def parse_args():
    parser = argparse.ArgumentParser(description="Helper de atualização do Project Parallel")
    parser.add_argument("--app-dir", required=True)
    parser.add_argument("--payload-dir", required=True)
    parser.add_argument("--staging-dir", required=True)
    parser.add_argument("--backup-dir", required=True)
    parser.add_argument("--wait-pid", type=int, required=True)
    parser.add_argument("--target-version", required=True)
    parser.add_argument("--state-path", required=True)
    parser.add_argument("--log-path", required=True)
    return parser.parse_args()


def main():
    args = parse_args()

    app_dir = Path(args.app_dir)
    payload_dir = Path(args.payload_dir)
    staging_dir = Path(args.staging_dir)
    backup_dir = Path(args.backup_dir)
    state_path = Path(args.state_path)
    log_path = Path(args.log_path)

    write_log(log_path, f"Helper iniciado para aplicar a versão {args.target_version}.")
    update_state(
        state_path,
        status="applying",
        target_version=args.target_version,
        backup_dir=str(backup_dir),
        helper_started_at=_timestamp(),
    )

    try:
        wait_for_process(args.wait_pid, timeout_seconds=20, log_path=log_path)
        copy_payload(app_dir, payload_dir, log_path)
        update_state(
            state_path,
            status="applied",
            target_version=args.target_version,
            applied_at=_timestamp(),
        )
        launch_application(app_dir, log_path)
    except Exception as error:
        write_log(log_path, f"Erro durante a aplicação da atualização: {error}")
        rollback_ok = restore_backup(app_dir, backup_dir, log_path)
        update_state(
            state_path,
            status="failed",
            target_version=args.target_version,
            failed_at=_timestamp(),
            rollback_applied=rollback_ok,
            last_error=str(error),
        )

        if rollback_ok:
            try:
                launch_application(app_dir, log_path)
            except Exception as restart_error:
                write_log(log_path, f"Falha ao reabrir o aplicativo após rollback: {restart_error}")
        return 1
    finally:
        try:
            if staging_dir.exists():
                shutil.rmtree(staging_dir, ignore_errors=True)
                write_log(log_path, "Pasta de staging removida.")
        except Exception as cleanup_error:
            write_log(log_path, f"Falha ao limpar staging: {cleanup_error}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
