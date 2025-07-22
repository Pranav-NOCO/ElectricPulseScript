@echo off
REM Electrical Pulse Analysis Tool - Windows Launcher
REM Double-click this file to start the application

title Electrical Pulse Analysis Tool

echo.
echo ================================================================
echo    ELECTRICAL PULSE ANALYSIS TOOL - WINDOWS LAUNCHER
echo ================================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo.
    echo Please install Python 3.7+ from https://python.org
    echo Make sure to check "Add Python to PATH" during installation
    echo.
    pause
    exit /b 1
)

echo Python found - OK
echo.

REM Change to the script directory
cd /d "%~dp0"

REM Check if the launcher script exists
if not exist "scripts\run_program.py" (
    echo ERROR: Launcher script not found!
    echo.
    echo Expected location: %CD%\scripts\run_program.py
    echo Current directory: %CD%
    echo.
    echo Please make sure you're running this from the project root directory.
    echo.
    pause
    exit /b 1
)

REM Run the main launcher script
echo Starting application...
echo.

python scripts\run_program.py

if errorlevel 1 (
    echo.
    echo ERROR: Application failed to start.
    echo Check the error messages above for details.
    echo.
)

echo.
echo Application has stopped.
pause
