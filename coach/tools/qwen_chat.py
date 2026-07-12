import sys, time
sys.path.insert(0, "coach/tools")
from qwen_inference import QwenInference

q = QwenInference()
messages = []
print("Qwen chat (Ctrl+C to exit)\n")

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
    r = q.chat(messages, max_new_tokens=200)
    elapsed = time.time() - t0
    messages.append({"role": "assistant", "content": r})
    print(f"Qwen [{elapsed:.1f}s]: {r}\n")
