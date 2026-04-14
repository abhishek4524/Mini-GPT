"""
Debug script to inspect CSV structure
"""

import csv

print("Inspecting train.csv structure...\n")

with open('train.csv', 'r', encoding='utf-8', errors='ignore') as f:
    reader = csv.reader(f)
    header = next(reader)
    print(f"Header: {header}\n")
    
    # Read first 3 rows
    for i in range(3):
        row = next(reader)
        print(f"\n{'='*80}")
        print(f"Row {i+1}:")
        print(f"{'='*80}")
        
        # Print columns
        for j, col in enumerate(header):
            print(f"\n{col}:")
            value = row[j] if j < len(row) else "N/A"
            # Print only first 500 chars
            print(f"  {value[:500]}")
            if len(value) > 500:
                print(f"  ... ({len(value)} total chars)")

print("\n" + "="*80)
print("CSV inspection complete!")
