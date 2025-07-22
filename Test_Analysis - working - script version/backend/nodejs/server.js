const express = require('express');
const multer = require('multer');
const cors = require('cors');
const path = require('path');
const fs = require('fs-extra');
const { spawn } = require('child_process');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, '..', '..', 'frontend'))); // Serve static files from frontend directory

// Configure multer for file uploads
const storage = multer.diskStorage({
    destination: (req, file, cb) => {
        const uploadDir = path.join(__dirname, 'uploads');
        fs.ensureDirSync(uploadDir);
        cb(null, uploadDir);
    },
    filename: (req, file, cb) => {
        // Keep original filename for processing
        cb(null, file.originalname);
    }
});

const upload = multer({ 
    storage: storage,
    fileFilter: (req, file, cb) => {
        // Accept only Excel files
        if (file.mimetype === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' || 
            file.mimetype === 'application/vnd.ms-excel' ||
            file.originalname.endsWith('.xlsx') || 
            file.originalname.endsWith('.xls')) {
            cb(null, true);
        } else {
            cb(new Error('Only Excel files are allowed!'), false);
        }
    },
    limits: {
        fileSize: 50 * 1024 * 1024 // 50MB limit
    }
});

// Routes
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, '..', '..', 'frontend', 'index.html'));
});

app.post('/api/analyze', upload.single('file'), async (req, res) => {
    try {
        if (!req.file) {
            return res.status(400).json({ error: 'No file uploaded' });
        }

        const inputFile = req.file.path;
        const outputName = req.body.outputName || 'analysis';
        const outputFile = path.join(__dirname, 'uploads', `${outputName}_analysis.xlsx`);

        console.log(`Processing file: ${inputFile}`);
        console.log(`Output will be: ${outputFile}`);

        // Create a modified version of our Python script that accepts command line arguments
        const pythonScript = path.join(__dirname, '..', 'python', 'process_file.py');
        
        // Run Python script
        const pythonProcess = spawn('python', [pythonScript, inputFile, outputFile]);
        
        let pythonOutput = '';
        let pythonError = '';

        pythonProcess.stdout.on('data', (data) => {
            pythonOutput += data.toString();
            console.log('Python output:', data.toString());
        });

        pythonProcess.stderr.on('data', (data) => {
            pythonError += data.toString();
            console.error('Python error:', data.toString());
        });

        pythonProcess.on('close', async (code) => {
            try {
                if (code !== 0) {
                    console.error(`Python script exited with code ${code}`);
                    console.error('Error output:', pythonError);
                    return res.status(500).json({ 
                        error: 'Processing failed', 
                        details: pythonError || 'Unknown error occurred'
                    });
                }

                // Check if output file was created
                if (!await fs.pathExists(outputFile)) {
                    return res.status(500).json({ error: 'Output file was not created' });
                }

                // Parse Python output to extract pulse information
                const pulseMatches = pythonOutput.match(/Pulse (\d+) started at row (\d+)/g);
                const pulseCount = pulseMatches ? pulseMatches.length : 0;
                const dataPointsMatch = pythonOutput.match(/Successfully read (\d+) rows/);
                const dataPoints = dataPointsMatch ? parseInt(dataPointsMatch[1]) : 0;

                // Send file for download
                res.download(outputFile, `${outputName}_analysis.xlsx`, (err) => {
                    if (err) {
                        console.error('Download error:', err);
                        if (!res.headersSent) {
                            res.status(500).json({ error: 'Download failed' });
                        }
                    }
                    
                    // Clean up files after download
                    setTimeout(() => {
                        fs.remove(inputFile).catch(console.error);
                        fs.remove(outputFile).catch(console.error);
                    }, 5000);
                });

            } catch (error) {
                console.error('Post-processing error:', error);
                res.status(500).json({ error: 'Post-processing failed' });
            }
        });

    } catch (error) {
        console.error('Server error:', error);
        res.status(500).json({ error: 'Server error occurred' });
    }
});

// Health check endpoint
app.get('/api/health', (req, res) => {
    res.json({ status: 'OK', message: 'Server is running' });
});

// Error handling middleware
app.use((error, req, res, next) => {
    if (error instanceof multer.MulterError) {
        if (error.code === 'LIMIT_FILE_SIZE') {
            return res.status(400).json({ error: 'File too large. Maximum size is 50MB.' });
        }
    }
    
    console.error('Unhandled error:', error);
    res.status(500).json({ error: error.message || 'Internal server error' });
});

app.listen(PORT, () => {
    console.log('='.repeat(60));
    console.log('Electrical Pulse Analysis Tool - Node.js Server');
    console.log('='.repeat(60));
    console.log(`Server running at: http://localhost:${PORT}`);
    console.log(`Upload endpoint: http://localhost:${PORT}/api/analyze`);
    console.log('\nPress Ctrl+C to stop the server');
    console.log('='.repeat(60));
});
