from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import zipfile
from datetime import date
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
DESKTOP_DIR = ROOT_DIR / "desktop"
VERSION_FILE = DESKTOP_DIR / "version.json"
SPEC_FILE = DESKTOP_DIR / "main.spec"
DIST_ROOT = DESKTOP_DIR / "output"
BUILD_DIR = DESKTOP_DIR / "build"
INSTALLER_SCRIPT = ROOT_DIR / "installer_script.iss"
ARTIFACTS_DIR = ROOT_DIR / "installer_output"


def load_version_data():
    with open(VERSION_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def save_version_data(data):
    with open(VERSION_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)
        file.write("\n")


def update_version_file(version=None, release_date=None, changelog=None):
    data = load_version_data()
    changed = False

    if version and data.get("version") != version:
        data["version"] = version
        changed = True

    if changelog is not None and data.get("changelog") != changelog:
        data["changelog"] = changelog
        changed = True

    if release_date is None and changed:
        release_date = date.today().isoformat()

    if release_date and data.get("release_date") != release_date:
        data["release_date"] = release_date
        changed = True

    if changed:
        save_version_data(data)

    return data


def run_command(command, cwd=ROOT_DIR):
    print(f"> {' '.join(str(part) for part in command)}")
    subprocess.run(command, cwd=cwd, check=True)


def build_desktop(dist_root, build_dir):
    dist_dir = dist_root / "main"
    pyinstaller_command = [
        sys.executable,
        "-m",
        "PyInstaller",
        str(SPEC_FILE),
        "--noconfirm",
        "--clean",
        "--distpath",
        str(dist_root),
        "--workpath",
        str(build_dir),
    ]
    run_command(pyinstaller_command, cwd=ROOT_DIR)

    executable_path = dist_dir / "main.exe"
    if not executable_path.exists():
        raise FileNotFoundError(
            f"Build concluido sem encontrar o executavel esperado em {executable_path}"
        )

    return executable_path


def create_portable_zip(version, dist_dir, artifacts_dir):
    if not dist_dir.exists():
        raise FileNotFoundError(
            f"Nao encontrei o build do desktop em {dist_dir}. Rode o script sem --skip-build primeiro."
        )

    artifacts_dir.mkdir(parents=True, exist_ok=True)
    zip_path = artifacts_dir / f"ProjectParallel_Portable_v{version}.zip"

    if zip_path.exists():
        zip_path.unlink()

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in dist_dir.rglob("*"):
            if path.is_file():
                archive.write(path, path.relative_to(dist_dir))

    return zip_path


def find_inno_compiler():
    compiler = shutil.which("ISCC.exe")
    if compiler:
        return Path(compiler)

    for env_key in ("ProgramFiles(x86)", "ProgramFiles"):
        base_dir = os.environ.get(env_key)
        if not base_dir:
            continue

        candidate = Path(base_dir) / "Inno Setup 6" / "ISCC.exe"
        if candidate.exists():
            return candidate

    local_appdata = os.environ.get("LOCALAPPDATA")
    if local_appdata:
        candidate = Path(local_appdata) / "Programs" / "Inno Setup 6" / "ISCC.exe"
        if candidate.exists():
            return candidate

    return None


def build_installer(version, dist_dir, artifacts_dir):
    compiler = find_inno_compiler()
    if not compiler:
        print("! Inno Setup nao encontrado. O ZIP portatil foi gerado, mas o setup foi pulado.")
        return None

    command = [
        str(compiler),
        f"/DMyAppVersion={version}",
        f"/DBuildRoot={dist_dir}",
        str(INSTALLER_SCRIPT),
    ]
    run_command(command, cwd=ROOT_DIR)

    installer_path = artifacts_dir / f"ProjectParallel_Setup_v{version}.exe"
    if installer_path.exists():
        return installer_path

    return None


def parse_args():
    parser = argparse.ArgumentParser(
        description="Gera os artefatos de distribuicao do Project Parallel."
    )
    parser.add_argument("--version", help="Nova versao a gravar no version.json antes do build.")
    parser.add_argument("--release-date", help="Data da release no formato YYYY-MM-DD.")
    parser.add_argument("--changelog", help="Changelog resumido da release.")
    parser.add_argument(
        "--skip-build",
        action="store_true",
        help="Reaproveita o build ja existente em desktop/output/main.",
    )
    parser.add_argument(
        "--skip-installer",
        action="store_true",
        help="Gera apenas o ZIP portatil usado pelo updater.",
    )
    parser.add_argument(
        "--dist-root",
        default=str(DIST_ROOT),
        help="Diretorio base do build do PyInstaller. O executavel sera gerado em <dist-root>/main.",
    )
    parser.add_argument(
        "--artifacts-dir",
        default=str(ARTIFACTS_DIR),
        help="Diretorio onde os artefatos finais da release serao salvos.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    dist_root = Path(args.dist_root).resolve()
    dist_dir = dist_root / "main"
    build_dir = BUILD_DIR.resolve()
    artifacts_dir = Path(args.artifacts_dir).resolve()
    version_data = update_version_file(
        version=args.version,
        release_date=args.release_date,
        changelog=args.changelog,
    )
    version = version_data["version"]

    print("=" * 60)
    print(f"Project Parallel - Release Builder v{version}")
    print("=" * 60)

    if not args.skip_build:
        build_desktop(dist_root, build_dir)
    elif not (dist_dir / "main.exe").exists():
        raise FileNotFoundError(
            f"Voce usou --skip-build, mas nao existe um build valido em {dist_dir}."
        )

    portable_zip = create_portable_zip(version, dist_dir, artifacts_dir)
    installer_path = None if args.skip_installer else build_installer(version, dist_dir, artifacts_dir)

    print()
    print("Artefatos gerados:")
    print(f"- ZIP portatil: {portable_zip}")
    if installer_path:
        print(f"- Setup Windows: {installer_path}")
    elif not args.skip_installer:
        print("- Setup Windows: nao gerado (Inno Setup nao encontrado)")

    print()
    print("Publicacao sugerida no GitHub Release:")
    print(f"1. Criar a tag v{version}")
    print(f"2. Anexar o arquivo {portable_zip.name}")
    if installer_path:
        print(f"3. Anexar tambem o arquivo {installer_path.name}")
    print("4. Publicar o changelog da versao")


if __name__ == "__main__":
    main()
