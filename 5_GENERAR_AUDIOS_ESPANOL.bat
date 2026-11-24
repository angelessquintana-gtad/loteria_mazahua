@echo off
chcp 65001 >nul
cd /d "%~dp0"
rem Crea el audio en ESPANOL de las tarjetas que no lo tienen, con la voz de Windows.
rem No reemplaza los audios que ya existen. MySQL debe estar encendido en XAMPP.
if not exist ".venv\Scripts\python.exe" ( echo Primero ejecuta 1_INSTALAR.bat & pause & exit /b 1 )
".venv\Scripts\python.exe" -m pip install -q "pyttsx3>=2.98,<3"
".venv\Scripts\python.exe" generar_audios_espanol.py
pause
