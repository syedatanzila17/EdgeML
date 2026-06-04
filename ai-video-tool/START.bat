@echo off
title AI Video Creator
color 0A

echo.
echo  ================================================
echo   AI VIDEO CREATOR  (100% FREE - OpenRouter AI)
echo  ================================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    color 0C
    echo  [ERROR] Python not found.
    echo  Install from: https://python.org
    echo  Check "Add Python to PATH" during install!
    pause
    exit /b
)
echo  [OK] Python found.

cd /d "%~dp0backend"

echo  [..] Checking dependencies (first time: 2-3 mins)...
pip install -r requirements.txt -q
echo  [OK] Dependencies ready.

:: Load saved key
if exist ".env" (
    for /f "tokens=2 delims==" %%a in ('findstr "OPENROUTER_API_KEY" .env') do set OPENROUTER_API_KEY=%%a
)

if "%OPENROUTER_API_KEY%"=="" (
    echo.
    echo  ================================================
    echo   FREE API KEY SETUP - OpenRouter
    echo  ================================================
    echo.
    echo  STEP 1: Open this in your browser:
    echo          https://openrouter.ai
    echo.
    echo  STEP 2: Click "Sign Up" - use Google or Email
    echo          (No credit card needed!)
    echo.
    echo  STEP 3: Go to: https://openrouter.ai/keys
    echo          Click "Create Key" - Copy it
    echo.
    echo  STEP 4: Paste it below and press Enter
    echo.
    set /p OPENROUTER_API_KEY= Paste your FREE OpenRouter key here:
    echo.
    echo OPENROUTER_API_KEY=%OPENROUTER_API_KEY%> .env
    echo  [OK] Key saved! Won't ask again.
) else (
    echo  [OK] API key loaded.
)

echo.
echo  ================================================
echo   STARTING... Browser opens automatically
echo  ================================================
echo.
echo  Keep this window OPEN while using the app.
echo  Press Ctrl+C to stop.
echo.

start "" cmd /c "timeout /t 5 >nul && start http://localhost:8000"
uvicorn main:app --host 0.0.0.0 --port 8000

pause
