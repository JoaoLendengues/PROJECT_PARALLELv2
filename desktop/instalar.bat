@echo off
title Instalador Project Parallel v1.1.2
color 0A

echo ========================================
echo   Project Parallel v1.1.2
echo   Sistema de Controle de Estoque
echo ========================================
echo.
echo Instalando o sistema...

REM Criar pasta no Desktop
mkdir "%USERPROFILE%\Desktop\ProjectParallel" 2>nul

REM Copiar arquivos
copy ProjectParallel.exe "%USERPROFILE%\Desktop\ProjectParallel\"
copy version.json "%USERPROFILE%\Desktop\ProjectParallel\"
copy version.py "%USERPROFILE%\Desktop\ProjectParallel\"

REM Copiar pasta de estilos
xcopy styles "%USERPROFILE%\Desktop\ProjectParallel\styles\" /E /I /Y

REM Criar arquivo .env padrão
echo API_URL=http://10.1.1.151:8000 > "%USERPROFILE%\Desktop\ProjectParallel\.env"

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
echo   2. Execute configurar.bat
echo.
pause
