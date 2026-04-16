@echo off
echo ========================================
echo   Configurar Project Parallel
echo ========================================
echo.
set /p servidor="Digite o IP do servidor (ex: 10.1.1.151): "
echo API_URL=http://%servidor%:8000 > .env
echo.
echo Configurado para servidor: %servidor%
echo.
echo Execute ProjectParallel.exe para iniciar
pause
