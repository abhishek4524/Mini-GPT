import torch
import torch.nn as nn

class MiniGPT(nn.Module):
    def __init__(self, vocab_size, d_model=256, n_heads=8, n_layers=4, block_size=128, dropout=0.1):
        super().__init__()
        self.token_embedding = nn.Embedding(vocab_size, d_model)
        self.position_embedding = nn.Embedding(block_size, d_model)
        self.block_size = block_size
        self.embedding_dropout = nn.Dropout(dropout)

        decoder_layer = nn.TransformerDecoderLayer(
            d_model=d_model, 
            nhead=n_heads, 
            batch_first=True,
            dropout=dropout,
            dim_feedforward=1024,  # Larger feed-forward network
            activation='gelu'       # GELU activation
        )
        self.transformer = nn.TransformerDecoder(decoder_layer, num_layers=n_layers)
        self.layer_norm = nn.LayerNorm(d_model)  # Final layer normalization
        self.lm_head = nn.Linear(d_model, vocab_size)

    def forward(self, idx, targets=None):
        B, T = idx.shape
        tok_emb = self.token_embedding(idx)                     # (B,T,d_model)
        pos = torch.arange(0, T, device=idx.device).unsqueeze(0) # (1,T)
        pos_emb = self.position_embedding(pos)                   # (1,T,d_model)
        x = tok_emb + pos_emb                                    # (B,T,d_model)
        x = self.embedding_dropout(x)                            # Apply embedding dropout

        # Causal mask: future tokens ko ignore kare
        causal_mask = torch.triu(
            torch.ones(T, T, device=idx.device) * float('-inf'), 
            diagonal=1
        )
        # memory=None kyunki hum encoder-decoder nahi, sirf decoder use kar rahe
        x = self.transformer(tgt=x, memory=torch.zeros_like(x), tgt_mask=causal_mask)
        x = self.layer_norm(x)                                   # Apply layer normalization
        logits = self.lm_head(x)                                 # (B,T,vocab_size)

        loss = None
        if targets is not None:
            loss_fn = nn.CrossEntropyLoss()
            loss = loss_fn(logits.view(-1, logits.size(-1)), targets.view(-1))
        return logits, loss

    @torch.no_grad()
    def generate(self, idx, max_new_tokens, temperature=1.0):
        """idx shape: (B,T)
        
        Sampling-based generation with temperature control.
        Higher temperature = more random. Lower temperature = more deterministic.
        """
        self.eval()
        for _ in range(max_new_tokens):
            idx_cond = idx[:, -self.block_size:]                 # last block_size tokens
            logits, _ = self(idx_cond)                           # (B,T,vocab_size)
            logits = logits[:, -1, :]                            # last token logits
            
            # Apply temperature scaling
            logits = logits / temperature
            probs = torch.softmax(logits, dim=-1)
            idx_next = torch.multinomial(probs, num_samples=1)   # sample
            idx = torch.cat((idx, idx_next), dim=1)
        return idx
    
    @torch.no_grad()
    def generate_greedy(self, idx, max_new_tokens):
        """idx shape: (B,T)
        
        Greedy generation - always picks the most likely token.
        Produces more coherent and deterministic output.
        """
        self.eval()
        for _ in range(max_new_tokens):
            idx_cond = idx[:, -self.block_size:]                 # last block_size tokens
            logits, _ = self(idx_cond)                           # (B,T,vocab_size)
            logits = logits[:, -1, :]                            # last token logits
            
            # Take argmax (most likely token)
            idx_next = torch.argmax(logits, dim=-1, keepdim=True)
            idx = torch.cat((idx, idx_next), dim=1)
        return idx