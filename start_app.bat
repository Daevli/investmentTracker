@echo off
echo Starting Investment Tracker...
echo.

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Start Flask application in the background
start /B python app.py

REM Wait a moment for the server to start
timeout /t 3 /nobreak > nul

REM Open browser to the application home page
start http://localhost:5000

echo.
echo Investment Tracker is running!
echo Press Ctrl+C in the application window to stop the server when done.