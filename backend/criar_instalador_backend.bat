@echo off
echo ========================================
echo   Criando Instalador do Backend
echo ========================================
echo.

REM Criar executável
echo Gerando executavel...
pyinstaller --onefile --name="ProjectParallelBackend" --add-data="app;app" --add-data=".env;." run.py

REM Criar pasta do instalador
mkdir installer_backend 2>nul

REM Copiar arquivos
copy dist\ProjectParallelBackend.exe installer_backend\
copy ..\database\schema.sql installer_backend\ 2>nul
copy ..\README.md installer_backend\ 2>nul

REM Criar script de instalação
echo @echo off > installer_backend\instalar_backend.bat
echo echo ======================================== >> installer_backend\instalar_backend.bat
echo echo   Instalando Project Parallel Backend >> installer_backend\instalar_backend.bat
echo echo ======================================== >> installer_backend\instalar_backend.bat
echo echo. >> installer_backend\instalar_backend.bat
echo echo Criando pasta de instalacao... >> installer_backend\instalar_backend.bat
echo mkdir "C:\ProjectParallelBackend" 2^>nul >> installer_backend\instalar_backend.bat
echo copy ProjectParallelBackend.exe "C:\ProjectParallelBackend\" >> installer_backend\instalar_backend.bat
echo copy schema.sql "C:\ProjectParallelBackend\" 2^>nul >> installer_backend\instalar_backend.bat
echo echo. >> installer_backend\instalar_backend.bat
echo echo Instalacao concluida! >> installer_backend\instalar_backend.bat
echo echo. >> installer_backend\instalar_backend.bat
echo echo Para iniciar o servidor: >> installer_backend\instalar_backend.bat
echo echo   cd C:\ProjectParallelBackend >> installer_backend\instalar_backend.bat
echo echo   ProjectParallelBackend.exe >> installer_backend\instalar_backend.bat
echo echo. >> installer_backend\instalar_backend.bat
echo pause >> installer_backend\instalar_backend.bat

REM Compactar
powershell Compress-Archive -Path installer_backend\* -DestinationPath ProjectParallelBackend_Installer.zip -Force

echo.
echo ========================================
echo   Instalador do Backend criado!
echo   Arquivo: ProjectParallelBackend_Installer.zip
echo ========================================
pause
