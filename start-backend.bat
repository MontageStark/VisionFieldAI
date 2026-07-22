@echo off
echo ===================================
echo  FieldVision AI - Backend Server
echo ===================================
echo.

cd /d "%~dp0"

REM Set PYTHONPATH so imports work (both root and backend dir needed)
set PYTHONPATH=%cd%;%cd%\backend

set PORT=8001

:: ── Check if port is free ───────────────────────────────────
netstat -ano | findstr ":%PORT% " | findstr "LISTENING" >nul 2>&1
if %errorlevel% equ 0 (
    echo  [WARN] Port %PORT% is already in use!
    echo.
    for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":%PORT% " ^| findstr "LISTENING"') do (
        echo         PID: %%p
        tasklist /fi "PID eq %%p" 2>nul | findstr /i "image name"
    )
    echo.
    echo  Options:
    echo    1. Kill the process using the port
    echo    2. Change the PORT variable in this script
    echo.
    set /p CHOICE="Kill process? (y/n): "
    if /i "%CHOICE%"=="y" (
        for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":%PORT% " ^| findstr "LISTENING"') do (
            echo  Killing PID %%p...
            taskkill /PID %%p /F >nul 2>&1
        )
        echo  [OK] Port %PORT% freed.
    ) else (
        echo  ABORT: Port %PORT% is occupied.
        pause
        exit /b 1
    )
) else (
    echo  [OK] Port %PORT% is free.
)

:: ── Check uvicorn ───────────────────────────────────────────
python -c "import uvicorn" 2>nul
if errorlevel 1 (
    echo [ERROR] uvicorn not found. Installing dependencies...
    pip install -r backend/requirements.txt
)

echo.
echo Starting backend on http://0.0.0.0:%PORT%
echo Press Ctrl+C to stop
echo.

python -m uvicorn app.main:create_app --factory --host 0.0.0.0 --port %PORT% --reload
