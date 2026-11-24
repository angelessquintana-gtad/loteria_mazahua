@echo off
chcp 65001 >nul
cd /d "%~dp0frontend"
rem Opcional, para EDITAR el frontend con recarga automatica.
rem 1) Deja corriendo 2_INICIAR_SISTEMA.bat (backend en el puerto 8000).
rem 2) Ejecuta este archivo y abre http://127.0.0.1:4321
echo Frontend en modo desarrollo: http://127.0.0.1:4321  (el backend debe estar en el puerto 8000)
call npm run dev
pause
