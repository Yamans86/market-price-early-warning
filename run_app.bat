@echo off
setlocal

cd /d "%~dp0"

echo.
echo Humanitarian Market Price Early Warning System
echo =================================================
echo.

where python >nul 2>nul
if errorlevel 1 (
    echo Python was not found on PATH.
    echo Install Python 3.10+ or activate your virtual environment, then run this file again.
    pause
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    echo Creating virtual environment in .venv ...
    python -m venv .venv
    if errorlevel 1 (
        echo Failed to create virtual environment.
        pause
        exit /b 1
    )
)

echo Installing or updating dependencies ...
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
    echo Dependency installation failed.
    pause
    exit /b 1
)

echo.
echo Starting Streamlit...
echo The app will open at http://localhost:8501
echo Press Ctrl+C in this window to stop the app.
echo.

".venv\Scripts\python.exe" -m streamlit run app.py

pause
