# Electrical Pulse Analysis Tool - PowerShell Launcher
# Right-click and "Run with PowerShell" to start the application

Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "   ELECTRICAL PULSE ANALYSIS TOOL - POWERSHELL LAUNCHER" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is installed
try {
    $pythonVersion = python --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host " $pythonVersion - OK" -ForegroundColor Green
    } else {
        throw "Python not found"
    }
} catch {
    Write-Host " ERROR: Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install Python 3.7+ from https://python.org" -ForegroundColor Yellow
    Write-Host "Or use Windows Package Manager command: winget install python" - ForegroundColor Yellow
    Write-Host "Make sure to check 'Add Python to PATH' during installation" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host " Starting application..." -ForegroundColor Green
Write-Host ""

# Change to the script directory (go up one level from alt_system_scripts)
$scriptDir = Split-Path -Parent $PSScriptRoot
Set-Location $scriptDir

# Check if the launcher script exists
$launcherScript = Join-Path $scriptDir "scripts\run_program.py"
if (-not (Test-Path $launcherScript)) {
    Write-Host " ERROR: Launcher script not found!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Expected location: $launcherScript" -ForegroundColor Yellow
    Write-Host "Current directory: $(Get-Location)" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Please make sure the project structure is intact." -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

# Run the main launcher script
try {
    python scripts\run_program.py
    if ($LASTEXITCODE -ne 0) {
        Write-Host " Application exited with error code: $LASTEXITCODE" -ForegroundColor Red
    }
} catch {
    Write-Host " Error running application: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "Application has stopped." -ForegroundColor Yellow
Read-Host "Press Enter to exit"
