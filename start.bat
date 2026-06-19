@echo off
setlocal

echo ==========================================
echo Starting Indian Market Backtester
echo ==========================================

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not added to your PATH.
    echo Please install Python 3.10+ and try again.
    pause
    exit /b 1
)

:: Check if venv directory exists
if not exist "venv" (
    echo [INFO] Creating virtual environment...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
)

:: Activate the virtual environment
echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat

:: Install/Upgrade dependencies
echo [INFO] Checking dependencies...
python -m pip install --upgrade pip >nul 2>&1
pip install -r requirements.txt

:: Run the Streamlit application
echo [INFO] Launching Streamlit dashboard...
streamlit run ui/app.py

:: Keep window open if streamlit crashes/stops
pause
