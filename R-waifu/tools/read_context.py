import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools.db import get_db
from tools.session_hooks import pre_session


def read_context(lines=10):
    print("=== R-waifu Context ===")
    print(pre_session())
    print()

    db = get_db()
    cur = db.execute("SELECT date, title, rating, mood FROM sessions ORDER BY date DESC LIMIT ?", (lines,))
    recent = cur.fetchall()
    if recent:
        print("Recent sessions:")
        for s in recent[:5]:
            print(f"  {s['date'][:16]} | {s['title']} | {s['rating']}/10 | mood: {s['mood']}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("n", nargs="?", type=int, default=10)
    args = parser.parse_args()
    read_context(args.n)
