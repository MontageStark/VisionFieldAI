@echo off
echo ===================================
echo  FieldVision AI - Frontend Dashboard
echo ===================================
echo.

cd /d "%~dp0frontend"

set PORT=5173

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

:: ── Check node_modules ──────────────────────────────────────
if not exist "node_modules" (
    echo [INFO] Installing frontend dependencies...
    call npm install
)

echo.
echo Starting frontend on http://localhost:%PORT%
echo Press Ctrl+C to stop
echo.

call npm run dev
