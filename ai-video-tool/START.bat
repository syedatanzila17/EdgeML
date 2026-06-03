@echo off
title AI Video Creator
color 0A

echo.
echo  ================================================
echo   AI VIDEO CREATOR
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

:: Install dependencies silently
echo  [..] Checking dependencies...
pip install -r requirements.txt -q
echo  [OK] Dependencies ready.

:: Load saved API key if it exists
if exist ".env" (
    for /f "tokens=2 delims==" %%a in ('findstr "ANTHROPIC_API_KEY" .env') do set ANTHROPIC_API_KEY=%%a
)

:: Ask for API key only if not saved yet
if "%ANTHROPIC_API_KEY%"=="" (
    echo.
    echo  ================================================
    echo   FIRST TIME SETUP - Enter your API Key
    echo  ================================================
    echo.
    echo  Get your key from: https://console.anthropic.com
    echo  It starts with: sk-ant-...
    echo.
    set /p ANTHROPIC_API_KEY= Paste your API key and press Enter:
    echo.

    :: Save key to .env file so we never ask again
    echo ANTHROPIC_API_KEY=%ANTHROPIC_API_KEY%> .env
    echo  [OK] API key saved! You won't need to enter it again.
) else (
    echo  [OK] API key loaded from saved file.
)

echo.
echo  ================================================
echo   STARTING SERVER...
echo  ================================================
echo.
echo  App will open in your browser in a few seconds.
echo.
echo  IMPORTANT: Keep this window open while using the app.
echo  To stop: press Ctrl+C
echo.

:: Open browser after 5 seconds
start "" cmd /c "timeout /t 5 >nul && start http://localhost:8000"

:: Run server
uvicorn main:app --host 0.0.0.0 --port 8000

echo.
echo  Server stopped. Close this window or run START.bat again.
pause
