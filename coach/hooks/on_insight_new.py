"""Hook: insight:new — Log new insight events.
Usage: triggered by hook_runner.py insight:new
"""
import sys, json

data = json.loads(sys.stdin.read())
payload = data.get("data", {})
pattern = payload.get("pattern", "unknown")
confidence = payload.get("confidence", "?")
print(f"[insight:new] Pattern: {pattern} (confidence: {confidence})")
