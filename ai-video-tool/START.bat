@echo off
title AI Video Creator
color 0A

echo.
echo  ================================================
echo   AI VIDEO CREATOR  (Powered by FREE Groq AI)
echo  ================================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    color 0C
    echo  [ERROR] Python not found.
    echo  Install from: https://python.org
    echo  Make sure to check "Add Python to PATH"
    pause
    exit /b
)
echo  [OK] Python found.

:: Go to backend folder
cd /d "%~dp0backend"

:: Install dependencies
echo  [..] Checking dependencies (first time takes 2-3 mins)...
pip install -r requirements.txt -q
echo  [OK] Dependencies ready.

:: Load saved API key if exists
if exist ".env" (
    for /f "tokens=2 delims==" %%a in ('findstr "GROQ_API_KEY" .env') do set GROQ_API_KEY=%%a
)

:: Ask for API key only if not saved
if "%GROQ_API_KEY%"=="" (
    echo.
    echo  ================================================
    echo   FREE API KEY SETUP (One time only)
    echo  ================================================
    echo.
    echo  STEP 1: Open this in your browser:
    echo          https://console.groq.com
    echo.
    echo  STEP 2: Sign up FREE (no credit card needed)
    echo.
    echo  STEP 3: Click API Keys - Create API Key - Copy it
    echo.
    echo  STEP 4: Paste it below and press Enter
    echo.
    set /p GROQ_API_KEY= Paste your FREE Groq API key here:
    echo.

    :: Save key permanently
    echo GROQ_API_KEY=%GROQ_API_KEY%> .env
    echo  [OK] API key saved! You won't need to enter it again.
) else (
    echo  [OK] API key loaded.
)

echo.
echo  ================================================
echo   STARTING... Browser will open automatically
echo  ================================================
echo.
echo  Keep this window OPEN while using the app.
echo  Press Ctrl+C to stop.
echo.

start "" cmd /c "timeout /t 5 >nul && start http://localhost:8000"

uvicorn main:app --host 0.0.0.0 --port 8000

pause
