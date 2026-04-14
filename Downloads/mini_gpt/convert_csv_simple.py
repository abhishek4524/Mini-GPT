"""
Simple and Direct CSV to Text Converter
Uses pandas to read CSV properly, then converts to User:/Bot: format
"""

import pandas as pd
import ast
from pathlib import Path

def convert_csv_simple(csv_file, output_file=None):
    """Convert CSV to User:/Bot: text format - Simple approach"""
    
    if output_file is None:
        base_name = Path(csv_file).stem
        output_file = f"converted_{base_name}.txt"
    
    print(f"\n{'='*70}")
    print(f"🔄 Converting: {csv_file}")
    print(f"{'='*70}")
    
    try:
        # Read CSV with pandas
        print("📖 Reading CSV...")
        df = pd.read_csv(csv_file)
        print(f"   Rows: {len(df)}")
        print(f"   Columns: {list(df.columns)}\n")
        
        conversations = []
        failed = 0
        
        # Process each row
        for idx, row in df.iterrows():
            dialog = row['dialog']
            
            # Try to convert dialog to list
            if isinstance(dialog, str):
                try:
                    # Multi-line string -> convert to list
                    lines = [line.strip() for line in dialog.split('\n') if line.strip()]
                    
                    # Try to parse as Python list
                    try:
                        dialog_list = ast.literal_eval(str(lines).replace('\n', ''))
                    except:
                        dialog_list = lines
                    
                    # Fallback: split by quotes if above didn't work
                    if not isinstance(dialog_list, list) or len(dialog_list) < 2:
                        import re
                        # Extract all quoted strings
                        pattern = r"['\"]([^'\"]*)['\"]"
                        matches = re.findall(pattern, dialog)
                        if matches:
                            dialog_list = [m.strip() for m in matches if m.strip()]
                    
                except:
                    dialog_list = None
            else:
                dialog_list = dialog
            
            # Convert to list if needed
            if not isinstance(dialog_list, list):
                try:
                    dialog_list = ast.literal_eval(str(dialog_list))
                except:
                    dialog_list = None
            
            # Process conversation
            if isinstance(dialog_list, list) and len(dialog_list) >= 2:
                for i in range(0, len(dialog_list) - 1, 2):
                    user_msg = str(dialog_list[i]).strip()
                    bot_msg = str(dialog_list[i+1]).strip()
                    
                    # Clean messages
                    user_msg = ' '.join(user_msg.split())
                    bot_msg = ' '.join(bot_msg.split())
                    
                    if user_msg and bot_msg:
                        conversations.append((user_msg, bot_msg))
            else:
                failed += 1
            
            if (idx + 1) % 1000 == 0:
                print(f"   ✓ Processed {idx + 1:,} rows, {len(conversations):,} conversations...")
        
        # Write output
        print(f"\n💾 Writing to: {output_file}")
        with open(output_file, 'w', encoding='utf-8') as f:
            for user_msg, bot_msg in conversations:
                f.write(f"User: {user_msg}\n")
                f.write(f"Bot: {bot_msg}\n\n")
        
        # Stats
        file_size_mb = Path(output_file).stat().st_size / (1024 * 1024)
        
        print(f"\n{'='*70}")
        print(f"✅ Done!")
        print(f"{'='*70}")
        print(f"📊 Results:")
        print(f"   Total rows        : {len(df):,}")
        print(f"   Conversations     : {len(conversations):,}")
        print(f"   Failed rows       : {failed:,}")
        print(f"   Output size       : {file_size_mb:.2f} MB")
        print(f"   Output file       : {output_file}")
        print(f"{'='*70}\n")
        
        return output_file
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


def combine_files(input_files, output_file):
    """Combine multiple text files"""
    print(f"\n{'='*70}")
    print(f"🔗 Combining files...")
    print(f"{'='*70}\n")
    
    total_convs = 0
    
    with open(output_file, 'w', encoding='utf-8') as f_out:
        for input_file in input_files:
            if not Path(input_file).exists():
                print(f"⚠️  File not found: {input_file}")
                continue
            
            with open(input_file, 'r', encoding='utf-8') as f_in:
                content = f_in.read()
                f_out.write(content)
            
            # Count conversations
            with open(input_file, 'r', encoding='utf-8') as f_in:
                lines = f_in.readlines()
                convs = len([l for l in lines if l.strip().startswith('User:')])
                total_convs += convs
            
            file_size = Path(input_file).stat().st_size / (1024 * 1024)
            print(f"   ✅ {Path(input_file).name:<50} {file_size:>8.2f} MB ({convs:>6,} convs)")
    
    output_size = Path(output_file).stat().st_size / (1024 * 1024)
    
    print(f"\n{'='*70}")
    print(f"✅ Combined!")
    print(f"{'='*70}")
    print(f"   File               : {output_file}")
    print(f"   Total size         : {output_size:.2f} MB")
    print(f"   Total conversations: {total_convs:,}")
    print(f"{'='*70}\n")


def main():
    print("\n" + "="*70)
    print("📊 Simple CSV to Text Converter for MiniGPT")
    print("="*70)
    print("\n🎯 Options:")
    print("1. Convert single CSV")
    print("2. Convert multiple CSVs and combine")
    print("3. Exit")
    
    choice = input("\nSelect (1-3): ").strip()
    
    if choice == '1':
        csv_file = input("CSV file: ").strip()
        output_file = input("Output file (Enter for default): ").strip() or None
        convert_csv_simple(csv_file, output_file)
    
    elif choice == '2':
        print("\nEnter CSV files (one per line, empty to finish):")
        files = []
        while True:
            f = input().strip()
            if not f:
                break
            files.append(f)
        
        if files:
            # Convert each
            converted = []
            for f in files:
                output = convert_csv_simple(f)
                if output:
                    converted.append(output)
            
            # Combine
            if len(converted) > 1:
                output_combined = input("\nCombined file (Enter for 'combined_data.txt'): ").strip() or "combined_data.txt"
                combine_files(converted, output_combined)


if __name__ == "__main__":
    main()
