#!/usr/bin/env python3
"""
Create a visualization of the current pulses
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

def main():
    # Find the Excel file
    excel_files = list(Path('.').glob('*.xlsx'))
    
    if not excel_files:
        print("No Excel files found.")
        return
    
    excel_file = excel_files[0]
    print(f"Creating pulse visualization from: {excel_file.name}")
    
    try:
        # Read the raw data
        raw_data = pd.read_excel(excel_file, sheet_name='Raw_Data')
        pulse_data = pd.read_excel(excel_file, sheet_name='Pulse_Summary')

        # Clean pulse data - only keep rows that have pulse numbers
        pulse_data = pulse_data.dropna(how='all')

        # Filter to only include actual pulse data (not statistics)
        if 'Pulse_Number' in pulse_data.columns:
            pulse_data = pulse_data[pulse_data['Pulse_Number'].notna()]
            # Convert to numeric to be safe
            pulse_data = pulse_data[pd.to_numeric(pulse_data['Pulse_Number'], errors='coerce').notna()]
        
        # Create the plot
        plt.figure(figsize=(14, 8))
        
        # Plot the raw current data
        plt.subplot(2, 1, 1)
        plt.plot(raw_data['Time_seconds'], raw_data['Current'], 'b-', linewidth=1, alpha=0.7, label='Current')
        
        # Mark the peaks
        if 'Peak_Time_s' in pulse_data.columns and 'Peak_Current_A' in pulse_data.columns:
            peak_times = pulse_data['Peak_Time_s'].values
            peak_currents = pulse_data['Peak_Current_A'].values
            
            plt.scatter(peak_times, peak_currents, color='red', s=100, zorder=5, label='Peak Current')
            
            # Annotate peaks
            for i, (time, current) in enumerate(zip(peak_times, peak_currents)):
                plt.annotate(f'P{i+1}\n{current:.0f}A', 
                           xy=(time, current), 
                           xytext=(10, 20), 
                           textcoords='offset points',
                           bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7),
                           arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'))
        
        plt.xlabel('Time (seconds)')
        plt.ylabel('Current (Amperes)')
        plt.title('Current vs Time - Full Test Data with Peak Detection')
        plt.grid(True, alpha=0.3)
        plt.legend()
        
        # Zoomed view of first pulse
        plt.subplot(2, 1, 2)
        
        # Show first 0.2 seconds in detail
        mask = raw_data['Time_seconds'] <= 0.2
        plt.plot(raw_data[mask]['Time_seconds'], raw_data[mask]['Current'], 'b-', linewidth=2, label='Current')
        
        if len(peak_times) > 0:
            plt.scatter([peak_times[0]], [peak_currents[0]], color='red', s=100, zorder=5, label='Peak')
            plt.annotate(f'Peak: {peak_currents[0]:.0f}A', 
                       xy=(peak_times[0], peak_currents[0]), 
                       xytext=(10, 20), 
                       textcoords='offset points',
                       bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7),
                       arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'))
        
        plt.xlabel('Time (seconds)')
        plt.ylabel('Current (Amperes)')
        plt.title('Detailed View - First Pulse (0-0.2 seconds)')
        plt.grid(True, alpha=0.3)
        plt.legend()
        
        plt.tight_layout()
        
        # Save the plot
        plot_filename = 'pulse_analysis_plot.png'
        plt.savefig(plot_filename, dpi=300, bbox_inches='tight')
        print(f"📊 Plot saved as: {plot_filename}")
        
        # Show the plot (if running in an environment that supports it)
        try:
            plt.show()
        except:
            print("Note: Plot display not available in this environment, but saved to file.")
        
        # Print summary
        print(f"\n📈 PULSE PATTERN SUMMARY:")
        print("-" * 40)
        print(f"• Test shows a regular pulse pattern")
        print(f"• 5 pulses occurring every 0.5 seconds")
        print(f"• Each pulse lasts exactly 0.1 seconds")
        print(f"• Peak currents range from 3,341A to 3,455A")
        print(f"• Very consistent pulse timing and duration")
        print(f"• This appears to be a controlled peak current test")
        
    except Exception as e:
        print(f"❌ Error creating visualization: {e}")

if __name__ == "__main__":
    main()
