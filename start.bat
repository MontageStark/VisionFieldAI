@echo off
echo ===================================
echo  FieldVision AI - Full Stack
echo ===================================
echo.
echo This will start both backend and frontend.
echo Close this window or press Ctrl+C to stop both.
echo.

cd /d "%~dp0"
set PYTHONPATH=%cd%;%cd%\backend

REM Start backend in background
echo [1/2] Starting backend on http://localhost:8001 ...
start "FieldVision Backend" cmd /c "cd /d %~dp0 && set PYTHONPATH=%cd%;%cd%\backend && python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8001 --reload"

REM Wait for backend to be ready
echo [2/2] Waiting for backend...
timeout /t 3 /nobreak >nul

REM Start frontend
echo [2/2] Starting frontend on http://localhost:5174 ...
cd frontend
if not exist "node_modules" (
    echo [INFO] Installing frontend dependencies...
    call npm install
)
call npm run dev
