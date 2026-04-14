from fastapi import FastAPI
import torch
from model import MiniGPT

# ---------- मॉडल लोड करें ----------
checkpoint = torch.load('mini_gpt_model.pt', map_location='cpu')
stoi = checkpoint['stoi']
itos = checkpoint['itos']
vocab_size = checkpoint['vocab_size']

model = MiniGPT(vocab_size=vocab_size)
model.load_state_dict(checkpoint['model_state_dict'])
model.eval()

# ---------- हेल्पर फंक्शंस ----------
def encode(s):
    return [stoi[c] for c in s if c in stoi]

def decode(l):
    return ''.join([itos[i] for i in l])

def generate_text(prompt="", max_length=50, temperature=0.8):
    if not prompt:
        return ""
    context = torch.tensor([encode(prompt)], dtype=torch.long)
    if context.numel() == 0:
        return ""
    out_idx = model.generate(context, max_new_tokens=max_length)
    return decode(out_idx[0].tolist())

def chat_response(user_input, max_length=80, temperature=0.8):
    # प्रॉम्प्ट को संवाद फॉर्मेट में ढालें (यदि मॉडल उस पर ट्रेन है)
    prompt = f"User: {user_input}\nBot:"
    full_output = generate_text(prompt, max_length, temperature)
    if "Bot:" in full_output:
        response = full_output.split("Bot:", 1)[1].strip()
        if "User:" in response:
            response = response.split("User:", 1)[0].strip()
        return response
    else:
        return full_output

# ---------- FastAPI ऐप ----------
app = FastAPI()

@app.get("/chat")
def chat(q: str = ""):
    if not q:
        return {"error": "Please provide a query with ?q=..."}
    # पूरे क्वेरी स्ट्रिंग का उपयोग करें (न कि सिर्फ पहला अक्षर)
    user_input = q.strip()
    # चेक करें कि कम से कम एक ज्ञात अक्षर हो
    if not any(ch in stoi for ch in user_input):
        return {"error": "No valid characters found in query."}
    response = chat_response(user_input, max_length=100)
    return {"response": response}

# uvicorn से चलाने के लिए कोई अतिरिक्त कोड आवश्यक नहीं