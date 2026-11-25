@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" -B crear_asesor.py
) else (
  python -B crear_asesor.py
)
if errorlevel 1 pause
