@echo off
title Instalador Project Parallel v1.0.2
color 0A

echo ========================================
echo   Project Parallel v1.0.2
echo   Sistema de Controle de Estoque
echo ========================================
echo.
echo Instalando o sistema...

REM Criar pasta no Desktop
mkdir "%USERPROFILE%\Desktop\ProjectParallel" 2>nul

REM Copiar arquivos
copy ProjectParallel.exe "%USERPROFILE%\Desktop\ProjectParallel\"
copy version.json "%USERPROFILE%\Desktop\ProjectParallel\"

REM Criar atalho
echo [InternetShortcut] > "%USERPROFILE%\Desktop\Project Parallel.url"
echo URL=file:///%USERPROFILE%\Desktop\ProjectParallel\ProjectParallel.exe >> "%USERPROFILE%\Desktop\Project Parallel.url"
echo IconIndex=0 >> "%USERPROFILE%\Desktop\Project Parallel.url"
echo IconFile=%USERPROFILE%\Desktop\ProjectParallel\ProjectParallel.exe >> "%USERPROFILE%\Desktop\Project Parallel.url"

echo.
echo ========================================
echo   Instalação concluída!
echo ========================================
echo.
echo Executável em: %USERPROFILE%\Desktop\ProjectParallel\ProjectParallel.exe
echo.
echo Para configurar o servidor:
echo   1. Abra a pasta ProjectParallel no Desktop
echo   2. Crie um arquivo .env com: API_URL=http://10.1.1.151:8000
echo.
pause
