@echo off
REM ArthaInvest CRM - Backend Startup (SQLite Version for Testing)
REM Run this to test your FastAPI backend without PostgreSQL

echo.
echo ========================================
echo   ArthaInvest CRM - FastAPI Backend
echo   SQLite Version (for Testing)
echo ========================================
echo.

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Installing dependencies...
pip install -q -r requirements-sqlite.txt

echo.
echo ✓ Environment ready!
echo.
echo Starting FastAPI server (SQLite)...
echo.
echo Access API at: http://localhost:8000
echo Interactive docs at: http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop the server
echo.

REM Start the server with SQLite version
python main_sqlite.py

pause
