@echo off
title Project Parallel Backend - HIGH PERFORMANCE
color 0A

echo ============================================================
echo   Project Parallel Backend
echo   MODO ALTA PERFORMANCE (200 usuarios simultaneos)
echo ============================================================
echo.

REM Verificar Python
python --version
echo.

REM Ativar ambiente virtual
call venv\Scripts\activate

REM Instalar dependências se necessário
pip show psutil > nul 2>&1
if %errorlevel% neq 0 (
    echo Instalando dependencias de monitoramento...
    pip install psutil
)

echo.
echo Configuracoes:
echo   Workers: 8
echo   Conexões máximas: 200
echo   Pool de conexões DB: 50
echo   Max overflow DB: 100
echo.

echo Iniciando servidor...
echo.

python run.py

pause
