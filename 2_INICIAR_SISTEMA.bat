@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Loteria Mazahua - Servidor (no cierres esta ventana)
set SERIAL_ENABLED=false
if not exist ".venv\Scripts\python.exe" (
  echo Primero ejecuta 1_INSTALAR.bat
  pause & exit /b 1
)
echo Compilando el frontend (Astro)...
pushd frontend
if not exist "node_modules" call npm install
call npm run build
if errorlevel 1 ( popd & echo [X] No se pudo compilar el frontend. & pause & exit /b 1 )
popd
echo.
echo ============================================================
echo   Sistema iniciado. Abre en tu navegador:
echo     Inicio ............ http://127.0.0.1:8000
echo     Vocabulario ....... http://127.0.0.1:8000/vocabulario
echo     Simulador ......... http://127.0.0.1:8000/simulador
echo     Videos ............ http://127.0.0.1:8000/videos
echo     Administracion .... http://127.0.0.1:8000/administracion
echo     Editor sencillo ... http://127.0.0.1:8000/editar
echo     Swagger (API) ..... http://127.0.0.1:8000/docs   (inicia sesion antes)
echo   Espera unos segundos: el navegador se abrira solo cuando todo este listo.
echo   Para detener el servidor cierra esta ventana o pulsa Ctrl+C.
echo ============================================================
rem El navegador se abre solo cuando el servidor ya esta listo (sin pantalla de error).
start "" /b ".venv\Scripts\python.exe" abrir_navegador.py http://127.0.0.1:8000
".venv\Scripts\python.exe" -m uvicorn main:app --host 0.0.0.0 --port 8000
echo.
echo El servidor se detuvo. Si aparece un error de MySQL, revisa que XAMPP tenga MySQL encendido.
pause
