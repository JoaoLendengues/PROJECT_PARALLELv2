@echo off
echo ========================================
echo   Project Parallel - Build Executavel
echo ========================================
echo.

echo Ativando ambiente virtual...
call ..\venv\Scripts\activate

echo Instalando dependencias...
pip install pyinstaller openpyxl reportlab requests python-dotenv

echo Limpando builds anteriores...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo Criando executavel...
pyinstaller --onefile --windowed --name="ProjectParallel" --icon=icon.ico ^
    --add-data="styles/style.qss;styles" ^
    --add-data="version.json;." ^
    --hidden-import=openpyxl ^
    --hidden-import=reportlab ^
    --hidden-import=requests ^
    --hidden-import=dotenv ^
    main.py

echo.
echo ========================================
echo   Build concluido!
echo   Executavel em: dist\ProjectParallel.exe
echo ========================================
pause
