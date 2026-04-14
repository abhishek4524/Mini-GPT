"""
CSV Dataset to Text Converter for MiniGPT
Converts Kaggle dialogue datasets (CSV format) to User:/Bot: format
"""

import pandas as pd
import ast
import os
from pathlib import Path

class CSVToTextConverter:
    """Convert CSV dialogue datasets to User:/Bot: format"""
    
    def __init__(self):
        self.stats = {
            'total_rows': 0,
            'successful_conversions': 0,
            'failed_conversions': 0,
            'total_conversations': 0,
        }
    
    def parse_dialog_column(self, dialog_str):
        """
        Parse the dialog column which may be:
        - A Python list (string representation) with 'Lines X-Y omitted' comments
        - A JSON array
        - Plain text
        """
        if pd.isna(dialog_str):
            return []
        
        dialog_str = str(dialog_str).strip()
        
        # Remove comments like "/* Lines 3-6 omitted */" 
        import re
        dialog_str_cleaned = re.sub(r'/\*.*?\*/', '', dialog_str)
        
        # Try to parse as Python list
        try:
            dialog_list = ast.literal_eval(dialog_str_cleaned)
            if isinstance(dialog_list, list):
                # Filter out empty strings
                return [item for item in dialog_list if item and str(item).strip()]
        except (ValueError, SyntaxError) as e:
            pass
        
        # Try to parse as JSON
        try:
            import json
            dialog_list = json.loads(dialog_str_cleaned)
            if isinstance(dialog_list, list):
                return [item for item in dialog_list if item and str(item).strip()]
        except:
            pass
        
        return []
    
    def convert_csv_to_text(self, csv_file, output_file=None):
        """
        Convert CSV file to User:/Bot: text format
        
        Expected CSV columns:
        - 'dialog' or 'dialogue': contains list of dialogue turns
        - Other columns: optional (act, emotion, etc.)
        """
        
        if output_file is None:
            base_name = Path(csv_file).stem
            output_file = f"converted_{base_name}.txt"
        
        print(f"\n{'='*60}")
        print(f"🔄 Converting CSV: {csv_file}")
        print(f"{'='*60}")
        
        try:
            # Read CSV
            print(f"📖 Reading CSV file...")
            df = pd.read_csv(csv_file)
            print(f"   Rows found: {len(df)}")
            print(f"   Columns: {list(df.columns)}")
            
            # Find dialog column
            dialog_col = None
            for col in ['dialog', 'dialogue', 'Dialog', 'Dialogue']:
                if col in df.columns:
                    dialog_col = col
                    break
            
            if dialog_col is None:
                print(f"❌ Error: Could not find dialog/dialogue column")
                print(f"   Available columns: {list(df.columns)}")
                return None
            
            print(f"   Using column: '{dialog_col}'\n")
            
            # Reset stats
            self.stats = {
                'total_rows': len(df),
                'successful_conversions': 0,
                'failed_conversions': 0,
                'total_conversations': 0,
            }
            
            # Convert to User:/Bot: format
            conversations = []
            
            for idx, row in df.iterrows():
                dialog_list = self.parse_dialog_column(row[dialog_col])
                
                if not dialog_list or len(dialog_list) < 2:
                    self.stats['failed_conversions'] += 1
                    continue
                
                # Convert alternating user/bot messages
                for i in range(0, len(dialog_list) - 1, 2):
                    user_msg = str(dialog_list[i]).strip()
                    bot_msg = str(dialog_list[i + 1]).strip()
                    
                    # Clean messages
                    user_msg = self.clean_message(user_msg)
                    bot_msg = self.clean_message(bot_msg)
                    
                    if user_msg and bot_msg:
                        conversations.append((user_msg, bot_msg))
                        self.stats['total_conversations'] += 1
                
                self.stats['successful_conversions'] += 1
                
                if (idx + 1) % 100 == 0:
                    print(f"   📊 Processed {idx + 1}/{len(df)} rows, "
                          f"{self.stats['total_conversations']} conversations extracted...")
            
            # Write to file
            print(f"\n💾 Writing to file: {output_file}")
            with open(output_file, 'w', encoding='utf-8') as f:
                for user_msg, bot_msg in conversations:
                    f.write(f"User: {user_msg}\n")
                    f.write(f"Bot: {bot_msg}\n\n")
            
            # Print statistics
            self._print_stats(output_file)
            
            return output_file
        
        except Exception as e:
            print(f"❌ Error: {e}")
            return None
    
    def clean_message(self, text):
        """Clean and normalize message text"""
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Remove special formatting
        text = text.replace('\n', ' ')
        text = text.replace('\r', '')
        
        # Remove excessive punctuation
        import re
        text = re.sub(r'([!?.])\1{2,}', r'\1\1', text)
        
        return text.strip()
    
    def _print_stats(self, output_file):
        """Print conversion statistics"""
        file_size_mb = Path(output_file).stat().st_size / (1024 * 1024)
        
        print(f"\n{'='*60}")
        print(f"✅ Conversion Complete!")
        print(f"{'='*60}")
        print(f"📊 Statistics:")
        print(f"   Total rows in CSV          : {self.stats['total_rows']:,}")
        print(f"   Successful conversions     : {self.stats['successful_conversions']:,}")
        print(f"   Failed conversions         : {self.stats['failed_conversions']:,}")
        print(f"   Total conversations        : {self.stats['total_conversations']:,}")
        print(f"   Output file size           : {file_size_mb:.2f} MB")
        print(f"   Output file                : {output_file}")
        print(f"{'='*60}\n")
    
    def convert_multiple_csv(self, csv_files, output_combined=None):
        """
        Convert multiple CSV files and optionally combine them
        
        csv_files: list of CSV file paths
        output_combined: if provided, combines all converted files into one
        """
        
        all_conversations = []
        converted_files = []
        
        for csv_file in csv_files:
            if not os.path.exists(csv_file):
                print(f"⚠️  File not found: {csv_file}")
                continue
            
            # Convert individual file
            output_file = self.convert_csv_to_text(csv_file)
            if output_file:
                converted_files.append(output_file)
        
        # Combine if requested
        if output_combined and len(converted_files) > 1:
            print(f"\n{'='*60}")
            print(f"🔗 Combining converted files...")
            print(f"{'='*60}")
            
            total_convs = 0
            with open(output_combined, 'w', encoding='utf-8') as f_out:
                for conv_file in converted_files:
                    with open(conv_file, 'r', encoding='utf-8') as f_in:
                        content = f_in.read()
                        f_out.write(content)
                    
                    # Count conversations (each has 2 lines)
                    with open(conv_file, 'r', encoding='utf-8') as f_in:
                        lines = f_in.readlines()
                        convs = len([l for l in lines if l.strip().startswith('User:')]) 
                        total_convs += convs
            
            file_size_mb = Path(output_combined).stat().st_size / (1024 * 1024)
            print(f"✅ Combined file created!")
            print(f"   File: {output_combined}")
            print(f"   Size: {file_size_mb:.2f} MB")
            print(f"   Conversations: {total_convs:,}")
            
            return output_combined
        
        return converted_files


def main():
    """Interactive menu"""
    print("\n" + "=" * 60)
    print("📊 CSV to Text Converter for MiniGPT")
    print("=" * 60)
    print("\n🎯 Options:")
    print("1. Convert single CSV file")
    print("2. Convert multiple CSV files and combine")
    print("3. Exit")
    
    choice = input("\nSelect option (1-3): ").strip()
    
    converter = CSVToTextConverter()
    
    if choice == '1':
        csv_file = input("Enter CSV file path: ").strip()
        output_file = input("Output file path (press Enter for default): ").strip()
        output_file = output_file if output_file else None
        converter.convert_csv_to_text(csv_file, output_file)
    
    elif choice == '2':
        print("\nEnter CSV file paths (one per line, empty line to finish):")
        csv_files = []
        while True:
            file_path = input().strip()
            if not file_path:
                break
            csv_files.append(file_path)
        
        if csv_files:
            output_combined = input("Combined output file path (press Enter for 'combined_data.txt'): ").strip()
            output_combined = output_combined if output_combined else "combined_data.txt"
            converter.convert_multiple_csv(csv_files, output_combined)
    
    elif choice != '3':
        print("❌ Invalid option")
    
    print("✅ Done!")


if __name__ == "__main__":
    main()
