#!/usr/bin/env python3
"""
Example script to convert the WinDaq file in this directory to Excel.

This script demonstrates how to use the windaq_to_excel_converter module.
"""

import os
import sys
from pathlib import Path
from windaq_to_excel_converter import convert_csv_to_excel, convert_windaq_direct

def main():
    # Find the WinDaq file in the current directory
    current_dir = Path('.')
    wdq_files = list(current_dir.glob('*.WDQ')) + list(current_dir.glob('*.wdq'))
    
    if not wdq_files:
        print("No WinDaq files (.WDQ or .wdq) found in the current directory.")
        return
    
    # Use the first WinDaq file found
    wdq_file = wdq_files[0]
    print(f"Found WinDaq file: {wdq_file}")
    
    # Generate output filename
    excel_file = wdq_file.with_suffix('.xlsx')
    
    print(f"Converting to: {excel_file}")
    
    try:
        # Attempt direct conversion first
        print("Attempting direct WinDaq file conversion...")
        output_file = convert_windaq_direct(str(wdq_file), str(excel_file))
        print(f"Success! Converted to: {output_file}")
        
    except Exception as e:
        print(f"Direct conversion failed: {e}")
        print("\nRecommended approach:")
        print("1. Open your WinDaq file in WinDaq Waveform Browser")
        print("2. Go to File > Save As...")
        print("3. Choose 'Spreadsheet print (CSV)' format")
        print("4. Save as a .csv file")
        print("5. Then run:")
        print(f"   python windaq_to_excel_converter.py your_exported_file.csv")

if __name__ == "__main__":
    main()
