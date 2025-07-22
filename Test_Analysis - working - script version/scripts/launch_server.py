#!/usr/bin/env python3
"""
Simple HTTP server to serve the Electrical Pulse Analysis Tool locally
"""

import http.server
import socketserver
import webbrowser
import os
import sys

# Configuration
PORT = 8000
HOST = 'localhost'

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Add CORS headers to allow file uploads
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

def main():
    # Change to the directory containing the web files
    web_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(web_dir)
    
    # Create server
    with socketserver.TCPServer((HOST, PORT), CustomHTTPRequestHandler) as httpd:
        url = f"http://{HOST}:{PORT}"
        
        print("=" * 60)
        print(" Electrical Pulse Analysis Tool - Local Server")
        print("=" * 60)
        print(f"Server running at: {url}")
        print(f"Directory: {web_dir}")
        print("\nPress Ctrl+C to stop the server")
        print("=" * 60)
        
        # Try to open browser automatically
        try:
            webbrowser.open(url)
            print(f" Opened {url} in your default browser")
        except Exception as e:
            print(f"  Could not open browser automatically: {e}")
            print(f"Please manually open: {url}")
        
        print("\n Server is ready! Upload an Excel file to test the analysis.")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\n Server stopped by user")
            print("Thanks for using the Electrical Pulse Analysis Tool!")

if __name__ == "__main__":
    main()
