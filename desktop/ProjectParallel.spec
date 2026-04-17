# -*- mode: python ; coding: utf-8 -*-

import sys
import os

# Adicionar o caminho do python.dll se necessário
python_dll_path = os.path.join(sys.base_prefix, 'python312.dll')
if not os.path.exists(python_dll_path):
    python_dll_path = os.path.join(sys.base_prefix, 'python3.dll')

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[
        (python_dll_path, '.') if os.path.exists(python_dll_path) else None,
    ],
    datas=[
        ('styles/style.qss', 'styles'),
        ('version.json', '.'),
        ('version.py', '.'),
    ],
    hiddenimports=[
        'pyexpat',
        'xml.etree.ElementTree',
        'xml.parsers.expat',
        'openpyxl',
        'reportlab',
        'PIL',
        'PIL._imaging',
        'PIL._imagingft',
        'PIL._imagingtk',
        'PIL._webp',
        'PIL.Image',
        'PIL.ImageFile',
        'PIL.ImagePalette',
        'PIL.ImageDraw',
        'PIL.ImageFont',
        'PIL.ImageOps',
        'PIL.ImageChops',
        'PIL.ImageColor',
        'PIL.ImageFilter',
        'PIL.ImageMath',
        'PIL.ImageMode',
        'PIL.ImageShow',
        'PIL.ImageWin',
        'PIL.ImageQt',
        'PIL.ImageSequence',
        'PIL.ImageCms',
        'requests',
        'dotenv',
        'psutil',
        'jose',
        'passlib',
        'apscheduler',
        'sqlalchemy',
        'psycopg2',
        'datetime',
        'json',
        'typing',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

# Remover entradas None da lista de binaries
a.binaries = [b for b in a.binaries if b is not None]

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='ProjectParallel',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Colocar True para ver erros (depois muda para False)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
