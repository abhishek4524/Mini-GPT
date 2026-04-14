import torch
import torch.nn as nn
from model import MiniGPT
import os

# ---------- कॉन्फ़िगरेशन ----------
BATCH_SIZE = 128          # Increased from 64
BLOCK_SIZE = 128          # Increased from 64 for better context
LEARNING_RATE = 0.0005    # Decreased from 0.001 (was too high)
EPOCHS = 10000            # Can be extended for larger datasets
CHECKPOINT_INTERVAL = 500

# Validation settings
VALIDATION_SPLIT = 0.1    # 10% of data for validation
VALIDATION_INTERVAL = 500 # Validate every 500 steps

MODEL_SAVE_PATH = 'mini_gpt_model.pt'
CHECKPOINT_PATH = 'training_checkpoint.pt'

# Mixed precision training (optional, for faster training)
USE_MIXED_PRECISION = True

# ---------- डिवाइस सेट करें (GPU उपलब्ध होने पर cuda, नहीं तो cpu) ----------
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"Using device: {device}")

# For mixed precision
if USE_MIXED_PRECISION and device.type == 'cuda':
    from torch.cuda.amp import autocast, GradScaler
    scaler = GradScaler()
    print("✅ Using mixed precision training")
else:
    scaler = None
    USE_MIXED_PRECISION = False

# ---------- डेटा लोड करें ----------
with open('data.txt', 'r', encoding='utf-8') as f:
    text = f.read()

chars = sorted(list(set(text)))
vocab_size = len(chars)
stoi = {ch: i for i, ch in enumerate(chars)}
itos = {i: ch for ch, i in stoi.items()}

encode = lambda s: [stoi[c] for c in s]
decode = lambda l: ''.join([itos[i] for i in l])

data = torch.tensor(encode(text), dtype=torch.long)
print(f"Data length: {len(data)} characters, Vocab size: {vocab_size}")

# ---------- ट्रेन/वेलिडेशन स्प्लिट ----------
split_idx = int(len(data) * (1 - VALIDATION_SPLIT))
train_data = data[:split_idx]
val_data = data[split_idx:]
print(f"Train set: {len(train_data)} | Validation set: {len(val_data)}")

# ---------- बैच जनरेटर ----------
def get_batch(split='train', batch_size=BATCH_SIZE, block_size=BLOCK_SIZE):
    data_src = train_data if split == 'train' else val_data
    
    if len(data_src) < block_size:
        print(f"⚠️  Warning: {split} data size is smaller than block_size")
        return None, None
    
    ix = torch.randint(len(data_src) - block_size, (batch_size,))
    x = torch.stack([data_src[i:i+block_size] for i in ix])
    y = torch.stack([data_src[i+1:i+block_size+1] for i in ix])
    
    x, y = x.to(device), y.to(device)
    return x, y

# ---------- मॉडल इनिशियलाइज़ करें ----------
model = MiniGPT(
    vocab_size=vocab_size,
    d_model=256,           # Better architecture
    n_heads=8,
    n_layers=4,
    block_size=BLOCK_SIZE,
    dropout=0.1
)
model = model.to(device)
print(f"Model parameters: {sum(p.numel() for p in model.parameters()):,}")

optimizer = torch.optim.AdamW(model.parameters(), lr=LEARNING_RATE, weight_decay=0.01)

# ---------- लर्निंग रेट शेड्यूलर ----------
scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
    optimizer, 
    T_max=EPOCHS,
    eta_min=1e-6
)

start_epoch = 0
best_val_loss = float('inf')
best_train_loss = float('inf')
train_losses = []
val_losses = []

# ---------- चेकपॉइंट से रिज़्यूम करें ----------
if os.path.exists(CHECKPOINT_PATH):
    print(f"Loading checkpoint from {CHECKPOINT_PATH}")
    checkpoint = torch.load(CHECKPOINT_PATH, map_location=device)
    model.load_state_dict(checkpoint['model_state_dict'])
    optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
    scheduler.load_state_dict(checkpoint['scheduler_state_dict'])
    start_epoch = checkpoint['epoch'] + 1
    best_val_loss = checkpoint.get('best_val_loss', float('inf'))
    best_train_loss = checkpoint.get('best_train_loss', float('inf'))
    train_losses = checkpoint.get('train_losses', [])
    val_losses = checkpoint.get('val_losses', [])
    print(f"Resuming from epoch {start_epoch}")
    print(f"Previous best train loss: {best_train_loss:.4f}")
    print(f"Previous best val loss: {best_val_loss:.4f}")
else:
    print("No checkpoint found, starting fresh training.")

# ---------- वेलिडेशन लूप ----------
def validate(num_batches=50):
    """Compute validation loss"""
    model.eval()
    val_loss = 0
    
    with torch.no_grad():
        for _ in range(num_batches):
            xb, yb = get_batch('val', batch_size=BATCH_SIZE, block_size=BLOCK_SIZE)
            if xb is None:
                break
            
            if USE_MIXED_PRECISION:
                with autocast():
                    logits, loss = model(xb, yb)
            else:
                logits, loss = model(xb, yb)
            
            val_loss += loss.item()
    
    model.train()
    return val_loss / num_batches

# ---------- ट्रेनिंग लूप ----------
print("\n" + "=" * 60)
print("🚀 Starting Training")
print("=" * 60)

for epoch in range(start_epoch, EPOCHS):
    model.train()
    xb, yb = get_batch('train', batch_size=BATCH_SIZE, block_size=BLOCK_SIZE)
    
    if xb is None:
        print("❌ Could not get training batch, stopping.")
        break
    
    optimizer.zero_grad()
    
    if USE_MIXED_PRECISION:
        with autocast():
            logits, loss = model(xb, yb)
        scaler.scale(loss).backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        scaler.step(optimizer)
        scaler.update()
    else:
        logits, loss = model(xb, yb)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        optimizer.step()
    
    train_losses.append(loss.item())
    
    # लर्निंग रेट शेड्यूलर स्टेप
    scheduler.step()
    
    # In progress logging
    if epoch % 100 == 0:
        current_lr = optimizer.param_groups[0]['lr']
        print(f"Epoch {epoch:5d} | Loss: {loss.item():.4f} | LR: {current_lr:.2e}")
    
    # पीरियोडिक वेलिडेशन
    if epoch % VALIDATION_INTERVAL == 0 and epoch > 0:
        val_loss = validate(num_batches=50)
        val_losses.append(val_loss)
        
        print(f"  ✓ Validation Loss: {val_loss:.4f}")
        
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            print(f"  🌟 Best validation loss improved to {best_val_loss:.4f}")
    
    if loss.item() < best_train_loss:
        best_train_loss = loss.item()
    
    # चेकपॉइंट सेव करें
    if epoch % CHECKPOINT_INTERVAL == 0 and epoch > 0:
        checkpoint = {
            'epoch': epoch,
            'model_state_dict': model.state_dict(),
            'optimizer_state_dict': optimizer.state_dict(),
            'scheduler_state_dict': scheduler.state_dict(),
            'loss': loss.item(),
            'best_train_loss': best_train_loss,
            'best_val_loss': best_val_loss,
            'train_losses': train_losses,
            'val_losses': val_losses,
            'stoi': stoi,
            'itos': itos,
            'vocab_size': vocab_size,
            'chars': chars
        }
        torch.save(checkpoint, CHECKPOINT_PATH)
        print(f"\n💾 Checkpoint saved at epoch {epoch}")
        
        if loss.item() < best_train_loss:
            best_train_loss = loss.item()
            torch.save(checkpoint, MODEL_SAVE_PATH)
            print(f"🏆 Best model saved with train loss {best_train_loss:.4f}")

# ---------- अंतिम मॉडल सेव करें ----------
print("\n" + "=" * 60)
print("✅ Training Completed")
print("=" * 60)

final_checkpoint = {
    'epoch': EPOCHS - 1,
    'model_state_dict': model.state_dict(),
    'optimizer_state_dict': optimizer.state_dict(),
    'scheduler_state_dict': scheduler.state_dict(),
    'loss': loss.item(),
    'best_train_loss': best_train_loss,
    'best_val_loss': best_val_loss,
    'train_losses': train_losses,
    'val_losses': val_losses,
    'stoi': stoi,
    'itos': itos,
    'vocab_size': vocab_size,
    'chars': chars
}
torch.save(final_checkpoint, MODEL_SAVE_PATH)
print(f"✅ Model saved as '{MODEL_SAVE_PATH}'")
print(f"📊 Training Statistics:")
print(f"   Best Train Loss: {best_train_loss:.4f}")
print(f"   Best Val Loss:   {best_val_loss:.4f}")
print(f"   Total Epochs:    {EPOCHS}")