"""Hook: error — Log errors for analysis.
Usage: triggered by hook_runner.py error
"""
import sys, json, datetime

data = json.loads(sys.stdin.read())
payload = data.get("data", {})
ts = data.get("timestamp", datetime.datetime.now().isoformat())

error_msg = payload.get("message", "Unknown error")
source = payload.get("source", "unknown")

print(f"[error] {ts} — {source}: {error_msg}")
