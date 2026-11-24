@echo off
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" serial_bridge.py
) else (
  python serial_bridge.py
)
pause
