@echo off
REM ArthaInvest Capital CRM - Quick Installation Script
REM Run this script to set up the CRM on your computer

setlocal enabledelayedexpansion

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║                                                            ║
echo ║    🎯 ArthaInvest Capital CRM - Installation Setup       ║
echo ║                                                            ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ❌ Node.js is not installed!
    echo.
    echo Please download and install Node.js from:
    echo 👉 https://nodejs.org/ (v16 or higher)
    echo.
    echo After installation:
    echo 1. Restart your computer
    echo 2. Run this script again
    echo.
    pause
    exit /b 1
)

echo ✅ Node.js detected
node --version
echo.

REM Check if npm is installed
npm --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ❌ npm is not installed!
    echo.
    pause
    exit /b 1
)

echo ✅ npm detected
npm --version
echo.

REM Install dependencies
echo Installing dependencies...
echo This may take a few minutes...
echo.

npm install

if errorlevel 1 (
    echo.
    echo ❌ Installation failed!
    echo.
    echo Please contact technical support.
    echo.
    pause
    exit /b 1
)

echo.
echo ✅ Installation complete!
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║                                                            ║
echo ║          🎉 ArthaInvest Capital CRM Ready to Use!        ║
echo ║                                                            ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

echo Next steps:
echo.
echo 1. Start the CRM:
echo    node arthainvest-10-10-enhanced-server.js
echo.
echo 2. Open your browser:
echo    http://localhost:3001
echo.
echo 3. Login with:
echo    📧 Email: admin@arthainvest.com
echo    🔐 Password: admin123
echo.
echo 4. Change your password on first login!
echo.
echo ============================================================
echo.

pause
