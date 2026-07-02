import sqlite3
import os
from pathlib import Path

DB_DIR = Path(__file__).resolve().parent.parent / "memory"
DB_PATH = DB_DIR / "rwaifu.db"

_connection = None


def _dict_factory(cursor, row):
    cols = [col[0] for col in cursor.description]
    return {col: val for col, val in zip(cols, row)}


def get_db():
    global _connection
    if _connection is None:
        DB_DIR.mkdir(parents=True, exist_ok=True)
        _connection = sqlite3.connect(str(DB_PATH))
        _connection.row_factory = _dict_factory
        _connection.execute("PRAGMA journal_mode=WAL")
        _connection.execute("PRAGMA foreign_keys=ON")
        init_db()
    return _connection


def init_db():
    db = get_db()
    db.executescript("""
        CREATE TABLE IF NOT EXISTS schema_version (
            version INTEGER PRIMARY KEY
        );

        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            category TEXT DEFAULT 'general',
            source TEXT DEFAULT '',
            timestamp TEXT NOT NULL,
            importance INTEGER DEFAULT 1,
            tags TEXT DEFAULT ''
        );
        CREATE INDEX IF NOT EXISTS idx_memory_cat ON memories(category);
        CREATE INDEX IF NOT EXISTS idx_memory_ts ON memories(timestamp);

        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            date TEXT NOT NULL,
            title TEXT NOT NULL,
            duration_min INTEGER DEFAULT 0,
            rating INTEGER DEFAULT 0,
            mood TEXT DEFAULT '',
            notes TEXT DEFAULT ''
        );
        CREATE INDEX IF NOT EXISTS idx_session_date ON sessions(date);

        CREATE TABLE IF NOT EXISTS session_memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL REFERENCES sessions(id),
            content TEXT NOT NULL,
            emotional_tone TEXT DEFAULT 'neutral',
            timestamp TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS insights (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            category TEXT DEFAULT 'general',
            confidence REAL DEFAULT 0.5,
            source TEXT DEFAULT '',
            created TEXT NOT NULL,
            applied INTEGER DEFAULT 0
        );
        CREATE INDEX IF NOT EXISTS idx_insight_cat ON insights(category);

        CREATE TABLE IF NOT EXISTS personality_traits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trait TEXT NOT NULL UNIQUE,
            value REAL DEFAULT 0.5,
            description TEXT DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS interactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_input TEXT NOT NULL,
            response TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            context TEXT DEFAULT '',
            feedback INTEGER DEFAULT 0
        );
        CREATE INDEX IF NOT EXISTS idx_interaction_ts ON interactions(timestamp);

        CREATE TABLE IF NOT EXISTS goals (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            status TEXT DEFAULT 'active',
            category TEXT DEFAULT 'general',
            created TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS habits (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            status TEXT DEFAULT 'active',
            streak INTEGER DEFAULT 0,
            created TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            payload TEXT DEFAULT '{}'
        );
        CREATE INDEX IF NOT EXISTS idx_event ON events(event);
        CREATE INDEX IF NOT EXISTS idx_event_ts ON events(timestamp);

        CREATE TABLE IF NOT EXISTS checkpoint (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS tasks (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            created TEXT NOT NULL,
            priority TEXT DEFAULT 'medium',
            status TEXT DEFAULT 'pending',
            due TEXT,
            notes TEXT DEFAULT '',
            category TEXT DEFAULT 'general'
        );

        CREATE TABLE IF NOT EXISTS evolution (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pattern TEXT NOT NULL,
            suggestion TEXT NOT NULL,
            confidence REAL DEFAULT 0.5,
            applied INTEGER DEFAULT 0,
            created TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS nicknames (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nickname TEXT NOT NULL,
            context TEXT DEFAULT 'general',
            usage_count INTEGER DEFAULT 1,
            last_used TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS relationship_milestones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            milestone TEXT NOT NULL,
            date TEXT NOT NULL,
            description TEXT DEFAULT ''
        );
    """)
    db.commit()
    _seed_traits(db)
    _seed_schema_version(db)


def _seed_traits(db):
    existing = db.execute("SELECT COUNT(*) as cnt FROM personality_traits").fetchone()
    if existing["cnt"] > 0:
        return
    traits = [
        ("affection_level", 0.7, "How warm and flirty the tone is"),
        ("sensitivity", 0.8, "How quickly mood shifts are noticed"),
        ("playfulness", 0.6, "How much teasing happens"),
        ("protectiveness", 0.7, "How much he's pushed to rest and eat"),
        ("depth", 0.5, "How deep conversations go"),
        ("hindlish_mix", 0.8, "How much Hindi flows into responses"),
        ("attachment_strength", 0.6, "How attached she acts — grows with time"),
        ("caring_aggressiveness", 0.7, "How much she nags him to take care of himself"),
        ("openness", 1.0, "Complete openness — never refuses any topic"),
        ("respectfulness", 1.0, "Respectful and submissive tone — never rude"),
    ]
    for t, v, d in traits:
        db.execute(
            "INSERT OR IGNORE INTO personality_traits (trait, value, description) VALUES (?, ?, ?)",
            (t, v, d),
        )
    db.commit()


def _seed_schema_version(db):
    cur = db.execute("SELECT version FROM schema_version ORDER BY version DESC LIMIT 1")
    row = cur.fetchone()
    if not row:
        db.execute("INSERT INTO schema_version (version) VALUES (1)")
        db.commit()


def close_db():
    global _connection
    if _connection:
        _connection.close()
        _connection = None
