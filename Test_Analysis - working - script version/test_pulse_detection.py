#!/usr/bin/env python3
"""
Test script to verify the updated pulse detection functionality
"""

import pandas as pd
import numpy as np
import sys
import os
from pathlib import Path

# Add the backend directory to the path
backend_dir = Path(__file__).parent / "backend" / "python"
sys.path.insert(0, str(backend_dir))

from process_file import copy_raw_data

def create_test_data():
    """Create test data with multiple pulses"""
    print("Creating test data with multiple pulses...")
    
    # Create time series (10 seconds, 1000 Hz sampling)
    time = np.linspace(0, 10, 10000)
    
    # Create baseline current (small noise around 5A)
    current = np.random.normal(5, 1, len(time))
    
    # Add 5 pulses at different times
    pulse_times = [1.0, 2.5, 4.0, 6.5, 8.0]
    pulse_amplitudes = [200, 150, 300, 180, 250]
    pulse_durations = [0.2, 0.15, 0.25, 0.18, 0.22]
    
    for i, (pulse_time, amplitude, duration) in enumerate(zip(pulse_times, pulse_amplitudes, pulse_durations)):
        # Find indices for this pulse
        start_idx = int(pulse_time * 1000)  # Convert to sample index
        end_idx = int((pulse_time + duration) * 1000)
        
        # Create pulse shape (ramp up, plateau, ramp down)
        pulse_length = end_idx - start_idx
        ramp_length = pulse_length // 4
        
        # Ramp up
        current[start_idx:start_idx + ramp_length] = np.linspace(5, amplitude, ramp_length)
        # Plateau
        current[start_idx + ramp_length:end_idx - ramp_length] = amplitude
        # Ramp down
        current[end_idx - ramp_length:end_idx] = np.linspace(amplitude, 5, ramp_length)
        
        print(f"Added pulse {i+1}: {amplitude}A at {pulse_time}s for {duration}s")
    
    # Create voltage data (simple relationship to current)
    voltage = 12 + current * 0.02 + np.random.normal(0, 0.1, len(time))
    
    # Create DataFrame in the expected format
    df = pd.DataFrame({
        'Relative Time': time,
        'Date': ['01/01/2024'] * len(time),
        'Time Stamp UTC': ['12:00:00 PM'] * len(time),
        'Volt ': voltage,
        'Amp ': current
    })
    
    return df

def main():
    """Test the updated pulse detection"""
    print("=" * 60)
    print("TESTING UPDATED PULSE DETECTION")
    print("=" * 60)
    
    # Create test data
    test_df = create_test_data()
    
    # Save test data to Excel file
    test_input = "test_input.xlsx"
    test_output = "test_output.xlsx"
    
    print(f"\nSaving test data to {test_input}...")
    test_df.to_excel(test_input, index=False)
    
    # Process the test file
    print(f"\nProcessing {test_input} -> {test_output}...")
    try:
        result = copy_raw_data(test_input, test_output)
        
        if result:
            print(f"\n✅ SUCCESS: Test completed successfully!")
            print(f"Output file: {result}")
            print("\nYou can now open the output file to verify:")
            print("1. Raw Data sheet with Time and Current columns")
            print("2. Peak Current Analysis sheet with peak currents for all detected pulses")
            print("3. All Data sheet with complete dataset")
            print("4. Current vs Time Chart")
        else:
            print("❌ FAILED: Processing failed")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up test input file
        if os.path.exists(test_input):
            os.remove(test_input)
            print(f"\nCleaned up {test_input}")

if __name__ == "__main__":
    main()
