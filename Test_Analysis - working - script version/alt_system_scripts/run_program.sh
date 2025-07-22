#!/bin/bash
# Electrical Pulse Analysis Tool - Linux/Mac Launcher
# Run: chmod +x run_program.sh && ./run_program.sh

echo ""
echo "================================================================"
echo "   ELECTRICAL PULSE ANALYSIS TOOL - LINUX/MAC LAUNCHER"
echo "================================================================"
echo ""

# Check if Python is installed
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
    echo "✅ $(python3 --version) - OK"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
    echo "✅ $(python --version) - OK"
else
    echo "❌ ERROR: Python is not installed or not in PATH"
    echo ""
    echo "Please install Python 3.7+ from your package manager:"
    echo "  Ubuntu/Debian: sudo apt install python3 python3-pip"
    echo "  CentOS/RHEL:   sudo yum install python3 python3-pip"
    echo "  macOS:         brew install python3"
    echo ""
    read -p "Press Enter to exit"
    exit 1
fi

echo ""
echo "🚀 Starting application..."
echo ""

# Change to the project root directory (go up one level from alt_system_scripts)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

# Check if the launcher script exists
LAUNCHER_SCRIPT="$PROJECT_ROOT/scripts/run_program.py"
if [ ! -f "$LAUNCHER_SCRIPT" ]; then
    echo "❌ ERROR: Launcher script not found!"
    echo ""
    echo "Expected location: $LAUNCHER_SCRIPT"
    echo "Current directory: $(pwd)"
    echo ""
    echo "Please make sure the project structure is intact."
    echo ""
    read -p "Press Enter to exit"
    exit 1
fi

# Run the main launcher script
$PYTHON_CMD scripts/run_program.py

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Application exited with error code: $?"
fi

echo ""
echo "Application has stopped."
read -p "Press Enter to exit"
