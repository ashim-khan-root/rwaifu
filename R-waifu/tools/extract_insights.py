import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools.db import get_db
from tools.insight_ledger import add_insight, log_event


def extract_from_session(session_id):
    db = get_db()
    cur = db.execute("SELECT content, emotional_tone FROM session_memories WHERE session_id=?", (session_id,))
    memories = cur.fetchall()
    if not memories:
        return []

    insights = []
    emotional_counts = {}
    for m in memories:
        tone = m["emotional_tone"]
        emotional_counts[tone] = emotional_counts.get(tone, 0) + 1

    if emotional_counts:
        dominant = max(emotional_counts, key=emotional_counts.get)
        add_insight(
            f"Session had dominant {dominant} emotional tone ({emotional_counts[dominant]} moments)",
            category="emotional_pattern",
            confidence=0.6,
            source=f"session:{session_id}",
        )
        insights.append(f"dominant tone: {dominant}")

    return insights


def extract_evolution_patterns():
    db = get_db()
    cur = db.execute(
        "SELECT user_input, response, timestamp FROM interactions ORDER BY timestamp DESC LIMIT 50"
    )
    interactions = cur.fetchall()
    if len(interactions) < 3:
        return []

    topics = {}
    for i in interactions:
        words = i["user_input"].lower().split()
        for w in words:
            if len(w) > 4:
                topics[w] = topics.get(w, 0) + 1

    recurring = {k: v for k, v in topics.items() if v >= 3}
    for topic, count in sorted(recurring.items(), key=lambda x: -x[1])[:5]:
        add_insight(
            f"Recurring topic '{topic}' appeared {count} times in recent interactions",
            category="topic_pattern",
            confidence=0.5,
            source="extract_evolution_patterns",
        )

    return list(recurring.keys())[:5]


if __name__ == "__main__":
    patterns = extract_evolution_patterns()
    print(f"Found {len(patterns)} recurring patterns")
    for p in patterns:
        print(f"  - {p}")
