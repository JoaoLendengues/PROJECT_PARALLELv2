@echo off 
echo ======================================== 
echo   Instalando Project Parallel Backend 
echo ======================================== 
echo. 
echo Criando pasta de instalacao... 
mkdir "C:\ProjectParallelBackend" 2>nul 
copy ProjectParallelBackend.exe "C:\ProjectParallelBackend\" 
copy schema.sql "C:\ProjectParallelBackend\" 2>nul 
echo. 
echo Instalacao concluida! 
echo. 
echo Para iniciar o servidor: 
echo   cd C:\ProjectParallelBackend 
echo   ProjectParallelBackend.exe 
echo. 
pause 
