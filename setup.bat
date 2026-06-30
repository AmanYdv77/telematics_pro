@echo off
echo ========================================
echo   TelematicsPro - Python Setup Script
echo   Vehicle Telematics Data Pipeline
echo ========================================
echo.

:: Check if Python is installed
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python is not installed!
    echo Please download and install Python from: https://python.org/
    echo Make sure to check "Add Python to PATH" during installation!
    echo.
    pause
    exit /b 1
)

echo [OK] Python found:
python --version
echo.

:: Create virtual environment
echo [1/3] Creating virtual environment...
python -m venv venv
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to create virtual environment!
    pause
    exit /b 1
)
echo [OK] Virtual environment created!
echo.

:: Activate virtual environment and install dependencies
echo [2/3] Installing dependencies...
echo This may take a few minutes...
call venv\Scripts\activate.bat
pip install --upgrade pip
pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to install dependencies!
    pause
    exit /b 1
)
echo [OK] Dependencies installed successfully!
echo.

:: Run the application
echo [3/3] Starting TelematicsPro...
echo.
echo ========================================
echo   Application is starting...
echo   Open your browser to:
echo   http://localhost:8501
echo ========================================
echo.
echo Press Ctrl+C to stop the server.
echo.
streamlit run app.py
