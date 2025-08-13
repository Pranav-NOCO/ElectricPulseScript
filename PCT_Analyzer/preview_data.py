#!/usr/bin/env python3
"""
Preview the converted Excel data
"""

import pandas as pd
from pathlib import Path

def main():
    # Find the Excel file
    excel_files = list(Path('.').glob('*.xlsx'))
    
    if not excel_files:
        print("No Excel files found.")
        return
    
    excel_file = excel_files[0]
    print(f"Reading Excel file: {excel_file}")
    
    # Read the Excel file
    df = pd.read_excel(excel_file)
    
    print(f"\nDataset Info:")
    print(f"  Rows: {len(df)}")
    print(f"  Columns: {len(df.columns)}")
    print(f"  Column names: {list(df.columns)}")
    
    print(f"\nFirst 10 rows:")
    print(df.head(10))
    
    print(f"\nLast 10 rows:")
    print(df.tail(10))
    
    print(f"\nData statistics:")
    print(df.describe())
    
    # Check for current data
    if 'Current' in df.columns:
        current_data = df['Current']
        print(f"\nCurrent data analysis:")
        print(f"  Min current: {current_data.min():.6f} Amp")
        print(f"  Max current: {current_data.max():.6f} Amp")
        print(f"  Mean current: {current_data.mean():.6f} Amp")
        print(f"  Peak-to-peak: {current_data.max() - current_data.min():.6f} Amp")
    
    if 'Time_seconds' in df.columns:
        time_data = df['Time_seconds']
        print(f"\nTime data analysis:")
        print(f"  Duration: {time_data.max():.6f} seconds")
        print(f"  Sample rate: {1/(time_data.iloc[1] - time_data.iloc[0]):.1f} Hz")

if __name__ == "__main__":
    main()
