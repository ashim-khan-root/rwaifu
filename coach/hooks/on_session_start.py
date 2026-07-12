"""Hook: session:start — Log session start + context hints.
Usage: triggered by hook_runner.py session:start
"""
import sys, json, datetime

data = json.loads(sys.stdin.read())
event = data.get("event", "unknown")
ts = data.get("timestamp", datetime.datetime.now().isoformat())

print(f"[session:start] Session started at {ts}")
print(f"[session:start] Event: {event}")

if data.get("data"):
    for k, v in data["data"].items():
        print(f"[session:start]   {k}: {v}")
