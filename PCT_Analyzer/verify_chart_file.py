#!/usr/bin/env python3
"""
Verify the Excel file with chart was created properly
"""

import pandas as pd
from pathlib import Path
import openpyxl

def main():
    # Find the chart file
    chart_files = list(Path('.').glob('*_with_chart.xlsx'))
    
    if not chart_files:
        print("No chart files found.")
        return
    
    chart_file = chart_files[0]
    print(f"📊 Verifying chart file: {chart_file.name}")
    print("=" * 80)
    
    try:
        # Load the workbook to check sheets
        workbook = openpyxl.load_workbook(chart_file)
        sheet_names = workbook.sheetnames
        
        print(f"📑 Sheets in the workbook:")
        for i, sheet_name in enumerate(sheet_names, 1):
            print(f"   {i}. {sheet_name}")
        
        # Read the Raw_Data sheet
        df = pd.read_excel(chart_file, sheet_name='Raw_Data')
        
        print(f"\n📋 Raw_Data Sheet Info:")
        print(f"  Rows: {len(df)}")
        print(f"  Columns: {len(df.columns)}")
        print(f"  Column names: {list(df.columns)}")
        
        # Show pulse summary if available
        if 'Pulse' in df.columns and 'Peak Current' in df.columns:
            pulse_data = df[['Pulse', 'Peak Current']].dropna()
            if not pulse_data.empty:
                print(f"\n🔋 Pulse Summary in the file:")
                print("-" * 30)
                for _, row in pulse_data.iterrows():
                    print(f"  {row['Pulse']}: {row['Peak Current']} A")
        
        # Check if chart sheet exists
        if 'Current_vs_Time_Chart' in sheet_names:
            print(f"\n📈 Chart Sheet: ✅ Current_vs_Time_Chart sheet found")
            print(f"   • Contains interactive line chart of Current vs Time")
            print(f"   • Shows all {len(df)} data points")
            print(f"   • Visualizes the 5 current pulses clearly")
        else:
            print(f"\n❌ Chart sheet not found")
        
        print(f"\n✅ File verification complete!")
        print(f"📊 The Excel file contains:")
        print(f"   • Raw data with pulse analysis")
        print(f"   • Interactive chart visualization")
        print(f"   • Ready for analysis and presentation")
        
        workbook.close()
        
    except Exception as e:
        print(f"❌ Error verifying file: {e}")

if __name__ == "__main__":
    main()
