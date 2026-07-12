"""Hook: session:end — Post-session cleanup and logging.
Usage: triggered by hook_runner.py session:end
"""
import sys, json, datetime

data = json.loads(sys.stdin.read())
ts = data.get("timestamp", datetime.datetime.now().isoformat())
payload = data.get("data", {})

print(f"[session:end] Session ended at {ts}")
skill = payload.get("skill", "unknown")
duration = payload.get("duration", "?")
rating = payload.get("rating", "?")
print(f"[session:end] Skill: {skill}, Duration: {duration}min, Rating: {rating}/10")
