@echo off
REM Start AudioToText with its own virtual environment.
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo Creating virtual environment...
    py -m venv .venv || python -m venv .venv
)
".venv\Scripts\python.exe" -c "import faster_whisper, flask" 2>nul || (
    echo Installing requirements...
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt
)
start "" http://127.0.0.1:5000
".venv\Scripts\python.exe" app.py
pause
