@echo off
REM ============================================================================
REM   ArthaInvest CRM - Team Installation Script
REM   Professional Installer for Windows
REM   Version: 1.0 | Date: August 20, 2026
REM ============================================================================

setlocal enabledelayedexpansion

REM Set colors for console output
color 0A

echo.
echo ============================================================================
echo     ARTHAINVEST CRM - TEAM INSTALLATION WIZARD
echo ============================================================================
echo.
echo     Professional CRM System with Role-Based Access Control
echo     Ready for immediate team deployment
echo.
echo ============================================================================
echo.

REM Check if running as administrator
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo WARNING: This installer works better with Administrator privileges
    echo Attempting to continue anyway...
    echo.
)

REM Get current user's AppData path
set "INSTALL_PATH=%USERPROFILE%\ArthaInvestCRM"

echo Step 1: Checking system requirements...
echo.

REM Check Python installation
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed!
    echo.
    echo ACTION REQUIRED:
    echo 1. Visit: https://www.python.org/downloads/
    echo 2. Download Python 3.8 or higher
    echo 3. Run the installer
    echo 4. IMPORTANT: Check "Add Python to PATH"
    echo 5. Run this installer again
    echo.
    pause
    exit /b 1
)

echo [OK] Python found
python --version

echo.
echo Step 2: Creating installation directory...
if not exist "%INSTALL_PATH%" (
    mkdir "%INSTALL_PATH%"
    echo [OK] Created: %INSTALL_PATH%
) else (
    echo [OK] Directory exists: %INSTALL_PATH%
)

echo.
echo Step 3: Copying application files...
REM Copy main application file
if exist "arthainvest_crm_app.py" (
    copy /Y "arthainvest_crm_app.py" "%INSTALL_PATH%\" >nul
    echo [OK] Copied: arthainvest_crm_app.py
) else (
    echo ERROR: arthainvest_crm_app.py not found!
    pause
    exit /b 1
)

REM Copy supporting files
if exist "requirements.txt" (
    copy /Y "requirements.txt" "%INSTALL_PATH%\" >nul
    echo [OK] Copied: requirements.txt
)

if exist "QUICKSTART.txt" (
    copy /Y "QUICKSTART.txt" "%INSTALL_PATH%\" >nul
    echo [OK] Copied: QUICKSTART.txt
)

if exist "CRM_SETUP_GUIDE.txt" (
    copy /Y "CRM_SETUP_GUIDE.txt" "%INSTALL_PATH%\" >nul
    echo [OK] Copied: CRM_SETUP_GUIDE.txt
)

echo.
echo Step 4: Installing Python dependencies...
echo This may take 1-2 minutes on first install...
echo.

pip install -q PyQt5 2>nul
if %errorlevel% neq 0 (
    echo WARNING: PyQt5 installation had issues, retrying...
    pip install PyQt5
)

echo [OK] Dependencies installed

echo.
echo Step 5: Creating launch shortcuts...

REM Create Run script in install directory
(
    echo @echo off
    echo cd /d "%INSTALL_PATH%"
    echo python arthainvest_crm_app.py
    echo if errorlevel 1 pause
) > "%INSTALL_PATH%\RUN_CRM.bat"
echo [OK] Created: RUN_CRM.bat

REM Create Desktop shortcut batch file
(
    echo @echo off
    echo cd /d "%INSTALL_PATH%"
    echo python arthainvest_crm_app.py
    echo if errorlevel 1 pause
) > "%USERPROFILE%\Desktop\ArthaInvest CRM.bat"
echo [OK] Created Desktop shortcut

echo.
echo Step 6: Creating start menu shortcut...
set "START_MENU=%APPDATA%\Microsoft\Windows\Start Menu\Programs"
if not exist "%START_MENU%\ArthaInvest" mkdir "%START_MENU%\ArthaInvest"

(
    echo @echo off
    echo cd /d "%INSTALL_PATH%"
    echo python arthainvest_crm_app.py
    echo if errorlevel 1 pause
) > "%START_MENU%\ArthaInvest\ArthaInvest CRM.bat"
echo [OK] Created Start Menu shortcut

echo.
echo Step 7: Verification...
echo.

if exist "%INSTALL_PATH%\arthainvest_crm_app.py" (
    echo [OK] Application file: Present
) else (
    echo [ERROR] Application file: Missing
)

if exist "%INSTALL_PATH%\requirements.txt" (
    echo [OK] Requirements file: Present
) else (
    echo [WARNING] Requirements file: Missing
)

python -c "import PyQt5" >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] PyQt5 library: Installed
) else (
    echo [ERROR] PyQt5 library: Failed to install
)

echo.
echo ============================================================================
echo     INSTALLATION COMPLETE!
echo ============================================================================
echo.
echo Installation Directory: %INSTALL_PATH%
echo.
echo HOW TO RUN:
echo   Option 1: Double-click "ArthaInvest CRM.bat" on your Desktop
echo   Option 2: Search for "ArthaInvest" in Start Menu
echo   Option 3: Run from: %INSTALL_PATH%\RUN_CRM.bat
echo.
echo DEFAULT LOGIN:
echo   Username: admin
echo   Password: 123
echo.
echo TEAM ACCOUNTS:
echo   Username: teamlead / Password: 123
echo   Username: employee1 / Password: 123
echo.
echo DOCUMENTATION:
echo   - QUICKSTART.txt: 60-second quick start guide
echo   - CRM_SETUP_GUIDE.txt: Complete documentation
echo.
echo ============================================================================
echo.

pause

REM Try to launch the application
echo Launching ArthaInvest CRM...
cd /d "%INSTALL_PATH%"
python arthainvest_crm_app.py

exit /b 0
