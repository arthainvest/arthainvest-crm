@echo off
REM ArthaInvest CRM - Quick Start Script for Windows

title ArthaInvest CRM - Setup & Run
color 0B

echo.
echo ========================================
echo   ArthaInvest CRM Pro - Setup Script
echo ========================================
echo.

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js is not installed!
    echo.
    echo Please install Node.js from: https://nodejs.org/
    echo Then restart this script.
    echo.
    pause
    exit /b
)

echo [OK] Node.js is installed
node --version

REM Check if dependencies are installed
if not exist "node_modules\" (
    echo.
    echo [INFO] Installing dependencies...
    echo This may take a few minutes...
    call npm install
    if errorlevel 1 (
        echo [ERROR] npm install failed!
        pause
        exit /b
    )
    echo [OK] Dependencies installed
)

REM Menu
:menu
cls
echo.
echo ========================================
echo   ArthaInvest CRM - Options
echo ========================================
echo.
echo 1. Run Development Server
echo 2. Build Windows Installer (.exe)
echo 3. Build Portable Version
echo 4. Build All Platforms
echo 5. Install Dependencies (Fresh Install)
echo 6. Open Folder in Explorer
echo 7. Exit
echo.

set /p choice="Select option (1-7): "

if "%choice%"=="1" goto run_dev
if "%choice%"=="2" goto build_win
if "%choice%"=="3" goto build_portable
if "%choice%"=="4" goto build_all
if "%choice%"=="5" goto fresh_install
if "%choice%"=="6" goto open_folder
if "%choice%"=="7" goto exit_script
goto menu

:run_dev
cls
echo.
echo [INFO] Starting development server...
echo Opening app at http://localhost:3000
echo Press Ctrl+C in this window to stop
echo.
timeout /t 2
call npm start
goto menu

:build_win
cls
echo.
echo [INFO] Building Windows installer...
echo This will create dist/ArthaInvest-CRM-Setup-1.0.0.exe
echo Please wait...
echo.
call npm run build:win
if errorlevel 1 (
    echo [ERROR] Build failed!
) else (
    echo [OK] Build completed! Check the dist folder.
)
pause
goto menu

:build_portable
cls
echo.
echo [INFO] Building portable version...
echo This will create a standalone .exe (no installation needed)
echo Please wait...
echo.
call npm run build:win
if errorlevel 1 (
    echo [ERROR] Build failed!
) else (
    echo [OK] Build completed! Check the dist folder.
)
pause
goto menu

:build_all
cls
echo.
echo [INFO] Building for all platforms...
echo This will create Windows, Mac, and Linux versions
echo Please wait (this takes longer)...
echo.
call npm run build:all
if errorlevel 1 (
    echo [ERROR] Build failed!
) else (
    echo [OK] Build completed! Check the dist folder.
)
pause
goto menu

:fresh_install
cls
echo.
echo [WARNING] This will delete node_modules and reinstall
echo.
set /p confirm="Are you sure? (y/n): "
if /i not "%confirm%"=="y" goto menu

echo.
echo Deleting old files...
rmdir /s /q node_modules
del package-lock.json

echo Installing fresh dependencies...
call npm install
if errorlevel 1 (
    echo [ERROR] Installation failed!
) else (
    echo [OK] Installation complete!
)
pause
goto menu

:open_folder
explorer .
goto menu

:exit_script
cls
echo.
echo Thank you for using ArthaInvest CRM!
echo.
pause
exit /b 0
