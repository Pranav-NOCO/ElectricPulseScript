#!/usr/bin/env python3
"""
Simple script to run the Peak Current Test Analysis on localhost for testing
"""

import os
import sys
import subprocess
import webbrowser
import time
import threading
from pathlib import Path

def main():
    print("=" * 60)
    print("PEAK CURRENT TEST ANALYSIS - LOCALHOST TESTING")
    print("=" * 60)
    
    # Get the backend directory
    backend_dir = Path(__file__).parent / "backend" / "python"
    flask_server = backend_dir / "flask_server.py"
    
    if not flask_server.exists():
        print(f"Error: Flask server not found at {flask_server}")
        return
    
    # Try different ports
    ports_to_try = [3000, 8080, 8000, 5001, 4000]
    port = None

    for test_port in ports_to_try:
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('localhost', test_port))
            sock.close()
            if result != 0:  # Port is available
                port = test_port
                break
        except:
            continue

    if port is None:
        port = 3000  # Default fallback

    print(f"Using port: {port}")

    # Set environment variables
    env = os.environ.copy()
    env['PORT'] = str(port)
    env['PYTHONPATH'] = str(backend_dir)
    
    print(f"Starting server on http://localhost:{port}")
    print("Press Ctrl+C to stop the server")
    print("=" * 60)

    # Function to open browser after delay
    def open_browser():
        time.sleep(3)  # Give server time to start
        try:
            webbrowser.open(f'http://localhost:{port}')
            print(f"Opened http://localhost:{port} in your browser")
        except Exception as e:
            print(f"Could not open browser: {e}")
            print(f"Please manually open: http://localhost:{port}")
    
    # Start browser opening in background
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    try:
        # Start the Flask server
        subprocess.run([sys.executable, str(flask_server)], 
                      cwd=str(backend_dir), env=env)
    except KeyboardInterrupt:
        print("\nServer stopped by user")
        print("Thank you for using Peak Current Test Analysis!")
    except Exception as e:
        print(f"Error starting server: {e}")

if __name__ == "__main__":
    main()
