@echo off
REM ============================================================
REM  ArthaInvest - rebuild the prospecting engine and dashboard
REM
REM  Runs the SAFE rebuild:
REM    - refuses to start if a source workbook is missing
REM    - snapshots every output first
REM    - restores the snapshot if any step or the verification fails
REM
REM  Takes about 2.5 minutes. Excel runs hidden in the background.
REM  The same script runs automatically each morning at 09:15.
REM ============================================================
setlocal
set "ROOT=%~dp0"

powershell -NoProfile -ExecutionPolicy Bypass -File "%ROOT%build\Rebuild-Safe.ps1"
set RC=%ERRORLEVEL%

echo.
if "%RC%"=="0" (
  echo  Rebuild succeeded. Opening the dashboard...
  start "" "%ROOT%09_Dashboard.html"
  exit /b 0
)
if "%RC%"=="2" (
  echo  *** REFUSED TO START - a source workbook is missing.        ***
  echo  *** Nothing was changed. See the list above.                ***
) else (
  echo  *** BUILD FAILED - everything was rolled back.              ***
  echo  *** Your previous dashboard and spreadsheets are intact.    ***
)
echo.
echo  Full log: %ROOT%build\_staging\rebuild.log
echo.
pause
exit /b %RC%
