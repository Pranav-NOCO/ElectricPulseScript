#!/usr/bin/env python3
"""
Unified server launcher for the Electrical Pulse Analysis Tool
Supports multiple backend options: Flask, Node.js, or simple HTTP server
"""

import http.server
import socketserver
import webbrowser
import os
import sys
import subprocess
import argparse
from pathlib import Path

# Configuration
DEFAULT_PORT = 8000
HOST = 'localhost'

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        # Set the directory to serve files from
        super().__init__(*args, directory=str(Path(__file__).parent.parent / "frontend"), **kwargs)
    
    def end_headers(self):
        # Add CORS headers to allow file uploads
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

def start_simple_server(port=DEFAULT_PORT):
    """Start a simple HTTP server for frontend-only mode"""
    print("=" * 60)
    print(" Electrical Pulse Analysis Tool - Simple Server")
    print("=" * 60)
    print("Note: This serves the frontend only. For full functionality,")
    print("use --flask or --nodejs options.")
    print("=" * 60)
    
    try:
        with socketserver.TCPServer((HOST, port), CustomHTTPRequestHandler) as httpd:
            url = f"http://{HOST}:{port}"
            print(f"Server running at: {url}")
            print("Press Ctrl+C to stop the server")
            print("=" * 60)
            
            # Try to open browser automatically
            try:
                webbrowser.open(url)
                print(f"Opened {url} in your default browser")
            except Exception as e:
                print(f"Could not open browser automatically: {e}")
                print(f"Please manually open: {url}")
            
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except OSError as e:
        if e.errno == 10048:  # Port already in use
            print(f"Error: Port {port} is already in use")
            print("Try a different port with --port option")
        else:
            print(f"Error starting server: {e}")

def start_flask_server(port=5000):
    """Start the Flask backend server"""
    backend_dir = Path(__file__).parent.parent / "backend" / "python"
    flask_script = backend_dir / "flask_server.py"
    
    if not flask_script.exists():
        print(f"Error: Flask server not found at {flask_script}")
        return
    
    print("=" * 60)
    print(" Electrical Pulse Analysis Tool - Flask Server")
    print("=" * 60)
    print("Starting Flask backend with full analysis capabilities...")
    print("=" * 60)
    
    # Set environment variables
    env = os.environ.copy()
    env['PORT'] = str(port)
    env['PYTHONPATH'] = str(backend_dir)
    
    try:
        subprocess.run([sys.executable, str(flask_script)], 
                      cwd=str(backend_dir), env=env)
    except KeyboardInterrupt:
        print("\nServer stopped by user")

def start_nodejs_server(port=3000):
    """Start the Node.js backend server"""
    backend_dir = Path(__file__).parent.parent / "backend" / "nodejs"
    
    if not (backend_dir / "server.js").exists():
        print(f"Error: Node.js server not found in {backend_dir}")
        return
    
    print("=" * 60)
    print(" Electrical Pulse Analysis Tool - Node.js Server")
    print("=" * 60)
    print("Starting Node.js backend...")
    print("=" * 60)
    
    # Set environment variables
    env = os.environ.copy()
    env['PORT'] = str(port)
    
    try:
        subprocess.run(['node', 'server.js'], cwd=str(backend_dir), env=env)
    except FileNotFoundError:
        print("Error: Node.js not found. Please install Node.js first.")
    except KeyboardInterrupt:
        print("\nServer stopped by user")

def main():
    parser = argparse.ArgumentParser(description='Start the Electrical Pulse Analysis Tool server')
    parser.add_argument('--flask', action='store_true', 
                       help='Start Flask backend server (recommended)')
    parser.add_argument('--nodejs', action='store_true', 
                       help='Start Node.js backend server')
    parser.add_argument('--simple', action='store_true', 
                       help='Start simple HTTP server (frontend only)')
    parser.add_argument('--port', type=int, 
                       help='Port number (default: 8000 for simple, 5000 for Flask, 3000 for Node.js)')
    
    args = parser.parse_args()
    
    # Determine which server to start
    if args.flask:
        port = args.port or 5000
        start_flask_server(port)
    elif args.nodejs:
        port = args.port or 3000
        start_nodejs_server(port)
    elif args.simple:
        port = args.port or DEFAULT_PORT
        start_simple_server(port)
    else:
        # Default: try Flask first, fall back to simple server
        print("No server type specified. Trying Flask server...")
        try:
            port = args.port or 5000
            start_flask_server(port)
        except Exception as e:
            print(f"Flask server failed: {e}")
            print("Falling back to simple HTTP server...")
            port = args.port or DEFAULT_PORT
            start_simple_server(port)

if __name__ == '__main__':
    main()
