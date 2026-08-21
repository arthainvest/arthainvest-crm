@echo off
REM ============================================================================
REM   ArthaInvest CRM - Uninstaller
REM   Removes ArthaInvest CRM from this computer
REM ============================================================================

color 0C

echo.
echo ============================================================================
echo     ARTHAINVEST CRM - UNINSTALL WIZARD
echo ============================================================================
echo.

set "INSTALL_PATH=%USERPROFILE%\ArthaInvestCRM"

echo Are you sure you want to uninstall ArthaInvest CRM?
echo.
echo Location: %INSTALL_PATH%
echo.
echo NOTE: Your data will NOT be deleted (database will remain)
echo.
set /p CONFIRM="Continue with uninstall? (Y/N): "

if /i not "%CONFIRM%"=="Y" (
    echo Uninstall cancelled.
    pause
    exit /b 0
)

echo.
echo Removing application files...

if exist "%INSTALL_PATH%" (
    rmdir /s /q "%INSTALL_PATH%" 2>nul
    echo [OK] Removed: %INSTALL_PATH%
) else (
    echo [INFO] Installation directory not found
)

echo.
echo Removing Desktop shortcut...
if exist "%USERPROFILE%\Desktop\ArthaInvest CRM.bat" (
    del /q "%USERPROFILE%\Desktop\ArthaInvest CRM.bat"
    echo [OK] Removed Desktop shortcut
)

echo.
echo Removing Start Menu shortcut...
set "START_MENU=%APPDATA%\Microsoft\Windows\Start Menu\Programs\ArthaInvest"
if exist "%START_MENU%" (
    rmdir /s /q "%START_MENU%"
    echo [OK] Removed Start Menu shortcuts
)

echo.
echo ============================================================================
echo     UNINSTALLATION COMPLETE
echo ============================================================================
echo.
echo ArthaInvest CRM has been removed from your computer.
echo.
echo To reinstall, run: INSTALLER.bat
echo.
echo.
pause
