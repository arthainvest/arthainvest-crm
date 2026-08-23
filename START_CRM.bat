@echo off
cd /d "%~dp0"
echo Starting ArthaInvest CRM...
echo.
echo Starting web server on http://localhost:8000
echo Press Ctrl+C to stop
echo.
python -m http.server 8000 --bind 127.0.0.1
