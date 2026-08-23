@echo off
REM ArthaInvest CRM - Backend Startup Script
REM Run this to start your FastAPI backend

echo.
echo ========================================
echo   ArthaInvest CRM - FastAPI Backend
echo ========================================
echo.

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Installing dependencies...
pip install -q -r requirements.txt

echo.
echo ✓ Environment ready!
echo.
echo Starting FastAPI server...
echo Access API at: http://localhost:8000
echo Interactive docs at: http://localhost:8000/docs
echo.

REM Start the server
python main.py

pause
