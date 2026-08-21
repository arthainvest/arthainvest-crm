@echo off
REM ArthaInvest CRM Desktop Application Launcher
REM This script sets up and runs the CRM application

echo.
echo ========================================
echo   ArthaInvest CRM - Desktop Application
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo.
    echo Please install Python 3.8+ from https://www.python.org/
    echo Make sure to check "Add Python to PATH" during installation
    echo.
    pause
    exit /b 1
)

echo Checking Python version...
python --version

REM Install required packages if not already installed
echo.
echo Installing required packages...
pip install -q -r requirements.txt

if %errorlevel% neq 0 (
    echo ERROR: Failed to install packages
    pause
    exit /b 1
)

echo.
echo ✓ All dependencies installed successfully
echo.

REM Run the CRM application
echo Starting ArthaInvest CRM...
echo.

python arthainvest_crm_app.py

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Application failed to start
    echo.
    pause
    exit /b 1
)

pause
