import sys
import os
import json
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools.db import get_db
from tools.insight_ledger import log_event


def scaffold(title, milestone="", criteria=None):
    db = get_db()
    entry = {
        "title": title,
        "milestone": milestone,
        "criteria": criteria or [],
        "status": "active",
        "created": datetime.now().isoformat(),
    }
    key = f"isa:{title}"
    db.execute(
        "INSERT OR REPLACE INTO checkpoint (key, value) VALUES (?, ?)",
        (key, json.dumps(entry)),
    )
    db.commit()
    log_event("isa:scaffold", {"title": title})
    return key


def check(title):
    db = get_db()
    cur = db.execute("SELECT value FROM checkpoint WHERE key=?", (f"isa:{title}",))
    row = cur.fetchone()
    return json.loads(row["value"]) if row else None


def done(title):
    db = get_db()
    cur = db.execute("SELECT value FROM checkpoint WHERE key=?", (f"isa:{title}",))
    row = cur.fetchone()
    if row:
        entry = json.loads(row["value"])
        entry["status"] = "done"
        db.execute(
            "INSERT OR REPLACE INTO checkpoint (key, value) VALUES (?, ?)",
            (f"isa:{title}", json.dumps(entry)),
        )
        db.commit()
        log_event("isa:done", {"title": title})
