import torch
from model import MiniGPT

# ---------- सेव किया हुआ मॉडल लोड करें ----------
checkpoint = torch.load('mini_gpt_model.pt', map_location='cpu')
stoi = checkpoint['stoi']
itos = checkpoint['itos']
vocab_size = checkpoint['vocab_size']
chars = checkpoint['chars']

model = MiniGPT(vocab_size=vocab_size)
model.load_state_dict(checkpoint['model_state_dict'])
model.eval()

# ---------- हेल्पर फंक्शंस ----------
def encode(s):
    return [stoi[c] for c in s if c in stoi]

def decode(l):
    return ''.join([itos[i] for i in l])

def generate_text(prompt="", max_length=100, temperature=0.4, use_greedy=True):
    """प्रॉम्प्ट को जारी रखते हुए टेक्स्ट जनरेट करें
    
    Args:
        prompt: शुरुआती टेक्स्ट
        max_length: कितने टोकन जनरेट करें
        temperature: संभावना का विविधता (कम = अधिक निश्चित, ज्यादा = अधिक यादृच्छिक)
        use_greedy: True = सबसे संभावित टोकन (निश्चित), False = नमूना (यादृच्छिक)
    """
    if not prompt:
        prompt = chars[0]  # डिफॉल्ट पहला अक्षर
    context = torch.tensor([encode(prompt)], dtype=torch.long)
    # यदि प्रॉम्प्ट में कोई अज्ञात अक्षर हो तो खाली टेंसर मिल सकता है
    if context.numel() == 0:
        return ""
    
    if use_greedy:
        out_idx = model.generate_greedy(context, max_new_tokens=max_length)
    else:
        out_idx = model.generate(context, max_new_tokens=max_length, temperature=temperature)
    return decode(out_idx[0].tolist())

def chat_response(user_input, max_length=120, temperature=0.3, use_greedy=True):
    """
    यूज़र का इनपुट लेकर बॉट जैसा रिस्पॉन्स बनाएँ।
    यह मानकर चलता है कि मॉडल 'User: ... Bot: ...' फॉर्मेट पर ट्रेन है।
    
    Args:
        user_input: यूज़र का सवाल
        max_length: जनरेट करने के लिए टोकन (अधिक = लंबा उत्तर)
        temperature: संभाव्यता विविधता
        use_greedy: True = निश्चित उत्तर, False = यादृच्छिक उत्तर
    """
    prompt = f"User: {user_input}\nBot:"
    full_output = generate_text(prompt, max_length, temperature, use_greedy)
    # 'Bot:' के बाद का भाग निकालें
    if "Bot:" in full_output:
        response = full_output.split("Bot:", 1)[1].strip()
        # अगर आगे फिर से 'User:' आ जाए तो वहाँ तक काटें
        if "User:" in response:
            response = response.split("User:", 1)[0].strip()
        return response
    else:
        # यदि 'Bot:' नहीं मिला तो पूरा जनरेटेड टेक्स्ट लौटाएँ (सादा कंटिन्यूएशन)
        return full_output

if __name__ == "__main__":
    print("🤖 MiniGPT Chat (Improved Generation)")
    print("=" * 50)
    print("Commands:")
    print("  'greedy'    - Switch to deterministic mode (आगे जो हो से हो)")
    print("  'sampling'  - Switch to creative mode (रचनात्मक उत्तर)")
    print("  'temp X'    - Set temperature (0.1-1.0)")
    print("  'exit'      - Quit")
    print("=" * 50)
    
    use_greedy = True  # Default: deterministic for better quality
    temperature = 0.3
    
    while True:
        user_msg = input("\nYou: ").strip()
        
        if not user_msg:
            continue
        
        # Check for commands
        if user_msg.lower() == "exit" or user_msg.lower() == "quit":
            print("Bot: Goodbye! 👋")
            break
        
        if user_msg.lower() == "greedy":
            use_greedy = True
            print("✅ Switched to GREEDY mode (deterministic - सबसे संभावित उत्तर)")
            continue
        
        if user_msg.lower() == "sampling":
            use_greedy = False
            print("✅ Switched to SAMPLING mode (creative - रचनात्मक उत्तर)")
            continue
        
        if user_msg.lower().startswith("temp "):
            try:
                temperature = float(user_msg.split()[1])
                temperature = max(0.1, min(1.0, temperature))  # Clamp between 0.1 and 1.0
                print(f"✅ Temperature set to {temperature}")
                continue
            except:
                print("❌ Usage: temp 0.5")
                continue
        
        # Generate response
        try:
            reply = chat_response(user_msg, max_length=120, temperature=temperature, use_greedy=use_greedy)
            print(f"Bot: {reply}")
        except Exception as e:
            print(f"❌ Error: {e}")