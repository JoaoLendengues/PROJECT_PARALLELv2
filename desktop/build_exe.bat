@echo off
title Building Project Parallel Executable
color 0A

echo ========================================
echo   Project Parallel - Build Executable
echo   Versao 1.1.0
echo ========================================
echo.

echo 📦 Limpando builds anteriores...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist *.spec del *.spec

echo.
echo 📋 Instalando dependencias...
pip install pyinstaller openpyxl reportlab requests python-dotenv psutil PySide6 apscheduler

echo.
echo 🔧 Criando executavel...
pip install pyinstaller ProjectParallel.spec --clean --noconfirm

echo.
echo ========================================
echo   ✅ Build concluido!
echo   📁 Executavel em: dist\ProjectParallel.exe
echo ========================================
echo.
pause
