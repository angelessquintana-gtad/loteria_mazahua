@echo off
chcp 65001 >nul
cd /d "%~dp0"
rem Respaldo: crear una cuenta docente o ponerle una contrasena nueva desde esta computadora.
rem (Normalmente se hace en la pagina /acceso.) MySQL debe estar encendido.
".venv\Scripts\python.exe" configurar_admin.py
pause
