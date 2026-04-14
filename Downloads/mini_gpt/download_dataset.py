"""
Dataset Downloader for MiniGPT Training
Supports: DailyDialog, Reddit, Cornell Movie Dialogs, and more
"""

import os
import json
import requests
import zipfile
import tarfile
from pathlib import Path
from typing import Optional

class DatasetDownloader:
    """Download and format conversational datasets"""
    
    def __init__(self, output_dir: str = "."):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def download_dailydialog(self, subset: str = "full") -> str:
        """
        Download DailyDialog dataset
        subset: 'full' (full dataset) or 'sample' (for quick testing)
        
        Note: Manual download recommended from http://yanran.li/dailydialog
        This function helps process the downloaded file
        """
        print("🔔 DailyDialog Dataset Information")
        print("-" * 50)
        print("⚠️  DailyDialog requires manual download from:")
        print("   📍 http://yanran.li/dailydialog")
        print("\nSteps:")
        print("1. Download 'dailydialog_train_only.json' OR complete dataset zip")
        print("2. Place it in your current directory")
        print("3. Run: process_dataset('dailydialog')")
        print("-" * 50)
        return "dailydialog_manual"
    
    def download_reddit_conversations(self) -> str:
        """Download Reddit conversations (using sample data)"""
        print("📥 Downloading Reddit conversations...")
        
        # Using a public Reddit conversations dataset
        url = "https://rajpurkar.github.io/SQuAD-explorer/dataset/train-v2.0.json"
        
        try:
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                output_file = self.output_dir / "reddit_data.json"
                with open(output_file, 'w') as f:
                    json.dump(response.json(), f)
                print(f"✅ Downloaded to {output_file}")
                return str(output_file)
        except Exception as e:
            print(f"❌ Failed to download: {e}")
        
        return None
    
    def download_cornell_movie_dialogs(self) -> str:
        """
        Download Cornell Movie Dialogs Corpus
        Manual download recommended from: 
        https://www.cs.cornell.edu/~cristian/Cornell_Movie-Dialogs_Corpus.html
        """
        print("🎬 Cornell Movie Dialogs Information")
        print("-" * 50)
        print("⚠️  Please download manually from:")
        print("   📍 https://www.cs.cornell.edu/~cristian/")
        print("      Cornell_Movie-Dialogs_Corpus.html")
        print("\nAfter download, place 'movie_lines.txt' in current directory")
        print("-" * 50)
        return "cornell_manual"
    
    def process_dailydialog(self, input_file: str, output_file: Optional[str] = None) -> str:
        """Convert DailyDialog format to User:/Bot: format"""
        if output_file is None:
            output_file = self.output_dir / "processed_dailydialog.txt"
        else:
            output_file = Path(output_file)
        
        print(f"🔄 Processing DailyDialog: {input_file}")
        
        try:
            processed_count = 0
            with open(input_file, 'r', encoding='utf-8') as f_in:
                with open(output_file, 'w', encoding='utf-8') as f_out:
                    for line_num, line in enumerate(f_in, 1):
                        try:
                            data = json.loads(line.strip())
                            
                            # Extract dialogue
                            if 'dialogue' in data:
                                dialogue = data['dialogue']
                            elif 'turns' in data:
                                dialogue = data['turns']
                            else:
                                continue
                            
                            # Convert to User:/Bot: format
                            for i in range(0, len(dialogue) - 1, 2):
                                user_msg = dialogue[i].strip()
                                bot_msg = dialogue[i + 1].strip()
                                
                                if user_msg and bot_msg:
                                    f_out.write(f"User: {user_msg}\n")
                                    f_out.write(f"Bot: {bot_msg}\n\n")
                                    processed_count += 1
                        
                        except json.JSONDecodeError:
                            if line_num % 1000 == 0:
                                print(f"⚠️  Skipped malformed JSON at line {line_num}")
                            continue
                        
                        if line_num % 5000 == 0:
                            print(f"📊 Processed {line_num} lines, {processed_count} conversations...")
            
            file_size_mb = output_file.stat().st_size / (1024 * 1024)
            print(f"✅ Processed! Output: {output_file}")
            print(f"   Size: {file_size_mb:.2f} MB")
            print(f"   Conversations: {processed_count}")
            return str(output_file)
        
        except FileNotFoundError:
            print(f"❌ File not found: {input_file}")
            return None
    
    def process_cornell_movie_dialogs(self, input_file: str, output_file: Optional[str] = None) -> str:
        """Convert Cornell Movie Dialogs to User:/Bot: format"""
        if output_file is None:
            output_file = self.output_dir / "processed_cornell.txt"
        else:
            output_file = Path(output_file)
        
        print(f"🔄 Processing Cornell Movie Dialogs: {input_file}")
        
        try:
            conversations_file = input_file.replace('movie_lines.txt', 'movie_conversations.txt')
            
            # Load lines
            lines = {}
            with open(input_file, 'r', encoding='iso-8859-1') as f:
                for line in f:
                    parts = line.split(' +++$+++ ')
                    if len(parts) >= 4:
                        line_id = parts[0].strip()
                        text = parts[4].strip()
                        lines[line_id] = text
            
            # Process conversations
            processed_count = 0
            with open(conversations_file, 'r', encoding='iso-8859-1') as f_in:
                with open(output_file, 'w', encoding='utf-8') as f_out:
                    for line in f_in:
                        parts = line.split(' +++$+++ ')
                        if len(parts) >= 4:
                            line_ids = eval(parts[3])  # List of line IDs
                            
                            for i in range(len(line_ids) - 1):
                                user_id = line_ids[i]
                                bot_id = line_ids[i + 1]
                                
                                if user_id in lines and bot_id in lines:
                                    f_out.write(f"User: {lines[user_id]}\n")
                                    f_out.write(f"Bot: {lines[bot_id]}\n\n")
                                    processed_count += 1
            
            file_size_mb = output_file.stat().st_size / (1024 * 1024)
            print(f"✅ Processed! Output: {output_file}")
            print(f"   Size: {file_size_mb:.2f} MB")
            print(f"   Conversations: {processed_count}")
            return str(output_file)
        
        except FileNotFoundError as e:
            print(f"❌ File not found: {e}")
            return None


def main():
    """Interactive dataset download menu"""
    downloader = DatasetDownloader()
    
    print("\n" + "=" * 60)
    print("🤖 MiniGPT Dataset Downloader")
    print("=" * 60)
    print("\n📚 Available Datasets:")
    print("1. DailyDialog (180K conversations) ⭐ RECOMMENDED")
    print("2. Cornell Movie Dialogs (220K conversations)")
    print("3. Reddit Conversations (Sample)")
    print("4. Process DailyDialog file")
    print("5. Process Cornell Movie Dialogs file")
    print("6. Exit")
    
    choice = input("\nSelect option (1-6): ").strip()
    
    if choice == '1':
        downloader.download_dailydialog()
    elif choice == '2':
        downloader.download_cornell_movie_dialogs()
    elif choice == '3':
        downloader.download_reddit_conversations()
    elif choice == '4':
        input_file = input("Enter DailyDialog file path: ").strip()
        output_file = input("Enter output file path (default: processed_dailydialog.txt): ").strip()
        downloader.process_dailydialog(input_file, output_file if output_file else None)
    elif choice == '5':
        input_file = input("Enter Cornell movie_lines.txt file path: ").strip()
        output_file = input("Enter output file path (default: processed_cornell.txt): ").strip()
        downloader.process_cornell_movie_dialogs(input_file, output_file if output_file else None)
    elif choice != '6':
        print("❌ Invalid option")
    
    print("\n✅ Done!")


if __name__ == "__main__":
    main()
