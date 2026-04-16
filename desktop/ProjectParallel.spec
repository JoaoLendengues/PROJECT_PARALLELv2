# -*- mode: python ; coding: utf-8 -*-

import sys
import os

# Adicionar caminho para icons se existir
icon_path = 'icon.ico'
if not os.path.exists(icon_path):
    icon_path = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
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
        'requests',
        'dotenv',
        'psutil',
        'jose',
        'passlib',
        'apscheduler',
        'sqlalchemy',
        'psycopg2',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

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
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_path,
)
