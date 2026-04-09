@echo off
title Project Parallel Backend - PRODUCAO
color 0A

echo ========================================
echo   Project Parallel Backend
echo   MODO PRODUCAO
echo ========================================
echo.
echo Iniciando servidor com 4 workers...
echo.

REM Ativar ambiente virtual
call venv\Scripts\activate

REM Verificar se as dependências estão instaladas
pip show waitress > nul 2>&1
if %errorlevel% neq 0 (
    echo Instalando dependencias de producao...
    pip install waitress
)

REM Iniciar servidor
python run_production.py

pause
