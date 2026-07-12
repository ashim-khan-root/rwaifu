"""Print current memory summary for the AI coach to read."""
import sys
import io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parent))
from db import init_db, load_recent_sessions, load_goals, load_habits

MEM_DIR = Path(__file__).resolve().parent.parent / "memory"
USER_DIR = Path(__file__).resolve().parent.parent / "user"

def read_md(file):
    if not file.exists():
        return ""
    text = file.read_text(encoding="utf-8")
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            text = text[end + 4:].lstrip()
    return text

def main(max_items=5):
    meta = read_md(MEM_DIR / "meta.md")
    resources = read_md(MEM_DIR / "resources.md")
    init_db()
    goals = load_goals()
    habits = load_habits()
    recent_sessions = load_recent_sessions(days=10)
    recent = []
    for s in recent_sessions[:max_items]:
        lines = []
        lines.append(f"date: {s.get('date', '')}")
        lines.append(f"skill: {s.get('skill', '')}")
        lines.append(f"duration_min: {s.get('duration_min', '')}")
        lines.append(f"rating: {s.get('rating', '')}")
        notes = s.get('notes', '')
        if notes:
            lines.append(f"notes: {notes}")
        recent.append("\n".join(lines))
    telos_path = USER_DIR / "telos.md"
    identity_path = USER_DIR / "identity.md"

    parts = []
    if identity_path.exists():
        parts.append("=== IDENTITY ===")
        text = identity_path.read_text(encoding="utf-8")
        for line in text.splitlines():
            if line.strip().startswith("- **"):
                parts.append(line.strip())
    if telos_path.exists():
        parts.append("=== TELOS ===")
        text = telos_path.read_text(encoding="utf-8")
        in_goals = False
        for line in text.splitlines():
            if line.startswith("## Goals"):
                in_goals = True
                parts.append("Active goals:")
            elif line.startswith("## "):
                in_goals = False
            elif in_goals and line.strip() and (line.strip().startswith("- ") or line.strip()[0].isdigit()):
                parts.append(f"  {line.strip()}")
    if meta:
        parts.append("=== META ===")
        parts.append(meta)
    if goals:
        parts.append("=== GOALS ===")
        for g in goals:
            parts.append(f"- {g['title']} ({g['status']})")
    if habits:
        parts.append("=== HABITS ===")
        for h in habits:
            parts.append(f"- {h['title']} ({h['status']})")
    if resources:
        parts.append("=== RESOURCES ===")
        parts.append(resources)
    if recent:
        parts.append("=== RECENT SESSIONS ===")
        parts.append("\n---\n".join(recent))
    print("\n\n".join(parts))

if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 5)
