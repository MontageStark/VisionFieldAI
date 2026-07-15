@echo off
echo ===================================
echo  FieldVision AI - Backend Server
echo ===================================
echo.

cd /d "%~dp0"

REM Set PYTHONPATH so imports work
set PYTHONPATH=%cd%

REM Check if uvicorn is installed
python -c "import uvicorn" 2>nul
if errorlevel 1 (
    echo [ERROR] uvicorn not found. Installing dependencies...
    pip install -r backend/requirements.txt
)

set PORT=8001
echo Starting backend on http://0.0.0.0:%PORT%
echo Press Ctrl+C to stop
echo.

python -m uvicorn backend.app.main:app --host 0.0.0.0 --port %PORT% --reload
