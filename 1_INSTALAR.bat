@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Loteria Mazahua - Instalacion
echo ============================================================
echo   LOTERIA MAZAHUA - INSTALACION (se hace UNA sola vez)
echo ============================================================
echo.

rem ---- 1. Python (backend) ----
set "PY="
where py >nul 2>nul && set "PY=py -3"
if not defined PY ( where python >nul 2>nul && set "PY=python" )
if not defined PY (
  echo [X] No se encontro Python. Instala Python 3.10 o superior desde https://www.python.org
  echo     y marca la casilla "Add python.exe to PATH". Despues vuelve a abrir este archivo.
  pause & exit /b 1
)
echo [1/5] Python encontrado:
%PY% --version

rem ---- 2. Node.js (frontend) ----
where npm >nul 2>nul
if errorlevel 1 (
  echo [X] No se encontro Node.js. Instala la version LTS desde https://nodejs.org y vuelve a abrir este archivo.
  pause & exit /b 1
)
echo [2/5] Node.js encontrado:
node --version

rem ---- 3. Archivo .env (conexion a MySQL) ----
if not exist ".env" (
  copy ".env.example" ".env" >nul
  echo [3/5] Se creo el archivo .env. Revisa usuario y contrasena de MySQL si no usas XAMPP.
) else (
  echo [3/5] El archivo .env ya existe; se conserva tal cual.
)

rem ---- 4. Backend: entorno virtual y dependencias ----
echo [4/5] Instalando dependencias del BACKEND (FastAPI)...
if not exist ".venv\Scripts\python.exe" %PY% -m venv .venv
".venv\Scripts\python.exe" -m pip install --upgrade pip >nul
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 ( echo [X] Fallo la instalacion del backend. Revisa tu conexion a internet. & pause & exit /b 1 )

rem ---- 5. Frontend: dependencias y compilacion ----
echo [5/5] Instalando y compilando el FRONTEND (Astro)...
pushd frontend
call npm install
if errorlevel 1 ( popd & echo [X] Fallo npm install. & pause & exit /b 1 )
call npm run build
if errorlevel 1 ( popd & echo [X] Fallo la compilacion de Astro. & pause & exit /b 1 )
popd

echo.
echo ============================================================
echo   Instalacion terminada.
echo   Siguiente paso: enciende MySQL (XAMPP) y abre 2_INICIAR_SISTEMA.bat
echo   Para crear los audios en espanol que faltan: 5_GENERAR_AUDIOS_ESPANOL.bat
echo ============================================================
pause
