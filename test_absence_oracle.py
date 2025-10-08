"""
Test script for Oracle Absence Report fetch with date parameter
"""
import sys
sys.path.append('.')

from agents.absence_analytics.get_data import get_absence_report_data, refresh_absence_database_from_oracle
from datetime import datetime

print("="*70)
print("Testing Oracle Absence Report Fetch")
print("="*70)

# Test with specific date: 31-12-2025
test_date = "31-12-2025"  # Using DD-MM-YYYY format (Oracle expected format)

print(f"\nTest 1: Fetch report for date: {test_date}")
print("-"*70)
print("Note: Oracle expects DD-MM-YYYY format")
print()

excel_data = get_absence_report_data(DATE_OF_ABSENCE=test_date)

if excel_data:
    print(f"Success! Received {len(excel_data)} bytes of Excel data")
    
    # Save for inspection
    with open("test_absence_report.xlsx", "wb") as f:
        f.write(excel_data)
    print("Saved as test_absence_report.xlsx for inspection")
    
    print("\nTest 2: Load data to database")
    print("-"*70)
    result = refresh_absence_database_from_oracle(date_of_absence=test_date)
    print(f"\nResult: {result}")
else:
    print("Failed to fetch data from Oracle")
    print("\nTrying with DD-MM-YYYY format (31-12-2025)...")
    
    # If YYYY-MM-DD failed, the issue might be date format
    # Oracle might expect DD-MM-YYYY
    print("\nNote: You may need to check Oracle's expected date format")
    print("Common formats: YYYY-MM-DD, DD-MM-YYYY, DD-MON-YYYY")

print("\n" + "="*70)
print("Test Complete")
print("="*70)
