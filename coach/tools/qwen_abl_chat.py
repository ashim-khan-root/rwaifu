import sys, time, json, urllib.request

MODEL = "hf.co/bartowski/Qwen2.5-Coder-0.5B-Instruct-abliterated-GGUF:Q4_K_S"

def ollama_chat(messages):
    data = json.dumps({"model": MODEL, "messages": messages, "stream": False}).encode()
    req = urllib.request.Request("http://localhost:11434/api/chat", data=data, headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req).read())["message"]["content"]

messages = []
print("Qwen Abliterated (Ctrl+C to exit)\n")

while True:
    try:
        user = input("You: ")
    except (EOFError, KeyboardInterrupt):
        print()
        break
    if not user:
        continue
    messages.append({"role": "user", "content": user})
    t0 = time.time()
    try:
        r = ollama_chat(messages)
        messages.append({"role": "assistant", "content": r})
        print(f"Qwen [{time.time()-t0:.1f}s]: {r}\n")
    except Exception as e:
        print(f"Error: {e}")
