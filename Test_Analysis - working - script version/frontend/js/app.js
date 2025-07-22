// ===== GLOBAL VARIABLES =====
let selectedFile = null;

// ===== DOM ELEMENTS =====
const excelUploadArea = document.getElementById('excelUploadArea');
const windaqUploadArea = document.getElementById('windaqUploadArea');
const excelFileInput = document.getElementById('excelFileInput');
const windaqFileInput = document.getElementById('windaqFileInput');
const filenameSection = document.getElementById('filenameSection');
const outputName = document.getElementById('outputName');
const processBtn = document.getElementById('processBtn');
const progressSection = document.getElementById('progressSection');
const progressFill = document.getElementById('progressFill');
const progressText = document.getElementById('progressText');
const errorSection = document.getElementById('errorSection');
const errorMessage = document.getElementById('errorMessage');

// ===== EVENT LISTENERS =====
document.addEventListener('DOMContentLoaded', function() {
    console.log('Electrical Pulse Analysis Tool loaded');

    // File input change events
    excelFileInput.addEventListener('change', (e) => handleFileSelect(e, 'excel'));
    windaqFileInput.addEventListener('change', (e) => handleFileSelect(e, 'windaq'));

    // Excel upload area events
    excelUploadArea.addEventListener('dragover', (e) => handleDragOver(e, 'excel'));
    excelUploadArea.addEventListener('dragleave', (e) => handleDragLeave(e, 'excel'));
    excelUploadArea.addEventListener('drop', (e) => handleDrop(e, 'excel'));
    excelUploadArea.addEventListener('click', () => excelFileInput.click());

    // WinDAQ upload area events
    windaqUploadArea.addEventListener('dragover', (e) => handleDragOver(e, 'windaq'));
    windaqUploadArea.addEventListener('dragleave', (e) => handleDragLeave(e, 'windaq'));
    windaqUploadArea.addEventListener('drop', (e) => handleDrop(e, 'windaq'));
    windaqUploadArea.addEventListener('click', () => windaqFileInput.click());

    // Form submission (if using form-based approach)
    const form = document.querySelector('form');
    if (form) {
        form.addEventListener('submit', handleFormSubmit);
    }

    // Process button
    if (processBtn) {
        processBtn.addEventListener('click', handleProcessClick);
    }

    // Health check on page load
    checkServerHealth();
});

// ===== FILE HANDLING =====
function handleFileSelect(event, fileType) {
    const file = event.target.files[0];
    if (file) {
        processSelectedFile(file, fileType);
    }
}

function handleDragOver(event, fileType) {
    event.preventDefault();
    const uploadArea = fileType === 'excel' ? excelUploadArea : windaqUploadArea;
    uploadArea.classList.add('dragover');
}

function handleDragLeave(event, fileType) {
    event.preventDefault();
    const uploadArea = fileType === 'excel' ? excelUploadArea : windaqUploadArea;
    uploadArea.classList.remove('dragover');
}

function handleDrop(event, fileType) {
    event.preventDefault();
    const uploadArea = fileType === 'excel' ? excelUploadArea : windaqUploadArea;
    uploadArea.classList.remove('dragover');

    const files = event.dataTransfer.files;
    if (files.length > 0) {
        processSelectedFile(files[0], fileType);
    }
}

function processSelectedFile(file, expectedFileType) {
    const fileName = file.name.toLowerCase();
    const fileExtension = fileName.substring(fileName.lastIndexOf('.'));

    // Validate file type based on expected type
    if (expectedFileType === 'excel') {
        if (!fileName.endsWith('.xlsx') && !fileName.endsWith('.xls')) {
            showError('Please select a valid Excel file (.xlsx or .xls)');
            return;
        }
        console.log('Excel file accepted:', file.name);
    } else if (expectedFileType === 'windaq') {
        if (!fileName.endsWith('.wdh')) {
            showError('Please select a valid WinDAQ file (.wdh)');
            return;
        }
        console.log('WinDAQ file accepted:', file.name);
    }

    // Check file size
    if (file.size > 50 * 1024 * 1024) {
        showError('File too large. Maximum size is 50MB.');
        return;
    }

    selectedFile = file;

    // Set default output name
    const baseName = file.name.replace(/\.[^/.]+$/, "");
    outputName.value = baseName;

    // Show filename section
    filenameSection.style.display = 'block';

    // Visual feedback - highlight the correct upload area
    resetUploadAreas();
    const uploadArea = expectedFileType === 'excel' ? excelUploadArea : windaqUploadArea;
    uploadArea.style.borderColor = '#4CAF50';
    uploadArea.style.backgroundColor = '#e8f5e8';

    console.log('File selected:', file.name, 'Type:', expectedFileType, 'Size:', file.size, 'bytes');
}

function resetUploadAreas() {
    // Reset both upload areas to default styling
    excelUploadArea.style.borderColor = '';
    excelUploadArea.style.backgroundColor = '';
    windaqUploadArea.style.borderColor = '';
    windaqUploadArea.style.backgroundColor = '';
}

// ===== FORM SUBMISSION =====
async function handleFormSubmit(event) {
    event.preventDefault();
    await handleProcessClick();
}

async function handleProcessClick() {
    if (!selectedFile) {
        showError('Please select a file first');
        return;
    }

    const filename = outputName.value.trim() || 'analysis';

    try {
        await processFile(selectedFile, filename);
    } catch (error) {
        console.error('Processing error:', error);
        showError(error.message || 'An error occurred while processing the file');
    }
}

// ===== FILE PROCESSING =====
async function processFile(file, filename) {
    try {
        // Show progress
        showProgress(10, 'Uploading file...');
        
        // Create form data
        const formData = new FormData();
        formData.append('file', file);
        formData.append('outputName', filename);
        
        console.log('Processing file:', file.name);
        console.log('Output name:', filename);
        
        // Upload and process
        showProgress(30, 'Processing with backend...');
        
        const response = await fetch('/api/analyze', {
            method: 'POST',
            body: formData
        });
        
        showProgress(80, 'Finalizing analysis...');
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.error || `Server error: ${response.status}`);
        }
        
        // Handle successful response
        const blob = await response.blob();
        const downloadUrl = window.URL.createObjectURL(blob);
        
        // Show results
        showProgress(100, 'Complete!');
        showResults(downloadUrl, `${filename}_analysis.xlsx`);
        
    } catch (error) {
        console.error('Processing error:', error);
        showError(error.message || 'Processing failed');
    }
}

// ===== UI FUNCTIONS =====
function showProgress(percentage, message) {
    progressSection.style.display = 'block';
    progressFill.style.width = percentage + '%';
    progressText.textContent = message;

    // Hide other sections
    errorSection.style.display = 'none';
}

function showResults(downloadUrl, filename) {
    // Hide progress
    progressSection.style.display = 'none';

    // Automatically trigger download
    const a = document.createElement('a');
    a.href = downloadUrl;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(downloadUrl);

    // Reset the form after download
    setTimeout(() => {
        resetForm();
    }, 1000);

    console.log('Analysis complete, download started');
}

function showError(message) {
    // Hide other sections
    progressSection.style.display = 'none';

    // Show error
    errorSection.style.display = 'block';
    errorMessage.textContent = message;

    console.error('Error:', message);
}

function resetForm() {
    // Hide all sections
    filenameSection.style.display = 'none';
    progressSection.style.display = 'none';
    errorSection.style.display = 'none';

    // Reset form inputs
    excelFileInput.value = '';
    windaqFileInput.value = '';
    outputName.value = '';
    selectedFile = null;

    // Reset upload areas
    resetUploadAreas();

    console.log('Form reset');
}

// ===== UTILITY FUNCTIONS =====
async function checkServerHealth() {
    try {
        const response = await fetch('/api/health');
        if (response.ok) {
            console.log('Backend server is running');
        } else {
            console.warn('Backend server health check failed');
        }
    } catch (error) {
        console.warn('Could not connect to backend server:', error.message);
    }
}

// ===== GLOBAL FUNCTIONS (for HTML onclick) =====
window.handleProcessClick = handleProcessClick;
