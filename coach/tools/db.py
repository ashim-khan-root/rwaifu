"""SQLite storage backend for personal-coach memory."""
import datetime
import json
import sqlite3
import sys
from pathlib import Path

MEM_DIR = Path(__file__).resolve().parent.parent / "memory"
DB_PATH = MEM_DIR / "coach.db"

_connection: sqlite3.Connection | None = None

SCHEMA_VERSION = 3


def _dict_factory(cursor, row):
    cols = [c[0] for c in cursor.description]
    return dict(zip(cols, row))


def get_db() -> sqlite3.Connection:
    global _connection
    if _connection is None:
        _connection = sqlite3.connect(str(DB_PATH))
        _connection.row_factory = _dict_factory
        _connection.execute("PRAGMA journal_mode=WAL")
        _connection.execute("PRAGMA foreign_keys=ON")
    return _connection


def init_db():
    db = get_db()
    db.executescript("""
        CREATE TABLE IF NOT EXISTS schema_version (
            version INTEGER PRIMARY KEY
        );
        CREATE TABLE IF NOT EXISTS insight_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            payload TEXT DEFAULT '{}'
        );
        CREATE INDEX IF NOT EXISTS idx_insight_event ON insight_events(event);
        CREATE INDEX IF NOT EXISTS idx_insight_ts ON insight_events(timestamp);

        CREATE TABLE IF NOT EXISTS tasks (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            created TEXT NOT NULL,
            priority TEXT DEFAULT 'medium',
            status TEXT DEFAULT 'pending',
            due TEXT,
            notes TEXT DEFAULT '',
            verify_method TEXT DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            date TEXT NOT NULL,
            skill TEXT NOT NULL,
            duration_min INTEGER DEFAULT 0,
            rating INTEGER DEFAULT 0,
            notes TEXT DEFAULT ''
        );
        CREATE INDEX IF NOT EXISTS idx_session_date ON sessions(date);

        CREATE TABLE IF NOT EXISTS session_decisions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL REFERENCES sessions(id),
            decision TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS goals (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            status TEXT DEFAULT 'active',
            created TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS habits (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            status TEXT DEFAULT 'active',
            streak INTEGER DEFAULT 0,
            created TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS checkpoint (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS prds (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            status TEXT DEFAULT 'DRAFT',
            created TEXT NOT NULL,
            updated TEXT NOT NULL,
            phase TEXT DEFAULT 'research',
            plan_path TEXT,
            criteria TEXT DEFAULT '',
            verification_method TEXT DEFAULT '',
            notes TEXT DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS intent_corrections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            input_pattern TEXT NOT NULL,
            correct_mode TEXT NOT NULL,
            correct_intent TEXT NOT NULL DEFAULT 'general',
            created TEXT NOT NULL,
            hit_count INTEGER DEFAULT 1,
            notes TEXT DEFAULT ''
        );
        CREATE INDEX IF NOT EXISTS idx_intent_corrections_pattern ON intent_corrections(input_pattern);
    """)
    row = db.execute("SELECT version FROM schema_version ORDER BY version DESC LIMIT 1").fetchone()
    if not row:
        db.execute("INSERT INTO schema_version (version) VALUES (?)", (SCHEMA_VERSION,))
        db.commit()
    else:
        current_ver = row["version"]
        if current_ver < 2:
            try:
                db.execute("ALTER TABLE tasks ADD COLUMN verify_method TEXT DEFAULT ''")
            except sqlite3.OperationalError:
                pass  # column already exists
            try:
                db.execute("""
                    CREATE TABLE IF NOT EXISTS prds (
                        id TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        status TEXT DEFAULT 'DRAFT',
                        created TEXT NOT NULL,
                        updated TEXT NOT NULL,
                        phase TEXT DEFAULT 'research',
                        plan_path TEXT,
                        criteria TEXT DEFAULT '',
                        verification_method TEXT DEFAULT '',
                        notes TEXT DEFAULT ''
                    )
                """)
            except sqlite3.OperationalError:
                pass
            db.execute("INSERT OR REPLACE INTO schema_version (version) VALUES (?)", (SCHEMA_VERSION,))
            db.commit()
        if current_ver < 3:
            try:
                db.execute("""
                    CREATE TABLE IF NOT EXISTS intent_corrections (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        input_pattern TEXT NOT NULL,
                        correct_mode TEXT NOT NULL,
                        correct_intent TEXT NOT NULL DEFAULT 'general',
                        created TEXT NOT NULL,
                        hit_count INTEGER DEFAULT 1,
                        notes TEXT DEFAULT ''
                    )
                """)
                db.execute("CREATE INDEX IF NOT EXISTS idx_intent_corrections_pattern ON intent_corrections(input_pattern)")
            except sqlite3.OperationalError:
                pass
            db.execute("INSERT OR REPLACE INTO schema_version (version) VALUES (?)", (SCHEMA_VERSION,))
            db.commit()


#
# ── Insight Ledger ──────────────────────────────────────────────────────
#

def log_insight(event: str, payload: dict | None = None):
    db = get_db()
    db.execute(
        "INSERT INTO insight_events (event, timestamp, payload) VALUES (?, ?, ?)",
        (event, datetime.datetime.now(datetime.timezone.utc).isoformat(), json.dumps(payload or {})),
    )
    db.commit()


def query_insights(event: str | None = None,
                   since: str | None = None,
                   limit: int = 50) -> list[dict]:
    db = get_db()
    clauses = []
    params = []
    if event:
        clauses.append("event = ?")
        params.append(event)
    if since:
        clauses.append("timestamp >= ?")
        params.append(since)
    where = "WHERE " + " AND ".join(clauses) if clauses else ""
    rows = db.execute(
        f"SELECT id, event, timestamp, payload FROM insight_events {where} ORDER BY timestamp DESC LIMIT ?",
        (*params, limit),
    ).fetchall()
    for r in rows:
        r["payload"] = json.loads(r["payload"])
    return rows


def get_insight_stats() -> dict:
    db = get_db()
    total = db.execute("SELECT COUNT(*) as c FROM insight_events").fetchone()["c"]
    types = [r["event"] for r in db.execute("SELECT DISTINCT event FROM insight_events ORDER BY event").fetchall()]
    ts = db.execute("SELECT MIN(timestamp) as earliest, MAX(timestamp) as latest FROM insight_events").fetchone()
    return {
        "total": total,
        "event_types": types,
        "earliest": ts["earliest"] if ts else None,
        "latest": ts["latest"] if ts else None,
    }


def migrate_insight_ledger_from_json():
    path = MEM_DIR / "insight_ledger.json"
    if not path.exists():
        return 0
    raw = path.read_text(encoding="utf-8")
    entries = json.loads(raw) if raw else []
    if not entries:
        return 0
    db = get_db()
    existing = db.execute("SELECT COUNT(*) as c FROM insight_events").fetchone()["c"]
    if existing > 0:
        return 0
    for entry in entries:
        db.execute(
            "INSERT INTO insight_events (event, timestamp, payload) VALUES (?, ?, ?)",
            (entry["event"], entry["timestamp"], json.dumps(entry.get("payload", {}))),
        )
    db.commit()
    return len(entries)


#
# ── Tasks ───────────────────────────────────────────────────────────────
#

def load_tasks() -> list[dict]:
    return get_db().execute("SELECT * FROM tasks ORDER BY created DESC").fetchall()


def add_task(task_id: str, title: str, priority: str = "medium", notes: str = "",
             verify_method: str = "") -> dict:
    task = {
        "id": task_id,
        "title": title,
        "created": datetime.date.today().isoformat(),
        "priority": priority if priority in ("low", "medium", "high") else "medium",
        "status": "pending",
        "notes": notes,
        "verify_method": verify_method if verify_method in ("CLI", "Test", "Static", "Browser", "Grep", "Read", "Custom", "") else "",
    }
    get_db().execute(
        "INSERT INTO tasks (id, title, created, priority, status, notes, verify_method) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (task["id"], task["title"], task["created"], task["priority"], task["status"], task["notes"], task["verify_method"]),
    )
    get_db().commit()
    return task


def update_task_status(task_id: str, status: str):
    get_db().execute("UPDATE tasks SET status = ? WHERE id = ?", (status, task_id))
    get_db().commit()


def delete_task(task_id: str) -> bool:
    cur = get_db().execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    get_db().commit()
    return cur.rowcount > 0


def migrate_tasks_from_md():
    path = MEM_DIR / "tasks.md"
    if not path.exists():
        return 0
    db = get_db()
    existing = db.execute("SELECT COUNT(*) as c FROM tasks").fetchone()["c"]
    if existing > 0:
        return 0
    import re as _re
    text = path.read_text(encoding="utf-8")
    tasks = []
    buffer = []
    for line in text.split("\n"):
        if line.startswith("- id:"):
            if buffer:
                tasks.append(_parse_task_md(buffer))
            buffer = [line]
        elif line.startswith("  ") and buffer:
            buffer.append(line)
    if buffer:
        tasks.append(_parse_task_md(buffer))
    count = 0
    for t in tasks:
        db.execute(
            "INSERT OR IGNORE INTO tasks (id, title, created, priority, status, due, notes) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (t.get("id", ""), t.get("title", ""), t.get("created", ""), t.get("priority", "medium"),
             t.get("status", "pending"), t.get("due"), t.get("notes", "")),
        )
        count += 1
    db.commit()
    return count


def _parse_task_md(lines: list[str]) -> dict:
    import re as _re
    task = {}
    for line in lines:
        if m := _re.match(r"- id:\s*(.+)", line):
            task["id"] = m.group(1).strip()
        elif m := _re.match(r"\s+title:\s*\"(.+)\"", line):
            task["title"] = m.group(1)
        elif m := _re.match(r"\s+created:\s*(.+)", line):
            task["created"] = m.group(1).strip()
        elif m := _re.match(r"\s+priority:\s*(.+)", line):
            task["priority"] = m.group(1).strip()
        elif m := _re.match(r"\s+status:\s*(.+)", line):
            task["status"] = m.group(1).strip()
        elif m := _re.match(r"\s+due:\s*(.+)", line):
            task["due"] = m.group(1).strip()
        elif m := _re.match(r"\s+notes:\s*\"(.+)\"", line):
            task["notes"] = m.group(1)
    return task


#
# ── Sessions ────────────────────────────────────────────────────────────
#

def load_recent_sessions(days: int) -> list[dict]:
    cutoff = (datetime.date.today() - datetime.timedelta(days=days)).isoformat()
    return get_db().execute(
        "SELECT * FROM sessions WHERE date >= ? ORDER BY date DESC", (cutoff,)
    ).fetchall()


def store_session(session_data: dict):
    db = get_db()
    db.execute(
        "INSERT OR REPLACE INTO sessions (id, date, skill, duration_min, rating, notes) VALUES (?, ?, ?, ?, ?, ?)",
        (session_data["id"], session_data["date"], session_data["skill"],
         session_data.get("duration_min", 0), session_data.get("rating", 0),
         session_data.get("notes", "")),
    )
    for decision in session_data.get("decisions", []):
        db.execute(
            "INSERT INTO session_decisions (session_id, decision) VALUES (?, ?)",
            (session_data["id"], decision),
        )
    db.commit()


def migrate_sessions_from_md() -> int:
    sessions_dir = MEM_DIR / "sessions"
    if not sessions_dir.exists():
        return 0
    db = get_db()
    existing = db.execute("SELECT COUNT(*) as c FROM sessions").fetchone()["c"]
    if existing > 0:
        return 0
    count = 0
    for fp in sorted(sessions_dir.glob("session-*.md")):
        text = fp.read_text(encoding="utf-8")
        data = {}
        decisions = []
        for line in text.splitlines():
            if line.startswith("id:"):
                data["id"] = line.split(":", 1)[1].strip().strip('"')
            elif line.startswith("date:"):
                data["date"] = line.split(":", 1)[1].strip().strip('"')
            elif line.startswith("skill:"):
                data["skill"] = line.split(":", 1)[1].strip().strip('"').strip(",")
            elif line.startswith("duration_min:"):
                val = line.split(":", 1)[1].strip().strip('"').strip(",")
                data["duration_min"] = int(val) if val.isdigit() else 0
            elif line.startswith("rating:"):
                val = line.split(":", 1)[1].strip().strip('"').strip(",")
                data["rating"] = int(val) if val.isdigit() else 0
            elif line.startswith("notes:"):
                data["notes"] = line.split(":", 1)[1].strip().strip("| ").strip('"')
            elif line.startswith("- decision:"):
                decisions.append(line.split(":", 1)[1].strip().strip('"'))
        if not data.get("id"):
            continue
        data["decisions"] = decisions
        store_session(data)
        count += 1
    return count


#
# ── Goals ───────────────────────────────────────────────────────────────
#

def load_goals() -> list[dict]:
    return get_db().execute("SELECT * FROM goals ORDER BY created DESC").fetchall()


def add_goal(goal_id: str, title: str, status: str = "active") -> dict:
    goal = {"id": goal_id, "title": title, "status": status, "created": datetime.date.today().isoformat()}
    get_db().execute(
        "INSERT INTO goals (id, title, status, created) VALUES (?, ?, ?, ?)",
        (goal["id"], goal["title"], goal["status"], goal["created"]),
    )
    get_db().commit()
    return goal


def migrate_goals_from_md() -> int:
    path = MEM_DIR / "goals.md"
    if not path.exists():
        return 0
    db = get_db()
    existing = db.execute("SELECT COUNT(*) as c FROM goals").fetchone()["c"]
    if existing > 0:
        return 0
    text = path.read_text(encoding="utf-8")
    count = 0
    buffer = []
    for line in text.split("\n"):
        if line.startswith("- id:"):
            if buffer:
                _insert_goal_from_md(buffer, db)
                count += 1
            buffer = [line]
        elif line.startswith("  ") and buffer:
            buffer.append(line)
    if buffer:
        _insert_goal_from_md(buffer, db)
        count += 1
    db.commit()
    return count


def _insert_goal_from_md(lines: list[str], db):
    import re as _re
    g = {}
    for line in lines:
        if m := _re.match(r"- id:\s*(.+)", line):
            g["id"] = m.group(1).strip()
        elif m := _re.match(r"\s+title:\s*\"(.+)\"", line):
            g["title"] = m.group(1)
        elif m := _re.match(r"\s+status:\s*(.+)", line):
            g["status"] = m.group(1).strip()
        elif m := _re.match(r"\s+created:\s*(.+)", line):
            g["created"] = m.group(1).strip()
    if g.get("id"):
        db.execute(
            "INSERT OR IGNORE INTO goals (id, title, status, created) VALUES (?, ?, ?, ?)",
            (g["id"], g.get("title", ""), g.get("status", "active"), g.get("created", "")),
        )


#
# ── Habits ──────────────────────────────────────────────────────────────
#

def load_habits() -> list[dict]:
    return get_db().execute("SELECT * FROM habits ORDER BY created DESC").fetchall()


def add_habit(habit_id: str, title: str, status: str = "active") -> dict:
    habit = {"id": habit_id, "title": title, "status": status, "streak": 0, "created": datetime.date.today().isoformat()}
    get_db().execute(
        "INSERT INTO habits (id, title, status, streak, created) VALUES (?, ?, ?, ?, ?)",
        (habit["id"], habit["title"], habit["status"], 0, habit["created"]),
    )
    get_db().commit()
    return habit


def migrate_habits_from_md() -> int:
    path = MEM_DIR / "habits.md"
    if not path.exists():
        return 0
    db = get_db()
    existing = db.execute("SELECT COUNT(*) as c FROM habits").fetchone()["c"]
    if existing > 0:
        return 0
    text = path.read_text(encoding="utf-8")
    count = 0
    buffer = []
    for line in text.split("\n"):
        if line.startswith("- id:"):
            if buffer:
                _insert_habit_from_md(buffer, db)
                count += 1
            buffer = [line]
        elif line.startswith("  ") and buffer:
            buffer.append(line)
    if buffer:
        _insert_habit_from_md(buffer, db)
        count += 1
    db.commit()
    return count


def _insert_habit_from_md(lines: list[str], db):
    import re as _re
    h = {}
    for line in lines:
        if m := _re.match(r"- id:\s*(.+)", line):
            h["id"] = m.group(1).strip()
        elif m := _re.match(r"\s+title:\s*\"(.+)\"", line):
            h["title"] = m.group(1)
        elif m := _re.match(r"\s+status:\s*(.+)", line):
            h["status"] = m.group(1).strip()
        elif m := _re.match(r"\s+streak:\s*(.+)", line):
            h["streak"] = int(m.group(1)) if m.group(1).isdigit() else 0
        elif m := _re.match(r"\s+created:\s*(.+)", line):
            h["created"] = m.group(1).strip()
    if h.get("id"):
        db.execute(
            "INSERT OR IGNORE INTO habits (id, title, status, streak, created) VALUES (?, ?, ?, ?, ?)",
            (h["id"], h.get("title", ""), h.get("status", "active"), h.get("streak", 0), h.get("created", "")),
        )


#
# ── Checkpoint ──────────────────────────────────────────────────────────
#

def get_checkpoint() -> dict:
    rows = get_db().execute("SELECT key, value FROM checkpoint").fetchall()
    return {r["key"]: r["value"] for r in rows}


def set_checkpoint(key: str, value: str):
    get_db().execute("INSERT OR REPLACE INTO checkpoint (key, value) VALUES (?, ?)", (key, value))
    get_db().commit()


def migrate_checkpoint_from_md() -> int:
    path = MEM_DIR / "checkpoint.md"
    if not path.exists():
        return 0
    db = get_db()
    existing = db.execute("SELECT COUNT(*) as c FROM checkpoint").fetchone()["c"]
    if existing > 0:
        return 0
    text = path.read_text(encoding="utf-8")
    count = 0
    for line in text.splitlines():
        if ":" in line and not line.startswith("---"):
            key, _, val = line.partition(":")
            key = key.strip()
            val = val.strip().strip('"')
            if key and val:
                db.execute("INSERT OR REPLACE INTO checkpoint (key, value) VALUES (?, ?)", (key, val))
                count += 1
    db.commit()
    return count


#
# ── Intent Corrections ──────────────────────────────────────────────────
#


def record_intent_correction(input_text: str, correct_mode: str, correct_intent: str = "general", notes: str = ""):
    db = get_db()
    existing = db.execute(
        "SELECT id, hit_count FROM intent_corrections WHERE input_pattern = ?", (input_text,)
    ).fetchone()
    utcnow = datetime.datetime.now(datetime.timezone.utc).isoformat()
    if existing:
        db.execute(
            "UPDATE intent_corrections SET hit_count = ?, notes = ? WHERE id = ?",
            (existing["hit_count"] + 1, notes, existing["id"]),
        )
    else:
        db.execute(
            "INSERT INTO intent_corrections (input_pattern, correct_mode, correct_intent, created, notes) VALUES (?, ?, ?, ?, ?)",
            (input_text, correct_mode, correct_intent, utcnow, notes),
        )
    db.commit()
    log_insight("intent_correction", {
        "input": input_text[:100],
        "mode": correct_mode,
        "intent": correct_intent,
    })


def get_intent_corrections() -> list[dict]:
    return get_db().execute(
        "SELECT * FROM intent_corrections ORDER BY hit_count DESC, created DESC"
    ).fetchall()


def match_intent_correction(input_text: str) -> dict | None:
    text = input_text.lower().strip()
    corrections = get_intent_corrections()
    for c in corrections:
        if c["input_pattern"].lower() == text:
            return {
                "mode": c["correct_mode"],
                "intent": c["correct_intent"],
                "confidence": 0.95,
            }
    for c in corrections:
        if c["input_pattern"].lower() in text or text in c["input_pattern"].lower():
            return {
                "mode": c["correct_mode"],
                "intent": c["correct_intent"],
                "confidence": 0.85,
            }
    return None


#
# ── Init ────────────────────────────────────────────────────────────────
#

def migrate_all():
    init_db()
    counts = {}
    counts["insight_ledger"] = migrate_insight_ledger_from_json()
    counts["tasks"] = migrate_tasks_from_md()
    counts["sessions"] = migrate_sessions_from_md()
    counts["goals"] = migrate_goals_from_md()
    counts["habits"] = migrate_habits_from_md()
    counts["checkpoint"] = migrate_checkpoint_from_md()
    return {k: v for k, v in counts.items() if v > 0}


if __name__ == "__main__":
    init_db()
    migrated = migrate_all()
    if migrated:
        print(f"Migrated: {migrated}")
    else:
        print("No new data to migrate.")
