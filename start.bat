@echo off
title FieldVision AI — Starting...
echo.
echo  ==============================
echo   FieldVision AI — Launch
echo  ==============================
echo.

set BACKEND_PORT=8001
set FRONTEND_PORT=5173

:: ── Check if ports are free ──────────────────────────────────
set CONFLICTS=0

netstat -ano | findstr ":%BACKEND_PORT% " | findstr "LISTENING" >nul 2>&1
if %errorlevel% equ 0 (
    echo  [WARN] Port %BACKEND_PORT% is already in use!
    for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":%BACKEND_PORT% " ^| findstr "LISTENING"') do (
        echo         PID: %%p — ^&tasklist /fi "PID eq %%p" 2^>nul ^| findstr /i "image name"
    )
    set /a CONFLICTS+=1
) else (
    echo  [OK]   Port %BACKEND_PORT% is free.
)

netstat -ano | findstr ":%FRONTEND_PORT% " | findstr "LISTENING" >nul 2>&1
if %errorlevel% equ 0 (
    echo  [WARN] Port %FRONTEND_PORT% is already in use!
    for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":%FRONTEND_PORT% " ^| findstr "LISTENING"') do (
        echo         PID: %%p — ^&tasklist /fi "PID eq %%p" 2^>nul ^| findstr /i "image name"
    )
    set /a CONFLICTS+=1
) else (
    echo  [OK]   Port %FRONTEND_PORT% is free.
)

if %CONFLICTS% gtr 0 (
    echo.
    echo  ABORT: One or more ports are occupied.
    echo  Close the conflicting process or run: netstat -ano ^| findstr ":8001 :5173"
    echo.
    pause
    exit /b 1
)

:: ── Start backend ────────────────────────────────────────────
echo.
echo [1/2] Starting backend (FastAPI on port %BACKEND_PORT%)...
start "FieldVision Backend" cmd /k "cd /d D:\FieldVision AI\backend && set PYTHONPATH=D:\FieldVision AI;D:\FieldVision AI\backend && python -m uvicorn app.main:create_app --factory --host 0.0.0.0 --port %BACKEND_PORT% --reload"

timeout /t 3 /nobreak >nul

:: ── Verify backend started ──────────────────────────────────
netstat -ano | findstr ":%BACKEND_PORT% " | findstr "LISTENING" >nul 2>&1
if %errorlevel% neq 0 (
    echo  [WARN] Backend may not have started on port %BACKEND_PORT%.
    echo         Check the backend window for errors.
) else (
    echo  [OK]   Backend is listening on port %BACKEND_PORT%.
)

:: ── Start frontend ──────────────────────────────────────────
echo.
echo [2/2] Starting frontend (Vite on port %FRONTEND_PORT%)...
start "FieldVision Frontend" cmd /k "cd /d D:\FieldVision AI\frontend && npm run dev"

timeout /t 2 /nobreak >nul

:: ── Verify frontend started ─────────────────────────────────
netstat -ano | findstr ":%FRONTEND_PORT% " | findstr "LISTENING" >nul 2>&1
if %errorlevel% neq 0 (
    echo  [WARN] Frontend may not have started on port %FRONTEND_PORT%.
    echo         Check the frontend window for errors.
) else (
    echo  [OK]   Frontend is listening on port %FRONTEND_PORT%.
)

echo.
echo  ──────────────────────────────────────────
echo   Backend:   http://localhost:%BACKEND_PORT%
echo   Frontend:  http://localhost:%FRONTEND_PORT%
echo   API docs:  http://localhost:%BACKEND_PORT%/docs
echo  ──────────────────────────────────────────
echo.
echo  Close this window anytime — the other two keep running.
echo.
pause
