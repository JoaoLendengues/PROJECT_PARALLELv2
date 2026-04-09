# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('styles/style.qss', 'styles'),
        ('version.json', '.'),
        ('widgets/toast_notification.py', 'widgets'),
        ('widgets/__init__.py', 'widgets'),
        ('widgets/login_widget.py', 'widgets'),
        ('widgets/main_window.py', 'widgets'),
        ('widgets/home_widget.py', 'widgets'),
        ('widgets/materiais_widget.py', 'widgets'),
        ('widgets/maquinas_widget.py', 'widgets'),
        ('widgets/movimentacoes_widget.py', 'widgets'),
        ('widgets/manutencoes_widget.py', 'widgets'),
        ('widgets/pedidos_widget.py', 'widgets'),
        ('widgets/usuarios_widget.py', 'widgets'),
        ('widgets/parametros_widget.py', 'widgets'),
        ('widgets/colaboradores_widget.py', 'widgets'),
        ('widgets/demandas_widget.py', 'widgets'),
        ('widgets/relatorios_widget.py', 'widgets'),
        ('widgets/update_widget.py', 'widgets'),
    ],
    hiddenimports=[
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'openpyxl',
        'reportlab',
        'requests',
        'dotenv',
        'sqlalchemy',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
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
    console=False,  # False = sem terminal (janela GUI), True = com terminal
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico',  # Opcional: adicione um ícone
)
