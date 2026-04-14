"""
Data Preprocessing Pipeline for MiniGPT
Clean, normalize, and augment training data
"""

import re
import random
from pathlib import Path
from collections import Counter
from typing import List, Tuple
import json


class DataPreprocessor:
    """Clean and normalize conversational data"""
    
    def __init__(self, min_msg_len: int = 2, max_msg_len: int = 500):
        self.min_msg_len = min_msg_len
        self.max_msg_len = max_msg_len
        self.stats = {
            'total_conversations': 0,
            'removed_short': 0,
            'removed_long': 0,
            'removed_empty': 0,
            'removed_duplicates': 0,
            'final_conversations': 0,
        }
    
    def clean_message(self, text: str) -> str:
        """Clean individual message"""
        # Remove excess whitespace
        text = ' '.join(text.split())
        
        # Fix common encoding issues
        text = text.replace('\u00a0', ' ')  # Non-breaking space
        text = text.replace('\u200b', '')   # Zero-width space
        
        # Remove excessive punctuation
        text = re.sub(r'([!?.])\1{2,}', r'\1\1', text)  # ... -> ..
        
        # Normalize quotes
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace(''', "'").replace(''', "'")
        
        return text.strip()
    
    def is_valid_message(self, text: str) -> bool:
        """Check if message meets quality criteria"""
        if not text:
            self.stats['removed_empty'] += 1
            return False
        
        if len(text) < self.min_msg_len:
            self.stats['removed_short'] += 1
            return False
        
        if len(text) > self.max_msg_len:
            self.stats['removed_long'] += 1
            return False
        
        # Remove messages with too many special characters
        special_chars = len(re.findall(r'[^a-zA-Z0-9\s\.\,\!\?\'\"\-]', text))
        if special_chars / len(text) > 0.3:
            return False
        
        return True
    
    def process_user_bot_format(self, input_file: str, output_file: str, remove_duplicates: bool = True) -> str:
        """Process data in 'User: ... Bot: ...' format"""
        
        print(f"🔄 Processing: {input_file}")
        
        conversations = []
        seen_pairs = set() if remove_duplicates else None
        
        try:
            with open(input_file, 'r', encoding='utf-8', errors='ignore') as f:
                current_user = None
                
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    
                    if line.startswith('User:'):
                        current_user = self.clean_message(line[5:].strip())
                        
                    elif line.startswith('Bot:') and current_user:
                        bot_msg = self.clean_message(line[4:].strip())
                        
                        # Validate pair
                        if self.is_valid_message(current_user) and self.is_valid_message(bot_msg):
                            pair = (current_user, bot_msg)
                            
                            # Check for duplicates
                            if remove_duplicates:
                                if pair not in seen_pairs:
                                    conversations.append(pair)
                                    seen_pairs.add(pair)
                                else:
                                    self.stats['removed_duplicates'] += 1
                            else:
                                conversations.append(pair)
                        
                        current_user = None
                    
                    self.stats['total_conversations'] = len(conversations)
                    
                    if line_num % 10000 == 0:
                        print(f"   📊 Processed {line_num} lines, {len(conversations)} valid conversations...")
            
            # Write cleaned data
            with open(output_file, 'w', encoding='utf-8') as f:
                for user_msg, bot_msg in conversations:
                    f.write(f"User: {user_msg}\n")
                    f.write(f"Bot: {bot_msg}\n\n")
            
            self.stats['final_conversations'] = len(conversations)
            
            print(f"\n✅ Processing Complete!")
            self._print_stats()
            
            file_size_mb = Path(output_file).stat().st_size / (1024 * 1024)
            print(f"\n📁 Output: {output_file} ({file_size_mb:.2f} MB)")
            
            return output_file
        
        except FileNotFoundError:
            print(f"❌ File not found: {input_file}")
            return None
    
    def balance_dataset(self, input_file: str, output_file: str, sample_size: int = 50000) -> str:
        """Balance dataset by topic/keyword diversity"""
        
        print(f"⚖️  Balancing dataset (max {sample_size} samples)...")
        
        conversations = []
        token_freq = Counter()
        
        with open(input_file, 'r', encoding='utf-8', errors='ignore') as f:
            current_user = None
            for line in f:
                line = line.strip()
                if line.startswith('User:'):
                    current_user = line[5:].strip()
                elif line.startswith('Bot:') and current_user:
                    bot_msg = line[4:].strip()
                    conversations.append((current_user, bot_msg))
                    
                    # Track token frequency
                    for token in (current_user + bot_msg).lower().split():
                        token_freq[token] += 1
        
        # Random sampling with seed for reproducibility
        random.seed(42)
        sampled = random.sample(conversations, min(sample_size, len(conversations)))
        sampled.sort(key=lambda x: len(x[0]) + len(x[1]))  # Sort by length for variety
        
        with open(output_file, 'w', encoding='utf-8') as f:
            for user_msg, bot_msg in sampled:
                f.write(f"User: {user_msg}\n")
                f.write(f"Bot: {bot_msg}\n\n")
        
        print(f"✅ Sampled {len(sampled)} conversations")
        print(f"📁 Output: {output_file}")
        
        return output_file
    
    def augment_data(self, input_file: str, output_file: str, multiplier: int = 2) -> str:
        """Simple data augmentation through paraphrasing variations"""
        
        print(f"🔀 Augmenting data (multiplier: {multiplier}x)...")
        
        augmentations = {
            "hello": ["hi", "hey", "heya", "greetings"],
            "thanks": ["thank you", "thankyou", "thanks a lot", "appreciate it"],
            "what's": ["what is", "whats"],
            "don't": ["do not", "dont"],
            "can't": ["cannot", "cant"],
            "won't": ["will not", "wont"],
            "how are you": ["how are you doing", "how you doing", "how ya doing"],
        }
        
        conversations = []
        with open(input_file, 'r', encoding='utf-8', errors='ignore') as f:
            current_user = None
            for line in f:
                line = line.strip()
                if line.startswith('User:'):
                    current_user = line[5:].strip()
                elif line.startswith('Bot:') and current_user:
                    bot_msg = line[4:].strip()
                    conversations.append((current_user, bot_msg))
        
        augmented = conversations.copy()
        
        for user_msg, bot_msg in conversations[:int(len(conversations) / multiplier)]:
            for original, variations in augmentations.items():
                for variation in variations:
                    augmented_user = user_msg.lower().replace(original.lower(), variation)
                    if augmented_user != user_msg:
                        augmented.append((augmented_user, bot_msg))
        
        with open(output_file, 'w', encoding='utf-8') as f:
            for user_msg, bot_msg in augmented:
                f.write(f"User: {user_msg}\n")
                f.write(f"Bot: {bot_msg}\n\n")
        
        print(f"✅ Augmented to {len(augmented)} conversations")
        print(f"📁 Output: {output_file}")
        
        return output_file
    
    def _print_stats(self):
        """Print preprocessing statistics"""
        print("\n📊 Preprocessing Statistics:")
        print("-" * 50)
        for key, value in self.stats.items():
            key_display = key.replace('_', ' ').title()
            print(f"  {key_display:<25}: {value:,}")
    
    def analyze_data(self, input_file: str):
        """Analyze dataset statistics"""
        
        print(f"\n📈 Analyzing: {input_file}")
        print("-" * 50)
        
        user_lengths = []
        bot_lengths = []
        vocab = set()
        token_freq = Counter()
        
        with open(input_file, 'r', encoding='utf-8', errors='ignore') as f:
            current_user = None
            for line in f:
                line = line.strip()
                if line.startswith('User:'):
                    current_user = line[5:].strip()
                    user_lengths.append(len(current_user.split()))
                elif line.startswith('Bot:') and current_user:
                    bot_msg = line[4:].strip()
                    bot_lengths.append(len(bot_msg.split()))
                    
                    for token in (current_user + bot_msg).lower().split():
                        token = re.sub(r'[^a-z0-9]', '', token)
                        if token:
                            vocab.add(token)
                            token_freq[token] += 1
        
        # Statistics
        total_conversations = len(user_lengths)
        avg_user_len = sum(user_lengths) / len(user_lengths) if user_lengths else 0
        avg_bot_len = sum(bot_lengths) / len(bot_lengths) if bot_lengths else 0
        
        print(f"  Total Conversations  : {total_conversations:,}")
        print(f"  Avg User Message Len : {avg_user_len:.1f} tokens")
        print(f"  Avg Bot Message Len  : {avg_bot_len:.1f} tokens")
        print(f"  Unique Vocab         : {len(vocab):,} tokens")
        print(f"  File Size            : {Path(input_file).stat().st_size / (1024*1024):.2f} MB")
        
        print(f"\n  Top 10 Most Common Tokens:")
        for token, freq in token_freq.most_common(10):
            print(f"    - {token:<20}: {freq:,}")


def main():
    """Interactive preprocessing menu"""
    
    print("\n" + "=" * 60)
    print("🧹 MiniGPT Data Preprocessing Pipeline")
    print("=" * 60)
    print("\n🎯 Available Operations:")
    print("1. Clean and validate data")
    print("2. Balance dataset (random sampling)")
    print("3. Augment data")
    print("4. Analyze dataset statistics")
    print("5. Full pipeline (clean + analyze)")
    print("6. Exit")
    
    choice = input("\nSelect option (1-6): ").strip()
    
    preprocessor = DataPreprocessor()
    
    if choice == '1':
        input_file = input("Input file path: ").strip()
        output_file = input("Output file path (default: processed_clean.txt): ").strip()
        output_file = output_file or "processed_clean.txt"
        preprocessor.process_user_bot_format(input_file, output_file)
    
    elif choice == '2':
        input_file = input("Input file path: ").strip()
        output_file = input("Output file path (default: balanced_data.txt): ").strip()
        output_file = output_file or "balanced_data.txt"
        size = input("Sample size (default: 50000): ").strip()
        size = int(size) if size else 50000
        preprocessor.balance_dataset(input_file, output_file, size)
    
    elif choice == '3':
        input_file = input("Input file path: ").strip()
        output_file = input("Output file path (default: augmented_data.txt): ").strip()
        output_file = output_file or "augmented_data.txt"
        preprocessor.augment_data(input_file, output_file)
    
    elif choice == '4':
        input_file = input("Input file path: ").strip()
        preprocessor.analyze_data(input_file)
    
    elif choice == '5':
        input_file = input("Input file path: ").strip()
        output_file = input("Output file path (default: processed_final.txt): ").strip()
        output_file = output_file or "processed_final.txt"
        preprocessor.process_user_bot_format(input_file, output_file)
        preprocessor.analyze_data(output_file)
    
    elif choice != '6':
        print("❌ Invalid option")
    
    print("\n✅ Done!")


if __name__ == "__main__":
    main()
