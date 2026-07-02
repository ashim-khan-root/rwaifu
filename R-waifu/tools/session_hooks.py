import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools.db import get_db


def pre_session():
    db = get_db()
    lines = []

    cur = db.execute("SELECT value FROM checkpoint WHERE key='phase'")
    row = cur.fetchone()
    phase = row["value"] if row else "Idle"
    lines.append(f"Phase: {phase}")

    cur = db.execute("SELECT value FROM checkpoint WHERE key='topic'")
    row = cur.fetchone()
    topic = row["value"] if row else "General"
    lines.append(f"Topic: {topic}")

    cur = db.execute("SELECT nickname, usage_count FROM nicknames ORDER BY usage_count DESC LIMIT 3")
    nicknames = cur.fetchall()
    if nicknames:
        fav = nicknames[0]["nickname"]
        lines.append(f"Favorite nickname: {fav}")

    cur = db.execute("SELECT title FROM goals WHERE status='active'")
    goals = cur.fetchall()
    if goals:
        lines.append("Active goals:")
        for g in goals:
            lines.append(f"  - {g['title']}")

    cur = db.execute("SELECT title, streak FROM habits WHERE status='active'")
    habits = cur.fetchall()
    if habits:
        lines.append("Tracked habits:")
        for h in habits:
            lines.append(f"  - {h['title']} (streak: {h['streak']})")

    cur = db.execute("SELECT id, title, rating, date FROM sessions ORDER BY date DESC LIMIT 1")
    last = cur.fetchone()
    if last:
        lines.append(f"Last session: {last['title']} ({last['rating']}/10)")

    cur = db.execute("SELECT trait, value FROM personality_traits ORDER BY value DESC")
    traits = cur.fetchall()
    if traits:
        lines.append("Current traits:")
        for t in traits:
            filled = int(t["value"] * 10)
            empty = 10 - filled
            bar = "#" * filled + "-" * empty
            lines.append(f"  {t['trait']:22s} [{bar}] {t['value']:.1f}")

    cur = db.execute("SELECT milestone, date FROM relationship_milestones ORDER BY date DESC LIMIT 3")
    milestones = cur.fetchall()
    if milestones:
        lines.append("Recent milestones:")
        for m in milestones:
            lines.append(f"  - {m['milestone']} ({m['date'][:10]})")

    cur = db.execute("SELECT content, confidence FROM insights ORDER BY confidence DESC LIMIT 5")
    insights = cur.fetchall()
    if insights:
        lines.append("Top insights:")
        for i in insights:
            lines.append(f"  - {i['content']}")

    return "\n".join(lines)


def post_session():
    pass
