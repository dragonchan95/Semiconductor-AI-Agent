@echo off
setlocal
cd /d "%~dp0"
set PYTHONUTF8=1
if not exist "..\.venv\Scripts\python.exe" (
  if not exist ".venv\Scripts\python.exe" (
    echo Run start.ps1 in PowerShell to prepare the Python environment.
    pause
    exit /b 1
  )
  set "SEMI_PYTHON=.venv\Scripts\python.exe"
) else (
  set "SEMI_PYTHON=..\.venv\Scripts\python.exe"
)
echo Open http://localhost:8700 in your browser. Keep this window open.
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start_local_qwen.ps1
"%SEMI_PYTHON%" -m uvicorn app.api:app --host 127.0.0.1 --port 8700
pause
