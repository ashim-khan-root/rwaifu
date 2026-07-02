import sys
import os
import json
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools.db import get_db

SNAPSHOT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "memory", "snapshots")


def save_snapshot(task="", files="", decisions="", next_steps=""):
    os.makedirs(SNAPSHOT_DIR, exist_ok=True)
    db = get_db()

    cur = db.execute("SELECT * FROM sessions ORDER BY date DESC LIMIT 5")
    sessions = cur.fetchall()
    cur = db.execute("SELECT * FROM insights ORDER BY confidence DESC LIMIT 10")
    insights = cur.fetchall()
    cur = db.execute("SELECT * FROM memories ORDER BY timestamp DESC LIMIT 20")
    memories = cur.fetchall()
    cur = db.execute("SELECT * FROM tasks WHERE status='pending'")
    tasks = cur.fetchall()
    cur = db.execute("SELECT * FROM goals WHERE status='active'")
    goals = cur.fetchall()
    cur = db.execute("SELECT * FROM checkpoint")
    checkpoint = cur.fetchall()

    snapshot = {
        "timestamp": datetime.now().isoformat(),
        "task": task,
        "files": files,
        "decisions": decisions,
        "next_steps": next_steps,
        "sessions": sessions,
        "insights": insights,
        "memories": memories,
        "tasks": tasks,
        "goals": goals,
        "checkpoint": {c["key"]: c["value"] for c in checkpoint},
    }

    filename = f"snapshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    filepath = os.path.join(SNAPSHOT_DIR, filename)
    with open(filepath, "w") as f:
        json.dump(snapshot, f, indent=2, default=str)
    return filepath


def load_snapshot(filepath):
    with open(filepath) as f:
        return json.load(f)


def list_snapshots():
    os.makedirs(SNAPSHOT_DIR, exist_ok=True)
    files = sorted(os.listdir(SNAPSHOT_DIR), reverse=True)
    return files
