@echo off
chcp 65001 >nul
cd /d "%~dp0"
rem Carga las palabras de la carpeta catalogo\ en MySQL con UID "DEMO 0001", "DEMO 0002"...
rem Solo agrega las que faltan: NO borra ni cambia las tarjetas que ya tienes.
".venv\Scripts\python.exe" cargar_datos_demo.py
pause
