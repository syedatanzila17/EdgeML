@echo off
title AI Video Creator - Setup & Run
color 0A

echo.
echo  ================================================
echo   AI VIDEO CREATOR - Auto Setup
echo  ================================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    color 0C
    echo  [ERROR] Python is not installed or not in PATH.
    echo  Please install Python from https://python.org
    echo  Make sure to check "Add Python to PATH" during install.
    pause
    exit /b
)

echo  [OK] Python found.

:: Go to backend folder
cd /d "%~dp0backend"

:: Install dependencies
echo.
echo  Installing dependencies (this may take 2-3 minutes)...
echo  Please wait...
echo.
pip install -r requirements.txt --quiet

if errorlevel 1 (
    color 0C
    echo.
    echo  [ERROR] Failed to install dependencies.
    echo  Try running this file as Administrator.
    pause
    exit /b
)

echo.
echo  [OK] All dependencies installed!

:: Ask for API key
echo.
echo  ================================================
echo   ANTHROPIC API KEY SETUP
echo  ================================================
echo.
echo  You need an API key from: https://console.anthropic.com
echo  It looks like: sk-ant-api03-xxxxx...
echo.

if "%ANTHROPIC_API_KEY%"=="" (
    set /p ANTHROPIC_API_KEY= Paste your API key here and press Enter:
)

if "%ANTHROPIC_API_KEY%"=="" (
    color 0C
    echo.
    echo  [ERROR] No API key entered. Please run again and enter your key.
    pause
    exit /b
)

echo.
echo  [OK] API key set!

:: Open browser after short delay
echo.
echo  ================================================
echo   STARTING SERVER...
echo  ================================================
echo.
echo  The app will open in your browser automatically.
echo  Keep this window open while using the tool.
echo  Press CTRL+C to stop the server.
echo.

:: Open browser after 4 seconds
start "" cmd /c "timeout /t 4 >nul && start http://localhost:8000"

:: Run the server
uvicorn main:app --host 0.0.0.0 --port 8000

pause
