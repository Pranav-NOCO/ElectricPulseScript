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
        pulse_labels = []
        value_formulas = []
        desc_labels = []
        current_pulse = 0
        in_pulse = False
        pulse_ranges = {}  # Store start/end rows for each pulse
        pulse_formula_locations = {}  # Track where each formula is located

        # Pulse detection parameters
        baseline_threshold = 10  # Current values below this are considered baseline
        pulse_start_threshold = 50  # Minimum current jump to start a pulse
        pulse_end_threshold = 20   # Current must drop below this to end a pulse

        print("Detecting pulses with fixed thresholds...")
        print(f"Baseline threshold: {baseline_threshold}A, Pulse start: {pulse_start_threshold}A, Pulse end: {pulse_end_threshold}A")
        
        for i in range(len(df_raw)):
            current_value = df_raw.iloc[i][current_col]

            if i == 0:
                # First row
                pulse_labels.append("")
                value_formulas.append("")
                desc_labels.append("")
            else:
                prev_value = df_raw.iloc[i-1][current_col]

                # Check for pulse start - significant jump in current from baseline
                if not in_pulse and prev_value < baseline_threshold and current_value > pulse_start_threshold:
                    current_pulse += 1
                    in_pulse = True
                    pulse_labels.append(current_pulse)
                    pulse_ranges[current_pulse] = {'start': i + 10}  # +10 because data starts at row 10
                    print(f"Pulse {current_pulse} started at row {i+10}: {prev_value:.2f}A -> {current_value:.2f}A (jump: {current_value - prev_value:.2f}A)")

                    # Add formulas for this pulse
                    value_formulas.append("")
                    desc_labels.append("")

                # Check for pulse end - current drops back below threshold
                elif in_pulse and current_value < pulse_end_threshold:
                    pulse_ranges[current_pulse]['end'] = i + 9  # +9 because this is the last row of pulse
                    in_pulse = False
                    pulse_labels.append("")
                    value_formulas.append("")
                    desc_labels.append("")
                    print(f"Pulse {current_pulse} ended at row {i+9}: {prev_value:.2f}A -> {current_value:.2f}A")

                # Continue current state
                elif in_pulse:
                    pulse_labels.append(current_pulse)
                    value_formulas.append("")
                    desc_labels.append("")
                else:
                    pulse_labels.append("")
                    value_formulas.append("")
                    desc_labels.append("")

                # Stop after 3 pulses
                if current_pulse >= 3 and not in_pulse:
                    # Fill remaining rows with empty labels
                    remaining = len(df_raw) - len(pulse_labels)
                    pulse_labels.extend([""] * remaining)
                    value_formulas.extend([""] * remaining)
                    desc_labels.extend([""] * remaining)
                    break
        
        # Now add the formulas for each pulse and track their locations
        for pulse_num in pulse_ranges:
            start_row = pulse_ranges[pulse_num]['start']
            end_row = pulse_ranges[pulse_num]['end']
            pulse_formula_locations[pulse_num] = {}
            
            # Find the first occurrence of this pulse to add formulas
            first_occurrence = pulse_labels.index(pulse_num)
            
            # Add Min [V] formula
            value_formulas[first_occurrence] = f"=MIN(D{start_row}:D{end_row})"
            desc_labels[first_occurrence] = "Min [V]"
            pulse_formula_locations[pulse_num]['min_v'] = first_occurrence + 10  # +10 for data start row
            
            # Add Peak [A] formula (find next empty spot in this pulse)
            for j in range(first_occurrence + 1, len(pulse_labels)):
                if pulse_labels[j] == pulse_num and value_formulas[j] == "":
                    value_formulas[j] = f"=MAX(E{start_row}:E{end_row})"
                    desc_labels[j] = "Peak [A]"
                    pulse_formula_locations[pulse_num]['peak_a'] = j + 10  # +10 for data start row
                    break

            # Add Joules [J] formula (find next empty spot in this pulse)
            for j in range(first_occurrence + 1, len(pulse_labels)):
                if pulse_labels[j] == pulse_num and value_formulas[j] == "":
                    count_formula = f"COUNT(E{start_row}:E{end_row})"
                    value_formulas[j] = f"=AVERAGE(D{start_row}:D{end_row})*AVERAGE(E{start_row}:E{end_row})*{count_formula}/100"
                    desc_labels[j] = "Joules [J]"
                    pulse_formula_locations[pulse_num]['joules'] = j + 10  # +10 for data start row
                    break
        
        # Add the pulse detection and formula columns
        df_raw['Pulse #'] = pulse_labels
        df_raw['Value'] = value_formulas
        df_raw['Desc'] = desc_labels
        
        print(f"Pulse ranges detected: {pulse_ranges}")
        print(f"Formula locations: {pulse_formula_locations}")
        
        # Define the new column headers in the specified order
        new_headers = ["Relative Time", "Date", "Time Stamp UTC", "Clamp [V]", "Current [A]", "Pulse #", "Value", "Desc"]
        
        print(f"New column headers: {new_headers}")
        
        # Create the Excel file using XlsxWriter for better chart support
        with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
            # Create summary table data with direct cell references to the calculated values
            summary_table = [
                ["", "", "", "", "", "", "", ""],  # Empty row
                ["", "Pulse #", "Min [V]", "Peak [A]", "Joules [J]", "", "", ""],
                ["", "1",
                 f"=G{pulse_formula_locations[1]['min_v']}" if 1 in pulse_formula_locations and 'min_v' in pulse_formula_locations[1] else "",
                 f"=G{pulse_formula_locations[1]['peak_a']}" if 1 in pulse_formula_locations and 'peak_a' in pulse_formula_locations[1] else "",
                 f"=G{pulse_formula_locations[1]['joules']}" if 1 in pulse_formula_locations and 'joules' in pulse_formula_locations[1] else "",
                 "", "", ""],
                ["", "2",
                 f"=G{pulse_formula_locations[2]['min_v']}" if 2 in pulse_formula_locations and 'min_v' in pulse_formula_locations[2] else "",
                 f"=G{pulse_formula_locations[2]['peak_a']}" if 2 in pulse_formula_locations and 'peak_a' in pulse_formula_locations[2] else "",
                 f"=G{pulse_formula_locations[2]['joules']}" if 2 in pulse_formula_locations and 'joules' in pulse_formula_locations[2] else "",
                 "", "", ""],
                ["", "3",
                 f"=G{pulse_formula_locations[3]['min_v']}" if 3 in pulse_formula_locations and 'min_v' in pulse_formula_locations[3] else "",
                 f"=G{pulse_formula_locations[3]['peak_a']}" if 3 in pulse_formula_locations and 'peak_a' in pulse_formula_locations[3] else "",
                 f"=G{pulse_formula_locations[3]['joules']}" if 3 in pulse_formula_locations and 'joules' in pulse_formula_locations[3] else "",
                 "", "", ""],
                ["", "", "", "", "", "", "", ""],  # Empty row
                ["", "", "", "", "", "", "", ""],  # Empty row
                ["", "", "", "", "", "", "", ""]   # Empty row
            ]
            
            # Write summary table
            df_summary = pd.DataFrame(summary_table)
            df_summary.to_excel(writer, sheet_name='Sheet1', index=False, header=False, startrow=0)
            
            # Write the new column headers immediately after summary table (row 8)
            pd.DataFrame([new_headers]).to_excel(writer, sheet_name='Sheet1', 
                                               index=False, header=False, startrow=8)
            
            # Write data immediately after headers (row 9)
            df_raw.to_excel(writer, sheet_name='Sheet1', index=False, header=False, startrow=9)
            
            # Get the workbook and worksheet objects for formatting
            workbook = writer.book
            worksheet = writer.sheets['Sheet1']
            
            # Create formats for the summary table
            yellow_format = workbook.add_format({
                'bg_color': '#FFFF00',
                'border': 1,
                'border_color': '#000000'
            })
            
            # Apply formatting to the summary table area (B2:E5)
            worksheet.conditional_format('B2:E5', {'type': 'no_errors', 'format': yellow_format})
            
            # Create a chart sheet using XlsxWriter
            chartsheet = workbook.add_chartsheet('Chart')
            
            # Create a line chart
            chart = workbook.add_chart({'type': 'line'})
            
            # Add voltage data series (dark blue)
            chart.add_series({
                'name': 'Clamp [V]',
                'categories': ['Sheet1', 9, 0, 9+len(df_raw)-1, 0],  # Relative Time column
                'values': ['Sheet1', 9, 3, 9+len(df_raw)-1, 3],      # Clamp [V] column
                'line': {'color': '#1f4e79', 'width': 2}             # Dark blue, thick line
            })
            
            # Add current data series (orange) on secondary axis
            chart.add_series({
                'name': 'Current [A]',
                'categories': ['Sheet1', 9, 0, 9+len(df_raw)-1, 0],  # Relative Time column
                'values': ['Sheet1', 9, 4, 9+len(df_raw)-1, 4],      # Current [A] column
                'line': {'color': '#ff8c00', 'width': 2},            # Orange, thick line
                'y2_axis': True                                       # Use secondary Y-axis
            })
            
            # Configure chart
            chart.set_title({'name': 'Clamp Voltage and Current vs Time'})
            chart.set_x_axis({'name': 'Relative Time (seconds)'})
            chart.set_y_axis({'name': 'Clamp [V]', 'min': 0, 'max': 25})
            chart.set_y2_axis({'name': 'Current [A]', 'min': 0, 'max': 450})  # Secondary axis on right
            chart.set_legend({'position': 'bottom'})
            
            # Add chart to the chart sheet (this makes it fill the entire sheet)
            chartsheet.set_chart(chart)
        
        print(f"Data copied to {output_file}")
        print(f"Added 8 empty rows at top, removed Chn 1 Events column")
        print(f"Total rows in output: {8 + 1 + len(df_raw)} (8 empty + 1 header + {len(df_raw)} data)")
        
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
