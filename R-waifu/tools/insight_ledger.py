import sys
import os
from datetime import datetime
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools.db import get_db


def log_event(event, payload=None):
    db = get_db()
    now = datetime.now().isoformat()
    db.execute(
        "INSERT INTO events (event, timestamp, payload) VALUES (?, ?, ?)",
        (event, now, json.dumps(payload or {})),
    )
    db.commit()


def add_insight(content, category="general", confidence=0.5, source=""):
    db = get_db()
    now = datetime.now().isoformat()
    db.execute(
        "INSERT INTO insights (content, category, confidence, source, created) VALUES (?, ?, ?, ?, ?)",
        (content, category, confidence, source, now),
    )
    db.commit()
    log_event("insight:new", {"content": content, "category": category})


def get_recent_insights(limit=10):
    db = get_db()
    cur = db.execute("SELECT * FROM insights ORDER BY created DESC LIMIT ?", (limit,))
    return cur.fetchall()


def add_memory(content, category="general", source="", importance=1, tags=""):
    db = get_db()
    now = datetime.now().isoformat()
    db.execute(
        "INSERT INTO memories (content, category, source, timestamp, importance, tags) VALUES (?, ?, ?, ?, ?, ?)",
        (content, category, source, now, importance, tags),
    )
    db.commit()
    log_event("memory:new", {"category": category, "importance": importance})


def search_memories(query, limit=10):
    db = get_db()
    cur = db.execute(
        "SELECT * FROM memories WHERE content LIKE ? ORDER BY importance DESC, timestamp DESC LIMIT ?",
        (f"%{query}%", limit),
    )
    return cur.fetchall()


def check_traits():
    db = get_db()
    cur = db.execute("SELECT trait, value, description FROM personality_traits ORDER BY trait")
    return cur.fetchall()


def update_trait(trait, delta):
    db = get_db()
    db.execute("UPDATE personality_traits SET value = MIN(1.0, MAX(0.0, value + ?)) WHERE trait = ?", (delta, trait))
    db.commit()


def log_nickname(nickname, context="general"):
    db = get_db()
    now = datetime.now().isoformat()
    cur = db.execute("SELECT id, usage_count FROM nicknames WHERE nickname=?", (nickname,))
    row = cur.fetchone()
    if row:
        db.execute(
            "UPDATE nicknames SET usage_count = usage_count + 1, last_used = ? WHERE id = ?",
            (now, row["id"]),
        )
    else:
        db.execute(
            "INSERT INTO nicknames (nickname, context, usage_count, last_used) VALUES (?, ?, 1, ?)",
            (nickname, context, now),
        )
    db.commit()


def add_milestone(milestone, description=""):
    db = get_db()
    now = datetime.now().isoformat()
    db.execute(
        "INSERT INTO relationship_milestones (milestone, date, description) VALUES (?, ?, ?)",
        (milestone, now, description),
    )
    db.commit()
    log_event("milestone:achieved", {"milestone": milestone})
