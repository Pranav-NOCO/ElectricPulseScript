#!/usr/bin/env python3
"""
Open the Excel file with chart in the default application
"""

import subprocess
import sys
from pathlib import Path

def main():
    # Find the chart file
    chart_files = list(Path('.').glob('*_with_chart.xlsx'))
    
    if not chart_files:
        print("No chart files found.")
        return
    
    chart_file = chart_files[0]
    print(f"📊 Opening Excel file with chart: {chart_file.name}")
    
    try:
        # Open the file with the default application
        if sys.platform == "darwin":  # macOS
            subprocess.run(["open", str(chart_file)])
        elif sys.platform == "win32":  # Windows
            subprocess.run(["start", str(chart_file)], shell=True)
        else:  # Linux
            subprocess.run(["xdg-open", str(chart_file)])
        
        print(f"✅ Excel file opened!")
        print(f"📑 The file contains two sheets:")
        print(f"   1. Raw_Data - Your data with pulse summary table")
        print(f"   2. Current_vs_Time_Chart - Interactive line chart")
        print(f"📈 Click on the 'Current_vs_Time_Chart' tab to see the visualization!")
        
    except Exception as e:
        print(f"❌ Error opening file: {e}")
        print(f"📋 You can manually open: {chart_file}")

if __name__ == "__main__":
    main()
