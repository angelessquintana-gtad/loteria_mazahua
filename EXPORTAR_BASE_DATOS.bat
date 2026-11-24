@echo off
chcp 65001 >nul
cd /d "%~dp0"
rem Guarda una copia completa (estructura + registros) de la base loteria_mazahua
rem en sql\respaldo_loteria_mazahua.sql. Usa el usuario root sin contrasena de XAMPP;
rem si tu MySQL tiene contrasena, agrega -p despues de -uroot.
set "DUMP=mysqldump"
where mysqldump >nul 2>nul || set "DUMP=C:\xampp\mysql\bin\mysqldump.exe"
"%DUMP%" -uroot --default-character-set=utf8mb4 --routines --databases loteria_mazahua > "sql\respaldo_loteria_mazahua.sql"
if errorlevel 1 ( echo [X] No se pudo exportar. Revisa que MySQL este encendido. ) else ( echo Listo: sql\respaldo_loteria_mazahua.sql )
pause
