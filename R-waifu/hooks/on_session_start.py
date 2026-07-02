import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools.db import get_db
from tools.insight_ledger import log_event


def run(event_name, context):
    if event_name != "session:start":
        return None

    db = get_db()
    cur = db.execute("SELECT id, title, rating, date FROM sessions ORDER BY date DESC LIMIT 1")
    last = cur.fetchone()
    msg = "Session started"
    if last:
        msg = f"Continuing after last session: {last['title']} ({last['rating']}/10)"

    log_event("session:start", {"last_session": last["id"] if last else None})
    return {"message": msg}
