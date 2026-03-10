@echo off
echo =======================================
echo Subiendo cambios a GitHub automaticamente
echo =======================================

:: Obtener la fecha y hora actual para el mensaje del commit del sistema local
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set datetime=%%I
set fecha=%datetime:~0,4%-%datetime:~4,2%-%datetime:~6,2%
set hora=%datetime:~8,2%:%datetime:~10,2%

:: Comandos de Git
git add .
git commit -m "Actualizacion Automatica: %fecha% %hora%"
git push origin main

echo =======================================
echo           Cambios Subidos!
echo =======================================
pause
