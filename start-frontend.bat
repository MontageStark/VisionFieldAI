@echo off
echo ===================================
echo  FieldVision AI - Frontend Dashboard
echo ===================================
echo.

cd /d "%~dp0frontend"

REM Check if node_modules exists
if not exist "node_modules" (
    echo [INFO] Installing frontend dependencies...
    call npm install
)

echo Starting frontend on http://localhost:5174
echo Press Ctrl+C to stop
echo.

call npm run dev
