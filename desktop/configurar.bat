@echo off
title Configurar Project Parallel
color 0A

echo ========================================
echo   Configurar Project Parallel
echo ========================================
echo.
echo Endereço padrão: 10.1.1.151
echo.
set /p servidor="Digite o IP do servidor (ex: 10.1.1.151): "

REM Verificar se o usuário digitou algo
if "%servidor%"=="" set servidor=10.1.1.151

REM Criar arquivo .env
echo API_URL=http://%servidor%:8000 > .env

echo.
echo ========================================
echo   Configuração concluída!
echo ========================================
echo.
echo Servidor configurado: %servidor%
echo Arquivo .env criado com sucesso!
echo.
echo Execute ProjectParallel.exe para iniciar
echo.
pause