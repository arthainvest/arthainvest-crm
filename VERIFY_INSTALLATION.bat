@echo off
REM ============================================================================
REM   ArthaInvest CRM - Installation Verification Script
REM   Verify that the CRM is properly installed and ready to use
REM ============================================================================

color 0B

echo.
echo ============================================================================
echo     ARTHAINVEST CRM - INSTALLATION VERIFICATION
echo ============================================================================
echo.

set "RESULT=0"

REM Check Python installation
echo Checking Python installation...
python --version >nul 2>&1
if %errorlevel% equ 0 (
    echo [PASS] Python is installed
    python --version
) else (
    echo [FAIL] Python is NOT installed
    set "RESULT=1"
)

echo.
echo Checking Python in PATH...
where python >nul 2>&1
if %errorlevel% equ 0 (
    echo [PASS] Python is in PATH
) else (
    echo [FAIL] Python is NOT in PATH
    set "RESULT=1"
)

echo.
echo Checking PyQt5 installation...
python -c "import PyQt5; print('[PASS] PyQt5 is installed')" 2>nul
if %errorlevel% neq 0 (
    echo [FAIL] PyQt5 is NOT installed
    set "RESULT=1"
)

echo.
echo Checking application file...
if exist "arthainvest_crm_app.py" (
    echo [PASS] Application file found
) else (
    echo [FAIL] Application file NOT found
    set "RESULT=1"
)

echo.
echo Checking database connectivity...
python -c "import sqlite3; db=sqlite3.connect(':memory:'); print('[PASS] SQLite3 is working')" 2>nul
if %errorlevel% neq 0 (
    echo [FAIL] SQLite3 is NOT working
    set "RESULT=1"
)

echo.
echo Checking application syntax...
python -m py_compile arthainvest_crm_app.py >nul 2>&1
if %errorlevel% equ 0 (
    echo [PASS] Application syntax is valid
) else (
    echo [FAIL] Application has syntax errors
    set "RESULT=1"
)

echo.
echo Checking application imports...
python -c "import arthainvest_crm_app; print('[PASS] Application imports successfully')" 2>nul
if %errorlevel% neq 0 (
    echo [FAIL] Application import failed
    set "RESULT=1"
)

echo.
echo ============================================================================
if %RESULT% equ 0 (
    echo     VERIFICATION COMPLETE - ALL CHECKS PASSED
    echo ============================================================================
    echo.
    echo Your ArthaInvest CRM installation is complete and ready to use!
    echo.
    echo You can now:
    echo   - Double-click RUN_CRM.bat to start the application
    echo   - Or run: python arthainvest_crm_app.py
    echo.
    echo Default login:
    echo   Username: admin
    echo   Password: 123
    echo.
    echo ============================================================================
) else (
    echo     VERIFICATION FAILED - SOME CHECKS DID NOT PASS
    echo ============================================================================
    echo.
    echo There are issues with your installation. Please:
    echo.
    echo 1. Make sure Python 3.8+ is installed
    echo 2. Make sure Python is in your PATH
    echo 3. Make sure PyQt5 is installed (pip install PyQt5)
    echo 4. Make sure arthainvest_crm_app.py is in this directory
    echo.
    echo For help, read: CRM_SETUP_GUIDE.txt
    echo.
    echo ============================================================================
)

echo.
pause
