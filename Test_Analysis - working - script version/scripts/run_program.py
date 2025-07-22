#!/usr/bin/env python3
"""
Electrical Pulse Analysis Tool - One-Click Launcher
Automatically checks dependencies, installs if needed, and starts the application
"""

import os
import sys
import subprocess
import importlib
import webbrowser
import time
from pathlib import Path

# Configuration
REQUIRED_PYTHON_VERSION = (3, 7)
DEFAULT_PORT = 5000
PROJECT_ROOT = Path(__file__).parent.parent

def print_banner():
    """Print application banner"""
    print("=" * 70)
    print("    ELECTRICAL PULSE ANALYSIS TOOL - ONE-CLICK LAUNCHER")
    print("=" * 70)
    print("Professional electrical data analysis in your browser")
    print("Supports Excel (.xlsx, .xls) and WinDAQ (.wdh) files")
    print("Features black background theme for better visibility")
    print("=" * 70)

def check_python_version():
    """Check if Python version meets requirements"""
    current_version = sys.version_info[:2]
    if current_version < REQUIRED_PYTHON_VERSION:
        print(f"Error: Python {REQUIRED_PYTHON_VERSION[0]}.{REQUIRED_PYTHON_VERSION[1]}+ required")
        print(f"   Current version: {current_version[0]}.{current_version[1]}")
        print("   Please upgrade Python and try again.")
        return False
    
    print(f"Python {current_version[0]}.{current_version[1]} - OK")
    return True

def check_pip():
    """Check if pip is available"""
    try:
        import pip
        print("pip - OK")
        return True
    except ImportError:
        print("pip not found. Please install pip and try again.")
        return False

def check_requirements():
    """Check if required packages are installed"""
    requirements_file = PROJECT_ROOT / "config" / "requirements.txt"
    
    if not requirements_file.exists():
        print(f"Requirements file not found: {requirements_file}")
        return False
    
    print("Checking Python dependencies...")
    
    # Read requirements
    with open(requirements_file, 'r') as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    
    missing_packages = []
    
    for requirement in requirements:
        # Extract package name (handle version specifiers)
        package_name = requirement.split('==')[0].split('>=')[0].split('<=')[0].split('>')[0].split('<')[0].strip()
        
        try:
            importlib.import_module(package_name.replace('-', '_'))
            print(f"  {package_name}")
        except ImportError:
            print(f"  {package_name} - Missing")
            missing_packages.append(requirement)
    
    return missing_packages

def install_requirements(missing_packages):
    """Install missing packages"""
    if not missing_packages:
        return True
    
    print(f"\n Installing {len(missing_packages)} missing packages...")
    
    requirements_file = PROJECT_ROOT / "config" / "requirements.txt"
    
    try:
        # Install all requirements at once
        cmd = [sys.executable, "-m", "pip", "install", "-r", str(requirements_file)]
        print(f"Running: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(" All dependencies installed successfully!")
            return True
        else:
            print(" Failed to install dependencies:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f" Error installing dependencies: {e}")
        return False

def start_server(port=DEFAULT_PORT):
    """Start the Flask server"""
    print(f"\n Starting Electrical Pulse Analysis Tool on port {port}...")
    
    # Change to backend directory
    backend_dir = PROJECT_ROOT / "backend" / "python"
    
    if not backend_dir.exists():
        print(f" Backend directory not found: {backend_dir}")
        return False
    
    flask_server = backend_dir / "flask_server.py"
    
    if not flask_server.exists():
        print(f" Flask server not found: {flask_server}")
        return False
    
    # Set environment variables
    env = os.environ.copy()
    env['PORT'] = str(port)
    env['PYTHONPATH'] = str(backend_dir)
    
    url = f"http://localhost:{port}"
    
    print("=" * 70)
    print(f" Server starting at: {url}")
    print(" Serving frontend from: frontend/")
    print(" Backend: Flask (Python)")
    print("=" * 70)
    print(" USAGE:")
    print("  1. Upload your Excel (.xlsx, .xls) or WinDAQ (.wdh) file")
    print("  2. Enter output filename (optional)")
    print("  3. Click process and download your analysis")
    print("=" * 70)
    print("Press Ctrl+C to stop the server")
    print("=" * 70)
    
    # Try to open browser after a short delay
    def open_browser():
        time.sleep(2)  # Give server time to start
        try:
            webbrowser.open(url)
            print(f" Opened {url} in your default browser")
        except Exception as e:
            print(f"  Could not open browser automatically: {e}")
            print(f"   Please manually open: {url}")
    
    # Start browser opening in background
    import threading
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    try:
        # Start the Flask server
        subprocess.run([sys.executable, str(flask_server)], 
                      cwd=str(backend_dir), env=env)
    except KeyboardInterrupt:
        print("\n Server stopped by user")
        print(" Thank you for using Electrical Pulse Analysis Tool!")
    except Exception as e:
        print(f" Error starting server: {e}")
        return False
    
    return True

def main():
    """Main function"""
    print_banner()
    
    # Check Python version
    if not check_python_version():
        input("Press Enter to exit...")
        return
    
    # Check pip
    if not check_pip():
        input("Press Enter to exit...")
        return
    
    # Check and install requirements
    missing_packages = check_requirements()
    
    if missing_packages:
        print(f"\nFound {len(missing_packages)} missing dependencies")
        response = input(" Would you like to install them automatically? (y/n): ").lower().strip()
        
        if response in ['y', 'yes']:
            if not install_requirements(missing_packages):
                print(" Failed to install dependencies. Please install manually:")
                print(f"   pip install -r {PROJECT_ROOT}/config/requirements.txt")
                input("Press Enter to exit...")
                return
        else:
            print("  Cannot continue without required dependencies.")
            print("   Please install manually and run again:")
            print(f"   pip install -r {PROJECT_ROOT}/config/requirements.txt")
            input("Press Enter to exit...")
            return
    else:
        print(" All dependencies are installed!")
    
    # Start the server
    print("\n" + "=" * 70)
    start_server()

if __name__ == "__main__":
    main()
