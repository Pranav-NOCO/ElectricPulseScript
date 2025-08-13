#!/usr/bin/env python3
"""
Preview the Excel file with pulse summary table
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
    print(f"📊 Reading Excel file: {excel_file.name}")
    print("=" * 80)

    # Read the Raw_Data sheet
    df = pd.read_excel(excel_file, sheet_name='Raw_Data')

    print(f"📋 Dataset Info:")
    print(f"  Rows: {len(df)}")
    print(f"  Columns: {len(df.columns)}")
    print(f"  Column names: {list(df.columns)}")

    # Show first few rows to see the layout
    print(f"\n📑 First 10 rows showing the layout:")
    print("-" * 60)
    print(df.head(10).to_string(index=False))

    # Show the pulse summary area (columns D and E)
    if len(df.columns) >= 5:
        print(f"\n🔋 Pulse Summary Table (from columns D & E):")
        print("-" * 40)
        # Get the pulse summary columns (should be columns 3 and 4, 0-indexed)
        pulse_cols = df.iloc[:10, 3:5]  # Show first 10 rows of columns D and E
        pulse_cols.columns = ['Pulse', 'Peak Current']

        # Filter out empty rows
        pulse_summary = pulse_cols.dropna(how='all')
        if not pulse_summary.empty:
            print(pulse_summary.to_string(index=False))
        else:
            print("No pulse summary data found in expected columns")

    print(f"\n✅ Excel file layout:")
    print(f"   • Columns A & B: Time_seconds and Current (original data)")
    print(f"   • Columns D & E: Pulse summary table")
    print(f"   • Simple format: Pulse 1, Pulse 2, etc. with peak currents")

if __name__ == "__main__":
    main()
