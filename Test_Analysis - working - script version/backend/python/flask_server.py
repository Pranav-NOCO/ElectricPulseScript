#!/usr/bin/env python3
"""
Flask backend server for the Electrical Pulse Analysis Tool
Uses the existing Python analysis code directly
"""

from flask import Flask, request, jsonify, send_file, render_template_string, send_from_directory
from werkzeug.utils import secure_filename
import os
import tempfile
import shutil
from datetime import datetime
import subprocess
import sys

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

# Import our analysis function
from process_file import copy_raw_data

# HTML template (embedded to avoid separate file)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Electrical Pulse Analysis Tool</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; color: #333; }
        .container { max-width: 800px; margin: 0 auto; padding: 20px; }
        header { text-align: center; margin-bottom: 40px; color: white; }
        header h1 { font-size: 2.5rem; margin-bottom: 10px; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); }
        header p { font-size: 1.1rem; opacity: 0.9; }
        main { background: white; border-radius: 15px; padding: 40px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); margin-bottom: 30px; }
        .upload-section { margin-bottom: 30px; }
        .upload-area { border: 3px dashed #667eea; border-radius: 10px; padding: 60px 20px; text-align: center; cursor: pointer; transition: all 0.3s ease; background: #f8f9ff; }
        .upload-area:hover { border-color: #764ba2; background: #f0f2ff; transform: translateY(-2px); }
        .upload-area.dragover { border-color: #4CAF50; background: #e8f5e8; }
        .upload-icon { font-size: 4rem; margin-bottom: 20px; }
        .upload-area h3 { margin-bottom: 10px; color: #667eea; }
        .upload-area p { color: #666; margin-bottom: 20px; }
        .browse-btn, .process-btn { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; padding: 12px 30px; border-radius: 25px; font-size: 1rem; cursor: pointer; transition: transform 0.2s ease; }
        .browse-btn:hover, .process-btn:hover { transform: translateY(-2px); box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4); }
        .filename-section { margin-bottom: 30px; padding: 20px; background: #f8f9ff; border-radius: 10px; display: none; }
        .filename-section label { display: block; margin-bottom: 10px; font-weight: 600; color: #333; }
        .filename-section input { width: 100%; padding: 12px; border: 2px solid #ddd; border-radius: 8px; font-size: 1rem; transition: border-color 0.3s ease; margin-bottom: 15px; }
        .filename-section input:focus { outline: none; border-color: #667eea; }
        .filename-section small { color: #666; margin-bottom: 15px; display: block; }
        .progress-section { margin-bottom: 30px; text-align: center; display: none; }
        .progress-bar { width: 100%; height: 8px; background: #e0e0e0; border-radius: 4px; overflow: hidden; margin-bottom: 15px; }
        .progress-fill { height: 100%; background: linear-gradient(90deg, #667eea, #764ba2); width: 0%; transition: width 0.3s ease; }
        .results-section { text-align: center; padding: 30px; background: #e8f5e8; border-radius: 10px; margin-bottom: 20px; display: none; }
        .results-section h3 { color: #4CAF50; margin-bottom: 20px; }
        .results-info p { margin-bottom: 10px; font-size: 1.1rem; }
        .error-section { text-align: center; padding: 30px; background: #ffebee; border-radius: 10px; margin-bottom: 20px; display: none; }
        .error-section h3 { color: #f44336; margin-bottom: 15px; }
        .retry-btn { background: #f44336; color: white; border: none; padding: 12px 30px; border-radius: 25px; font-size: 1rem; cursor: pointer; transition: all 0.3s ease; }
        .retry-btn:hover { background: #da190b; transform: translateY(-2px); }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Electrical Pulse Analysis Tool</h1>
            <p>Upload your electrical data Excel file to analyze voltage and current pulses</p>
        </header>
        <main>
            <form id="uploadForm" enctype="multipart/form-data">
                <div class="upload-section">
                    <!-- WinDAQ Files Upload - Primary -->
                    <div class="upload-area" id="windaqUploadArea" style="margin-bottom: 30px;">
                        <div class="upload-icon"><img src="/static/DATAQ_Logo.jpg" alt="DataQ Logo" style="max-width: 80px; max-height: 60px; object-fit: contain;"></div>
                        <h3>Upload WinDAQ File</h3>
                        <p>Drop your .wdh file here or click to browse</p>
                        <input type="file" id="windaqFileInput" name="file" accept=".wdh" hidden>
                        <button type="button" class="browse-btn" onclick="document.getElementById('windaqFileInput').click()">Browse WinDAQ Files</button>
                    </div>

                    <!-- Excel Files Upload - Secondary -->
                    <div style="text-align: center; margin-bottom: 20px;">
                        <p style="color: #666; margin-bottom: 10px;">Or upload Excel files:</p>
                        <input type="file" id="excelFileInput" name="file" accept=".xlsx,.xls" hidden>
                        <button type="button" class="browse-btn" style="padding: 8px 20px; font-size: 0.9rem;" onclick="document.getElementById('excelFileInput').click()">Browse Excel Files</button>
                    </div>
                </div>
                <div class="filename-section" id="filenameSection">
                    <label for="outputName">Output filename (without extension):</label>
                    <input type="text" id="outputName" name="outputName" placeholder="Enter filename">
                    <small>The file will be saved as: [your_name]_analysis.xlsx</small>
                    <button type="submit" class="process-btn">Process File</button>
                </div>
            </form>
            <div class="progress-section" id="progressSection">
                <div class="progress-bar"><div class="progress-fill" id="progressFill"></div></div>
                <p id="progressText">Processing your file...</p>
            </div>
            <div class="results-section" id="resultsSection">
                <h3>Analysis Complete!</h3>
                <div class="results-info">
                    <p><strong>Processing completed successfully!</strong></p>
                    <p>Your file has been analyzed and downloaded.</p>
                </div>
            </div>
            <div class="error-section" id="errorSection">
                <h3>Error</h3>
                <p id="errorMessage"></p>
                <button class="retry-btn" onclick="resetForm()">Try Again</button>
            </div>
        </main>
    </div>
    <script>
        let selectedFile = null;
        const windaqUploadArea = document.getElementById('windaqUploadArea');
        const excelFileInput = document.getElementById('excelFileInput');
        const windaqFileInput = document.getElementById('windaqFileInput');
        const filenameSection = document.getElementById('filenameSection');
        const outputName = document.getElementById('outputName');
        const uploadForm = document.getElementById('uploadForm');
        const progressSection = document.getElementById('progressSection');
        const progressFill = document.getElementById('progressFill');
        const progressText = document.getElementById('progressText');
        const resultsSection = document.getElementById('resultsSection');
        const errorSection = document.getElementById('errorSection');
        const errorMessage = document.getElementById('errorMessage');

        // WinDAQ file upload events (drag & drop)
        windaqUploadArea.addEventListener('dragover', (e) => { e.preventDefault(); windaqUploadArea.classList.add('dragover'); });
        windaqUploadArea.addEventListener('dragleave', (e) => { e.preventDefault(); windaqUploadArea.classList.remove('dragover'); });
        windaqUploadArea.addEventListener('drop', (e) => { e.preventDefault(); windaqUploadArea.classList.remove('dragover'); if (e.dataTransfer.files.length > 0) handleFile(e.dataTransfer.files[0], 'windaq'); });
        windaqFileInput.addEventListener('change', (e) => { if (e.target.files[0]) handleFile(e.target.files[0], 'windaq'); });

        // Excel file upload events (button only)
        excelFileInput.addEventListener('change', (e) => { if (e.target.files[0]) handleFile(e.target.files[0], 'excel'); });

        function handleFile(file, fileType) {
            console.log('File selected:', file.name, 'Type:', file.type, 'Size:', file.size, 'Expected:', fileType);
            const fileName = file.name.toLowerCase();

            // Validate based on expected file type
            if (fileType === 'excel') {
                if (!fileName.endsWith('.xlsx') && !fileName.endsWith('.xls')) {
                    showError('Please select a valid Excel file (.xlsx or .xls)');
                    return;
                }
            } else if (fileType === 'windaq') {
                if (!fileName.endsWith('.wdh')) {
                    showError('Please select a valid WinDAQ file (.wdh)');
                    return;
                }
            }

            console.log('File accepted:', file.name);
            if (file.size > 50 * 1024 * 1024) {
                showError('File too large. Maximum size is 50MB.'); return;
            }
            selectedFile = file;
            outputName.value = file.name.replace(/\\.[^/.]+$/, "");
            filenameSection.style.display = 'block';
        }

        uploadForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            if (!selectedFile) { showError('No file selected'); return; }
            
            const formData = new FormData();
            formData.append('file', selectedFile);
            formData.append('outputName', outputName.value.trim() || 'analysis');
            
            try {
                showProgress(10, 'Uploading file...');
                const response = await fetch('/api/analyze', { method: 'POST', body: formData });
                showProgress(50, 'Processing with Python...');
                
                if (!response.ok) {
                    const errorData = await response.json().catch(() => ({}));
                    throw new Error(errorData.error || `Server error: ${response.status}`);
                }
                
                showProgress(90, 'Preparing download...');
                const blob = await response.blob();
                const downloadUrl = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = downloadUrl;
                a.download = `${outputName.value.trim() || 'analysis'}_analysis.xlsx`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(downloadUrl);
                
                showProgress(100, 'Complete!');
                setTimeout(() => { progressSection.style.display = 'none'; resultsSection.style.display = 'block'; }, 500);
            } catch (error) {
                showError('Processing failed: ' + error.message);
            }
        });

        function showProgress(percent, text) {
            progressSection.style.display = 'block';
            progressFill.style.width = percent + '%';
            progressText.textContent = text;
            resultsSection.style.display = 'none';
            errorSection.style.display = 'none';
        }

        function showError(message) {
            errorSection.style.display = 'block';
            errorMessage.textContent = message;
            progressSection.style.display = 'none';
            resultsSection.style.display = 'none';
        }

        function resetForm() {
            filenameSection.style.display = 'none';
            progressSection.style.display = 'none';
            resultsSection.style.display = 'none';
            errorSection.style.display = 'none';
            excelFileInput.value = '';
            windaqFileInput.value = '';
            outputName.value = '';
            selectedFile = null;
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    # Serve the frontend index.html
    # Go up from backend/python/ to project root, then to frontend/
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    frontend_dir = os.path.join(project_root, 'frontend')
    return send_from_directory(frontend_dir, 'index.html')

@app.route('/css/<filename>')
def css_files(filename):
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    frontend_dir = os.path.join(project_root, 'frontend')
    return send_from_directory(os.path.join(frontend_dir, 'css'), filename)

@app.route('/js/<filename>')
def js_files(filename):
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    frontend_dir = os.path.join(project_root, 'frontend')
    return send_from_directory(os.path.join(frontend_dir, 'js'), filename)

@app.route('/assets/<filename>')
def asset_files(filename):
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    frontend_dir = os.path.join(project_root, 'frontend')
    return send_from_directory(os.path.join(frontend_dir, 'assets'), filename)

@app.route('/api/analyze', methods=['POST'])
def analyze_file():
    try:
        # Check if file was uploaded
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Get output name
        output_name = request.form.get('outputName', 'analysis').strip()
        if not output_name:
            output_name = 'analysis'
        
        # Validate file type (case-insensitive)
        filename_lower = file.filename.lower()
        if not (filename_lower.endswith('.xlsx') or filename_lower.endswith('.xls') or
                filename_lower.endswith('.wdh')):
            return jsonify({'error': f'Invalid file type: {file.filename}. Please upload an Excel (.xlsx, .xls) or WinDAQ (.wdh) file.'}), 400
        
        # Create temporary directory
        temp_dir = tempfile.mkdtemp()
        
        try:
            # Save uploaded file
            input_filename = secure_filename(file.filename)
            input_path = os.path.join(temp_dir, input_filename)
            file.save(input_path)
            
            # Create output path
            output_filename = f"{output_name}_analysis.xlsx"
            output_path = os.path.join(temp_dir, output_filename)
            
            print(f"Processing file: {input_path}")
            print(f"Output will be: {output_path}")
            
            # Process the file using our existing function
            result = copy_raw_data(input_path, output_path)
            
            if not result or not os.path.exists(output_path):
                return jsonify({'error': 'Processing failed - output file not created'}), 500
            
            # Return the processed file
            return send_file(
                output_path,
                as_attachment=True,
                download_name=output_filename,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            
        finally:
            # Clean up temp directory after a delay
            def cleanup():
                try:
                    shutil.rmtree(temp_dir)
                except:
                    pass
            
            # Schedule cleanup (Flask will handle this after response is sent)
            import threading
            threading.Timer(5.0, cleanup).start()
            
    except Exception as e:
        print(f"Error processing file: {e}")
        return jsonify({'error': f'Processing failed: {str(e)}'}), 500

@app.route('/api/health')
def health_check():
    return jsonify({'status': 'OK', 'message': 'Flask server is running'})

@app.route('/debug/paths')
def debug_paths():
    """Debug route to check file paths"""
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    frontend_dir = os.path.join(project_root, 'frontend')
    index_file = os.path.join(frontend_dir, 'index.html')

    return jsonify({
        'current_file': __file__,
        'project_root': project_root,
        'frontend_dir': frontend_dir,
        'index_file': index_file,
        'index_exists': os.path.exists(index_file),
        'frontend_exists': os.path.exists(frontend_dir),
        'frontend_contents': os.listdir(frontend_dir) if os.path.exists(frontend_dir) else 'Directory not found'
    })

@app.errorhandler(413)
def too_large(e):
    return jsonify({'error': 'File too large. Maximum size is 50MB.'}), 413

if __name__ == '__main__':
    # Get port from environment variable (Railway sets this)
    port = int(os.environ.get('PORT', 5000))

    # Debug path information
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    frontend_dir = os.path.join(project_root, 'frontend')
    index_file = os.path.join(frontend_dir, 'index.html')

    print("=" * 60)
    print("Electrical Pulse Analysis Tool - Flask Server")
    print("=" * 60)
    print(f"Server starting on port: {port}")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Flask server file: {__file__}")
    print(f"Project root: {project_root}")
    print(f"Frontend directory: {frontend_dir}")
    print(f"Frontend exists: {os.path.exists(frontend_dir)}")
    print(f"Index file exists: {os.path.exists(index_file)}")
    if os.path.exists(frontend_dir):
        print(f"Frontend contents: {os.listdir(frontend_dir)}")
    print("Press Ctrl+C to stop the server")
    print("=" * 60)

    # Run on all interfaces for Railway deployment
    app.run(debug=False, host='0.0.0.0', port=port)
