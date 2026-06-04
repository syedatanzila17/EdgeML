@echo off
title AI Video Creator
color 0A

echo.
echo  ================================================
echo   AI VIDEO CREATOR  - 100%% FREE, No API Key!
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

echo  [..] Installing dependencies (first time: 2-3 mins)...
pip install -r requirements.txt -q
echo  [OK] Ready to go!

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
