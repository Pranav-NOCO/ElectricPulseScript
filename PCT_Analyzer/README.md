# WinDaq to Excel Converter

This project provides Python scripts to convert WinDaq files (.wdq, .wdh, .wdc) to Excel format (.xlsx).

## Files in this project

- `windaq_to_excel_converter.py` - Main conversion script
- `convert_example.py` - Example script for your specific WinDaq file
- `requirements.txt` - Python dependencies
- `README.md` - This file

## Installation

1. Make sure you have Python 3.6+ installed
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

Or install individually:
```bash
pip install pandas openpyxl numpy
```

## Usage

### Method 1: Recommended (CSV Export from WinDaq Waveform Browser)

This is the most reliable method:

1. **Export from WinDaq Waveform Browser:**
   - Open your WinDaq file in WinDaq Waveform Browser
   - Select the desired data range using time markers and cursor
   - Go to `File > Save As...`
   - Choose "Spreadsheet print (CSV)" as the file storage format
   - Save with a .csv extension (e.g., `my_data.csv`)
   - You can select options like engineering units, comments, etc.

2. **Convert CSV to Excel:**
   ```bash
   python windaq_to_excel_converter.py my_data.csv
   ```
   
   Or specify output filename:
   ```bash
   python windaq_to_excel_converter.py my_data.csv output.xlsx
   ```

### Method 2: Direct WinDaq File Conversion (Experimental)

Attempt to read WinDaq files directly:

```bash
python windaq_to_excel_converter.py "GB150 BRP2 9000mAh 3S2P Full System 4AWG Diode Bar A 40C Pre-Soak Peak Current Test #2 4-16-25.WDQ"
```

Or use the example script:
```bash
python convert_example.py
```

**Note:** Direct conversion may not work reliably as WinDaq files have a proprietary format. The CSV export method is recommended.

## Command Line Options

```bash
python windaq_to_excel_converter.py --help
```

Options:
- `--force-csv`: Force treating input as CSV file
- `--force-windaq`: Force treating input as WinDaq file

## Examples

Convert a CSV file:
```bash
python windaq_to_excel_converter.py data.csv
```

Convert a WinDaq file:
```bash
python windaq_to_excel_converter.py data.wdq output.xlsx
```

Handle files with spaces in names:
```bash
python windaq_to_excel_converter.py "my data file.csv"
```

## Troubleshooting

### If direct WinDaq conversion fails:

1. The WinDaq file format is proprietary and complex
2. Use the recommended CSV export method instead
3. Make sure WinDaq Waveform Browser is installed on your system

### If CSV conversion fails:

1. Check that the CSV file is properly formatted
2. Try opening the CSV in a text editor to verify the structure
3. The script attempts multiple encodings (UTF-8, Latin-1, etc.)

### Common issues:

- **File not found**: Make sure the file path is correct and the file exists
- **Permission errors**: Ensure you have read access to the input file and write access to the output directory
- **Memory issues**: Very large files may require more RAM

## Output

The script will create an Excel file (.xlsx) with the same name as your input file but with .xlsx extension. The Excel file will contain:

- All data from the original file
- Column headers (if present in the source)
- Proper data types where possible

## Technical Notes

- Uses pandas for data manipulation
- Uses openpyxl for Excel file creation
- Supports multiple text encodings for CSV files
- Includes logging for debugging purposes

## Your Current File

Your WinDaq file: `GB150 BRP2 9000mAh 3S2P Full System 4AWG Diode Bar A 40C Pre-Soak Peak Current Test #2 4-16-25.WDQ`

To convert this file, you can either:
1. Run `python convert_example.py` (attempts direct conversion)
2. Export to CSV from WinDaq Waveform Browser first, then convert the CSV
