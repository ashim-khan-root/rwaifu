import sys
import os
import uuid
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools.db import get_db
from tools.auto_evolve import evolve_from_session


def store_session(title, duration_min=0, rating=0, mood="", notes=""):
    db = get_db()
    session_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    db.execute(
        "INSERT INTO sessions (id, date, title, duration_min, rating, mood, notes) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (session_id, now, title, duration_min, rating, mood, notes),
    )
    db.commit()

    evolve_from_session({
        "session_id": session_id,
        "title": title,
        "duration_min": duration_min,
        "rating": rating,
        "mood": mood,
        "notes": notes,
    })

    return session_id


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("title")
    parser.add_argument("--duration", type=int, default=0)
    parser.add_argument("--rating", type=int, default=0)
    parser.add_argument("--mood", default="")
    parser.add_argument("--notes", default="")
    args = parser.parse_args()
    sid = store_session(args.title, args.duration, args.rating, args.mood, args.notes)
    print(f"Session stored: {sid}")
