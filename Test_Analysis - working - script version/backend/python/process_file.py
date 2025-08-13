#!/usr/bin/env python3
"""
Modified version of data_formatter.py that accepts command line arguments
for use with the Node.js backend
"""

import pandas as pd
import sys
import os
from pathlib import Path

# Import WinDAQ support
try:
    import windaq
    WINDAQ_AVAILABLE = True
except ImportError:
    WINDAQ_AVAILABLE = False
    print("Warning: WinDAQ support not available. windaq.py not found.")

def convert_windaq_to_dataframe(input_file):
    """
    Convert WinDAQ file to pandas DataFrame in the same format as Excel files
    """
    if not WINDAQ_AVAILABLE:
        raise ImportError("WinDAQ support not available. Please ensure windaq.py is in the project directory.")

    print(f"Converting WinDAQ file: {input_file}")

    # Load WinDAQ file
    wfile = windaq.windaq(input_file)
    print(f"Successfully loaded WinDAQ file with {wfile.nChannels} channels")
    print(f"Number of samples per channel: {int(wfile.nSample)}")
    print(f"Time step: {wfile.timeStep} seconds")

    # Create time arrays
    relative_time = wfile.time()

    # Convert to datetime objects for formatting
    start_datetime = pd.to_datetime(wfile.fileCreatedRaw)
    timestamps = [start_datetime + pd.Timedelta(seconds=t) for t in relative_time]

    # Create DataFrame starting with time columns
    data_dict = {
        'Relative Time': relative_time,
        'Date': [ts.strftime('%m/%d/%Y') for ts in timestamps],
        'Time Stamp UTC': [ts.strftime('%I:%M:%S %p') for ts in timestamps]
    }

    # Find voltage and current channels
    volt_channel = None
    amp_channel = None

    for ch in range(1, wfile.nChannels + 1):
        try:
            channel_annotation = wfile.chAnnotation(ch).strip()
            channel_unit = wfile.unit(ch).strip().replace('\x00', '')

            # Look for voltage channel
            if 'volt' in channel_annotation.lower() or 'v' in channel_unit.lower():
                volt_channel = ch
                data_dict['Volt '] = wfile.data(ch)
                print(f"  Found voltage channel {ch}: {channel_annotation} ({channel_unit})")

            # Look for current/amp channel
            elif 'amp' in channel_annotation.lower() or 'current' in channel_annotation.lower() or 'a' in channel_unit.lower():
                amp_channel = ch
                data_dict['Amp '] = wfile.data(ch)
                print(f"  Found current channel {ch}: {channel_annotation} ({channel_unit})")

            # Add other channels with their original names
            else:
                if channel_unit:
                    col_name = channel_unit
                elif channel_annotation:
                    col_name = channel_annotation
                else:
                    col_name = f"Channel {ch}"
                data_dict[col_name] = wfile.data(ch)
                print(f"  Added channel {ch}: {channel_annotation} -> {col_name}")

        except Exception as e:
            print(f"Warning: Could not read channel {ch}: {e}")
            continue

    # Verify we found the required channels
    if volt_channel is None:
        print("Warning: No voltage channel found. Looking for any channel that might be voltage...")
        # Try first channel as voltage
        if wfile.nChannels >= 1:
            data_dict['Volt '] = wfile.data(1)
            print(f"  Using channel 1 as voltage")

    if amp_channel is None:
        print("Warning: No current channel found. Looking for any channel that might be current...")
        # Try second channel as current
        if wfile.nChannels >= 2:
            data_dict['Amp '] = wfile.data(2)
            print(f"  Using channel 2 as current")

    # Create DataFrame
    df = pd.DataFrame(data_dict)
    print(f"Created DataFrame with {len(df)} rows and columns: {list(df.columns)}")

    return df

def analyze_peak_currents(input_file):
    """
    Analyze peak currents and return data for frontend display
    Returns a dictionary with peak current data and raw data
    """
    print(f"Analyzing peak currents from {input_file}...")

    try:
        # Check file extension to determine how to read it
        file_ext = Path(input_file).suffix.lower()

        if file_ext in ['.wdh', '.wdq']:
            # Handle WinDAQ files
            print("Detected WinDAQ file format")
            df_raw = convert_windaq_to_dataframe(input_file)
        else:
            # Handle Excel files
            print("Detected Excel file format")
            df_raw = pd.read_excel(input_file)

        print(f"Successfully read {len(df_raw)} rows of data")
        print(f"Original columns: {df_raw.columns.tolist()}")

        # Remove the "Chn 1 Events" column if it exists
        if 'Chn 1 Events' in df_raw.columns:
            df_raw = df_raw.drop('Chn 1 Events', axis=1)
            print("Removed 'Chn 1 Events' column")

        # Detect pulses and extract peak currents
        current_col = 'Amp '  # This will become "Current [A]"

        # Pulse detection parameters
        baseline_threshold = 10  # Current values below this are considered baseline
        pulse_start_threshold = 50  # Minimum current jump to start a pulse
        pulse_end_threshold = 20   # Current must drop below this to end a pulse

        print("Detecting pulses dynamically...")
        print(f"Baseline threshold: {baseline_threshold}A, Pulse start: {pulse_start_threshold}A, Pulse end: {pulse_end_threshold}A")

        # First pass: detect all pulses
        pulse_ranges = {}  # Store start/end rows for each pulse
        current_pulse = 0
        in_pulse = False

        for i in range(len(df_raw)):
            current_value = df_raw.iloc[i][current_col]

            if i > 0:
                prev_value = df_raw.iloc[i-1][current_col]

                # Check for pulse start - significant jump in current from baseline
                if not in_pulse and prev_value < baseline_threshold and current_value > pulse_start_threshold:
                    current_pulse += 1
                    in_pulse = True
                    pulse_ranges[current_pulse] = {'start': i}
                    print(f"Pulse {current_pulse} started at row {i}: {prev_value:.2f}A -> {current_value:.2f}A (jump: {current_value - prev_value:.2f}A)")

                # Check for pulse end - current drops back below threshold
                elif in_pulse and current_value < pulse_end_threshold:
                    pulse_ranges[current_pulse]['end'] = i
                    in_pulse = False
                    print(f"Pulse {current_pulse} ended at row {i}: {prev_value:.2f}A -> {current_value:.2f}A")

        # If we're still in a pulse at the end, close it
        if in_pulse:
            pulse_ranges[current_pulse]['end'] = len(df_raw) - 1
            print(f"Pulse {current_pulse} ended at end of data (row {len(df_raw) - 1})")

        print(f"Total pulses detected: {len(pulse_ranges)}")

        # Calculate peak currents for each pulse
        peak_currents = []
        for pulse_num in sorted(pulse_ranges.keys()):
            start_idx = pulse_ranges[pulse_num]['start']
            end_idx = pulse_ranges[pulse_num]['end']

            # Get pulse data
            pulse_data = df_raw.iloc[start_idx:end_idx + 1][current_col]
            peak_current = pulse_data.max()
            peak_time = df_raw.iloc[start_idx:end_idx + 1]['Relative Time'].iloc[pulse_data.idxmax() - start_idx]

            peak_currents.append({
                'pulse_number': pulse_num,
                'peak_current': round(peak_current, 2),
                'peak_time': round(peak_time, 3),
                'start_time': round(df_raw.iloc[start_idx]['Relative Time'], 3),
                'end_time': round(df_raw.iloc[end_idx]['Relative Time'], 3),
                'duration': round(df_raw.iloc[end_idx]['Relative Time'] - df_raw.iloc[start_idx]['Relative Time'], 3)
            })

            print(f"Pulse {pulse_num}: Peak = {peak_current:.2f}A at {peak_time:.3f}s")

        # Prepare raw data for frontend
        raw_data = {
            'time': df_raw['Relative Time'].tolist(),
            'current': df_raw[current_col].tolist(),
            'voltage': df_raw['Volt '].tolist() if 'Volt ' in df_raw.columns else []
        }

        return {
            'success': True,
            'peak_currents': peak_currents,
            'raw_data': raw_data,
            'total_pulses': len(pulse_ranges),
            'file_info': {
                'total_samples': len(df_raw),
                'duration': round(df_raw['Relative Time'].max(), 3),
                'sampling_rate': round(len(df_raw) / df_raw['Relative Time'].max(), 1)
            }
        }

    except Exception as e:
        print(f"Error analyzing file: {e}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': str(e)
        }

def copy_raw_data(input_file, output_file):
    print(f"Reading data from {input_file}...")

    try:
        # Check file extension to determine how to read it
        file_ext = Path(input_file).suffix.lower()

        if file_ext in ['.wdh']:
            # Handle WinDAQ files
            print("Detected WinDAQ file format")
            df_raw = convert_windaq_to_dataframe(input_file)
        else:
            # Handle Excel files
            print("Detected Excel file format")
            df_raw = pd.read_excel(input_file)
        print(f"Successfully read {len(df_raw)} rows of data")
        print(f"Original columns: {df_raw.columns.tolist()}")
        
        # Remove the "Chn 1 Events" column
        if 'Chn 1 Events' in df_raw.columns:
            df_raw = df_raw.drop('Chn 1 Events', axis=1)
            print("Removed 'Chn 1 Events' column")
        
        # Detect pulses based on current jumps (assuming "Amp " column)
        current_col = 'Amp '  # This will become "Current [A]"

        # Pulse detection parameters
        baseline_threshold = 10  # Current values below this are considered baseline
        pulse_start_threshold = 50  # Minimum current jump to start a pulse
        pulse_end_threshold = 20   # Current must drop below this to end a pulse

        print("Detecting pulses dynamically...")
        print(f"Baseline threshold: {baseline_threshold}A, Pulse start: {pulse_start_threshold}A, Pulse end: {pulse_end_threshold}A")

        # First pass: detect all pulses
        pulse_ranges = {}  # Store start/end rows for each pulse
        current_pulse = 0
        in_pulse = False

        for i in range(len(df_raw)):
            current_value = df_raw.iloc[i][current_col]

            if i > 0:
                prev_value = df_raw.iloc[i-1][current_col]

                # Check for pulse start - significant jump in current from baseline
                if not in_pulse and prev_value < baseline_threshold and current_value > pulse_start_threshold:
                    current_pulse += 1
                    in_pulse = True
                    pulse_ranges[current_pulse] = {'start': i + 10}  # +10 because data starts at row 10
                    print(f"Pulse {current_pulse} started at row {i+10}: {prev_value:.2f}A -> {current_value:.2f}A (jump: {current_value - prev_value:.2f}A)")

                # Check for pulse end - current drops back below threshold
                elif in_pulse and current_value < pulse_end_threshold:
                    pulse_ranges[current_pulse]['end'] = i + 9  # +9 because this is the last row of pulse
                    in_pulse = False
                    print(f"Pulse {current_pulse} ended at row {i+9}: {prev_value:.2f}A -> {current_value:.2f}A")

        # If we're still in a pulse at the end, close it
        if in_pulse:
            pulse_ranges[current_pulse]['end'] = len(df_raw) + 9
            print(f"Pulse {current_pulse} ended at end of data (row {len(df_raw) + 9})")

        print(f"Total pulses detected: {len(pulse_ranges)}")
        print(f"Pulse ranges: {pulse_ranges}")

        # Second pass: create pulse labels and formulas
        pulse_labels = []
        value_formulas = []
        desc_labels = []
        pulse_formula_locations = {}  # Track where each formula is located

        for i in range(len(df_raw)):
            current_value = df_raw.iloc[i][current_col]

            # Determine which pulse this row belongs to
            row_pulse = None
            for pulse_num, pulse_range in pulse_ranges.items():
                if pulse_range['start'] <= i + 10 <= pulse_range['end']:
                    row_pulse = pulse_num
                    break

            if row_pulse:
                pulse_labels.append(row_pulse)
            else:
                pulse_labels.append("")

            # Initialize formula columns
            value_formulas.append("")
            desc_labels.append("")

        # Now add the formulas for each pulse and track their locations
        for pulse_num in pulse_ranges:
            start_row = pulse_ranges[pulse_num]['start']
            end_row = pulse_ranges[pulse_num]['end']
            pulse_formula_locations[pulse_num] = {}

            # Find the first occurrence of this pulse to add Peak [A] formula only
            first_occurrence = pulse_labels.index(pulse_num)

            # Add Peak [A] formula
            value_formulas[first_occurrence] = f"=MAX(E{start_row}:E{end_row})"
            desc_labels[first_occurrence] = "Peak [A]"
            pulse_formula_locations[pulse_num]['peak_a'] = first_occurrence + 10  # +10 for data start row

        # Add the pulse detection and formula columns
        df_raw['Pulse #'] = pulse_labels
        df_raw['Value'] = value_formulas
        df_raw['Desc'] = desc_labels

        print(f"Pulse ranges detected: {pulse_ranges}")
        print(f"Formula locations: {pulse_formula_locations}")

        # Create the Excel file using XlsxWriter for better chart support
        with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
            # Get the workbook and worksheet objects
            workbook = writer.book

            # Create Raw Data sheet
            raw_data_sheet = workbook.add_worksheet('Raw Data')

            # Write raw data headers
            raw_headers = ["Time (s)", "Current (A)"]
            for col, header in enumerate(raw_headers):
                raw_data_sheet.write(0, col, header)

            # Write raw data
            for row, (time_val, current_val) in enumerate(zip(df_raw['Relative Time'], df_raw[current_col]), 1):
                raw_data_sheet.write(row, 0, time_val)
                raw_data_sheet.write(row, 1, current_val)

            # Create Peak Current Analysis sheet
            analysis_sheet = workbook.add_worksheet('Peak Current Analysis')

            # Create summary table for peak currents
            analysis_sheet.write(0, 0, "Pulse Analysis Summary")
            analysis_sheet.write(2, 0, "Pulse #")
            analysis_sheet.write(2, 1, "Peak Current (A)")

            # Write peak current data for each detected pulse
            for i, pulse_num in enumerate(sorted(pulse_ranges.keys())):
                start_row = pulse_ranges[pulse_num]['start']
                end_row = pulse_ranges[pulse_num]['end']

                # Calculate peak current directly from data
                pulse_data = df_raw.iloc[start_row-10:end_row-9][current_col]  # Adjust for row offset
                peak_current = pulse_data.max()

                analysis_sheet.write(3 + i, 0, f"Pulse {pulse_num}")
                analysis_sheet.write(3 + i, 1, peak_current)

            # Create the main data sheet with all original data
            main_sheet = workbook.add_worksheet('All Data')

            # Define the column headers for main sheet
            main_headers = ["Relative Time", "Date", "Time Stamp UTC", "Clamp [V]", "Current [A]", "Pulse #", "Value", "Desc"]

            # Write headers
            for col, header in enumerate(main_headers):
                main_sheet.write(0, col, header)

            # Write main data
            for row in range(len(df_raw)):
                main_sheet.write(row + 1, 0, df_raw.iloc[row]['Relative Time'])
                main_sheet.write(row + 1, 1, df_raw.iloc[row]['Date'])
                main_sheet.write(row + 1, 2, df_raw.iloc[row]['Time Stamp UTC'])
                main_sheet.write(row + 1, 3, df_raw.iloc[row]['Volt '])
                main_sheet.write(row + 1, 4, df_raw.iloc[row][current_col])
                main_sheet.write(row + 1, 5, pulse_labels[row] if pulse_labels[row] else "")
                main_sheet.write(row + 1, 6, value_formulas[row])
                main_sheet.write(row + 1, 7, desc_labels[row])

            # Create a chart sheet for Current vs Time
            chartsheet = workbook.add_chartsheet('Current vs Time Chart')

            # Create a line chart
            chart = workbook.add_chart({'type': 'line'})

            # Add current data series
            chart.add_series({
                'name': 'Current [A]',
                'categories': ['Raw Data', 1, 0, len(df_raw), 0],  # Time column
                'values': ['Raw Data', 1, 1, len(df_raw), 1],      # Current column
                'line': {'color': '#ff8c00', 'width': 2}           # Orange, thick line
            })

            # Configure chart
            chart.set_title({'name': 'Current vs Time'})
            chart.set_x_axis({'name': 'Time (seconds)'})
            chart.set_y_axis({'name': 'Current (A)'})
            chart.set_legend({'position': 'bottom'})

            # Add chart to the chart sheet
            chartsheet.set_chart(chart)

        print(f"Data processed and saved to {output_file}")
        print(f"Created {len(pulse_ranges)} pulse analysis with the following sheets:")
        print("  - Raw Data: Time and Current columns")
        print("  - Peak Current Analysis: Summary of peak currents for all pulses")
        print("  - All Data: Complete dataset with pulse detection")
        print("  - Current vs Time Chart: Graph of current vs time")
        print(f"Total pulses detected: {len(pulse_ranges)}")

        return output_file
        
    except Exception as e:
        print(f"Error reading/writing file: {e}")
        return None

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python process_file.py <input_file> <output_file>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' does not exist")
        sys.exit(1)
    
    result = copy_raw_data(input_file, output_file)
    
    if result:
        print(f"SUCCESS: Analysis complete. Output saved to {result}")
        sys.exit(0)
    else:
        print("ERROR: Processing failed")
        sys.exit(1)
