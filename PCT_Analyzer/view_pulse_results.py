#!/usr/bin/env python3
"""
View the pulse analysis results from the Excel file
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
    print(f"📊 Reading pulse analysis results from: {excel_file.name}")
    print("=" * 80)
    
    try:
        # Read the Pulse_Summary sheet
        pulse_df = pd.read_excel(excel_file, sheet_name='Pulse_Summary')
        
        # The sheet contains both pulse data and statistics
        # Find where statistics start (look for empty rows or specific patterns)
        stats_start_row = None
        for i, row in pulse_df.iterrows():
            if pd.isna(row.iloc[0]) or str(row.iloc[0]).startswith('Total Pulses'):
                stats_start_row = i
                break
        
        if stats_start_row is not None:
            # Split into pulse data and statistics
            pulse_data = pulse_df.iloc[:stats_start_row].copy()
            stats_data = pulse_df.iloc[stats_start_row:].copy()
        else:
            pulse_data = pulse_df.copy()
            stats_data = pd.DataFrame()
        
        # Display pulse summary
        print("🔋 INDIVIDUAL PULSE ANALYSIS")
        print("-" * 50)
        
        if not pulse_data.empty:
            # Clean up the pulse data (remove any NaN rows)
            pulse_data = pulse_data.dropna(how='all')
            
            print(pulse_data.to_string(index=False))
            
            print(f"\n📈 PULSE PEAKS SUMMARY:")
            print("-" * 30)
            for _, pulse in pulse_data.iterrows():
                if 'Pulse_Number' in pulse and 'Peak_Current_A' in pulse:
                    print(f"Pulse {int(pulse['Pulse_Number'])}: {pulse['Peak_Current_A']:.2f} A at {pulse['Peak_Time_s']:.3f}s")
        
        # Display statistics if available
        if not stats_data.empty:
            print(f"\n📊 OVERALL STATISTICS")
            print("-" * 30)
            
            # Clean up stats data
            stats_data = stats_data.dropna(how='all')
            
            for _, stat in stats_data.iterrows():
                if len(stat) >= 2 and pd.notna(stat.iloc[0]) and pd.notna(stat.iloc[1]):
                    stat_name = str(stat.iloc[0])
                    stat_value = stat.iloc[1]
                    unit = stat.iloc[2] if len(stat) > 2 and pd.notna(stat.iloc[2]) else ""
                    print(f"{stat_name}: {stat_value} {unit}")
        
        # Additional analysis
        print(f"\n🎯 KEY FINDINGS:")
        print("-" * 20)
        
        if not pulse_data.empty and 'Peak_Current_A' in pulse_data.columns:
            peak_currents = pulse_data['Peak_Current_A'].values
            print(f"• Total pulses detected: {len(pulse_data)}")
            print(f"• Highest peak current: {max(peak_currents):.2f} A")
            print(f"• Lowest peak current: {min(peak_currents):.2f} A")
            print(f"• Average peak current: {sum(peak_currents)/len(peak_currents):.2f} A")
            print(f"• Peak current variation: {max(peak_currents) - min(peak_currents):.2f} A")
            
            if 'Duration_s' in pulse_data.columns:
                durations = pulse_data['Duration_s'].values
                print(f"• Pulse duration: {durations[0]:.3f} s (consistent across all pulses)")
                
            if 'Start_Time_s' in pulse_data.columns and 'End_Time_s' in pulse_data.columns:
                start_times = pulse_data['Start_Time_s'].values
                end_times = pulse_data['End_Time_s'].values
                intervals = []
                for i in range(1, len(start_times)):
                    interval = start_times[i] - end_times[i-1]
                    intervals.append(interval)
                
                if intervals:
                    avg_interval = sum(intervals) / len(intervals)
                    print(f"• Average interval between pulses: {avg_interval:.3f} s")
        
        print(f"\n✅ Analysis complete! Check the Excel file for detailed data.")
        
    except Exception as e:
        print(f"❌ Error reading pulse analysis results: {e}")
        print("Make sure the pulse analysis has been run and the Excel file contains a 'Pulse_Summary' sheet.")

if __name__ == "__main__":
    main()
