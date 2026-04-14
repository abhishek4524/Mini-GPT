"""
Advanced CSV to Text Converter for Kaggle Dialogue Datasets
Handles complex formats with comments and quoted lists
"""

import csv
import ast
import re
import json
from pathlib import Path
from typing import List, Tuple

class AdvancedCSVConverter:
    """Advanced converter for dialogue datasets"""
    
    def __init__(self):
        self.stats = {
            'total_rows': 0,
            'successful': 0,
            'failed': 0,
            'conversations': 0,
        }
    
    def extract_dialog_from_string(self, dialog_str) -> List[str]:
        """
        Extract dialogue list from string representation
        Handles formats like:
        "['Hello', 'Hi', /* Lines omitted */ 'Bye']"
        "['Hello' 'Hi' 'Bye']" (without commas)
        """
        if not dialog_str or pd.isna(dialog_str):
            return []
        
        dialog_str = str(dialog_str).strip()
        
        # Remove comments
        dialog_str = re.sub(r'/\*.*?\*/', '', dialog_str)
        
        # Try 1: ast.literal_eval
        try:
            result = ast.literal_eval(dialog_str)
            if isinstance(result, list):
                return [str(item).strip() for item in result if str(item).strip()]
        except:
            pass
        
        # Try 2: JSON parser
        try:
            result = json.loads(dialog_str)
            if isinstance(result, list):
                return [str(item).strip() for item in result if str(item).strip()]
        except:
            pass
        
        # Try 3: Manual parsing - extract quotes
        try:
            # Pattern: 'text' or "text"
            pattern = r"['\"]([^'\"]*)['\"]"
            matches = re.findall(pattern, dialog_str)
            if matches:
                return [m.strip() for m in matches if m.strip()]
        except:
            pass
        
        return []
    
    def convert_csv_direct(self, csv_file, output_file=None):
        """
        Convert CSV directly using raw parsing
        More reliable than pandas for complex formats
        """
        if output_file is None:
            base_name = Path(csv_file).stem
            output_file = f"converted_{base_name}.txt"
        
        print(f"\n{'='*60}")
        print(f"🔄 Converting CSV (Advanced): {csv_file}")
        print(f"{'='*60}")
        
        try:
            conversations = []
            self.stats = {
                'total_rows': 0,
                'successful': 0,
                'failed': 0,
                'conversations': 0,
            }
            
            with open(csv_file, 'r', encoding='utf-8', errors='ignore') as f:
                reader = csv.reader(f)
                header = next(reader)  # Skip header
                
                print(f"📖 Header: {header}\n")
                
                for row_idx, row in enumerate(reader, 1):
                    if not row or len(row) == 0:
                        continue
                    
                    self.stats['total_rows'] += 1
                    
                    # Assume first column is dialog
                    dialog_str = row[0]
                    
                    # Extract dialogue list
                    dialog_list = self.extract_dialog_from_string(dialog_str)
                    
                    if len(dialog_list) < 2:
                        self.stats['failed'] += 1
                        continue
                    
                    # Convert alternating messages to User:/Bot: format
                    for i in range(0, len(dialog_list) - 1, 2):
                        user_msg = self.clean_message(dialog_list[i])
                        bot_msg = self.clean_message(dialog_list[i + 1])
                        
                        if user_msg and bot_msg:
                            conversations.append((user_msg, bot_msg))
                            self.stats['conversations'] += 1
                    
                    self.stats['successful'] += 1
                    
                    if row_idx % 500 == 0:
                        print(f"   📊 Processed {row_idx} rows, "
                              f"{self.stats['conversations']} conversations...")
            
            # Write output
            print(f"\n💾 Writing to file: {output_file}")
            with open(output_file, 'w', encoding='utf-8') as f:
                for user_msg, bot_msg in conversations:
                    f.write(f"User: {user_msg}\n")
                    f.write(f"Bot: {bot_msg}\n\n")
            
            self._print_stats(output_file)
            return output_file
        
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def clean_message(self, text: str) -> str:
        """Clean message text"""
        text = str(text).strip()
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Remove newlines
        text = text.replace('\n', ' ').replace('\r', '')
        
        # Fix common patterns
        text = text.replace(" ' ", "'")
        text = text.replace("' ", "'")
        text = text.replace(" '", "'")
        
        # Remove excessive punctuation
        text = re.sub(r'([!?.])\1{2,}', r'\1\1', text)
        
        return text.strip()
    
    def _print_stats(self, output_file):
        """Print statistics"""
        file_size_mb = Path(output_file).stat().st_size / (1024 * 1024)
        
        print(f"\n{'='*60}")
        print(f"✅ Conversion Complete!")
        print(f"{'='*60}")
        print(f"📊 Statistics:")
        print(f"   Total rows             : {self.stats['total_rows']:,}")
        print(f"   Successful rows        : {self.stats['successful']:,}")
        print(f"   Failed rows            : {self.stats['failed']:,}")
        print(f"   Total conversations    : {self.stats['conversations']:,}")
        print(f"   Output file size       : {file_size_mb:.2f} MB")
        print(f"   Output file            : {output_file}")
        print(f"{'='*60}\n")
    
    def combine_files(self, input_files: List[str], output_file: str):
        """Combine multiple text files"""
        print(f"\n{'='*60}")
        print(f"🔗 Combining files...")
        print(f"{'='*60}")
        
        total_convs = 0
        total_size = 0
        
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
                total_size += file_size
                print(f"   ✅ {input_file} ({file_size:.2f} MB, {convs} convs)")
        
        output_size = Path(output_file).stat().st_size / (1024 * 1024)
        print(f"\n✅ Combined file:")
        print(f"   File: {output_file}")
        print(f"   Total size: {output_size:.2f} MB")
        print(f"   Total conversations: {total_convs:,}")


def main():
    """Advanced menu"""
    print("\n" + "=" * 60)
    print("📊 Advanced CSV to Text Converter for MiniGPT")
    print("=" * 60)
    print("\n🎯 Options:")
    print("1. Convert single CSV file (Advanced)")
    print("2. Convert multiple CSV files and combine")
    print("3. Exit")
    
    choice = input("\nSelect option (1-3): ").strip()
    
    # Import pandas only here
    global pd
    import pandas as pd
    
    converter = AdvancedCSVConverter()
    
    if choice == '1':
        csv_file = input("Enter CSV file path: ").strip()
        output_file = input("Output file path (press Enter for default): ").strip()
        output_file = output_file if output_file else None
        converter.convert_csv_direct(csv_file, output_file)
    
    elif choice == '2':
        print("\nEnter CSV file paths (one per line, empty line to finish):")
        csv_files = []
        while True:
            file_path = input().strip()
            if not file_path:
                break
            csv_files.append(file_path)
        
        if csv_files:
            # Convert each file
            converted_files = []
            for csv_file in csv_files:
                output = converter.convert_csv_direct(csv_file)
                if output:
                    converted_files.append(output)
            
            # Combine
            if len(converted_files) > 1:
                output_combined = input("\nCombined output file (press Enter for 'combined_data.txt'): ").strip()
                output_combined = output_combined if output_combined else "combined_data.txt"
                converter.combine_files(converted_files, output_combined)
    
    elif choice != '3':
        print("❌ Invalid option")
    
    print("✅ Done!")


if __name__ == "__main__":
    main()
