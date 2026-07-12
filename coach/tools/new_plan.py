"""Create a new coaching plan from template with PRD lifecycle. Usage:
  python tools/new_plan.py "<title>"
  python tools/new_plan.py "<title>" --prd     (create with PRD lifecycle tracking)
Saves to process/plans/active/<slug>-YYYYMMDD-HHMMSS.md
"""
import sys, datetime, re, uuid
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
PLANS_DIR = PROJECT_ROOT / "process" / "plans" / "active"
COMPLETED_DIR = PROJECT_ROOT / "process" / "plans" / "completed"
BACKLOG_DIR = PROJECT_ROOT / "process" / "plans" / "backlog"
TEMPLATE = PROJECT_ROOT / "process" / "plans" / "_template.md"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from db import init_db, get_db


PRD_STATUSES = ["DRAFT", "CRITERIA_DEFINED", "PLANNED", "IN_PROGRESS", "VERIFYING", "COMPLETE"]


def init_prd_table():
    init_db()
    db = get_db()
    db.executescript("""
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
    """)
    db.commit()


def create_prd(title, plan_path):
    init_prd_table()
    db = get_db()
    prd_id = f"prd_{uuid.uuid4().hex[:8]}"
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    db.execute(
        "INSERT INTO prds (id, title, status, created, updated, plan_path) VALUES (?, ?, ?, ?, ?, ?)",
        (prd_id, title, "DRAFT", now, now, str(plan_path)),
    )
    db.commit()
    return prd_id


def list_prds(status=None):
    init_prd_table()
    db = get_db()
    if status:
        rows = db.execute("SELECT * FROM prds WHERE status = ? ORDER BY updated DESC", (status,)).fetchall()
    else:
        rows = db.execute("SELECT * FROM prds ORDER BY updated DESC").fetchall()
    return rows


def update_prd_status(prd_id, new_status):
    init_prd_table()
    if new_status not in PRD_STATUSES:
        print(f"Invalid PRD status: {new_status}. Valid: {', '.join(PRD_STATUSES)}")
        return False
    db = get_db()
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    db.execute("UPDATE prds SET status = ?, updated = ? WHERE id = ?", (new_status, now, prd_id))
    db.commit()
    return True


def update_prd_criteria(prd_id, criteria, verification_method=""):
    init_prd_table()
    db = get_db()
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    db.execute("UPDATE prds SET criteria = ?, verification_method = ?, updated = ? WHERE id = ?",
               (criteria, verification_method, now, prd_id))
    db.commit()


def main():
    if len(sys.argv) < 2:
        print("Usage: python tools/new_plan.py '<title>' [--prd]")
        print("       python tools/new_plan.py --list-prds [status]")
        print("       python tools/new_plan.py --prd-status <id> <new_status>")
        sys.exit(1)

    if sys.argv[1] == "--list-prds":
        status = sys.argv[2] if len(sys.argv) > 2 else None
        prds = list_prds(status)
        if not prds:
            print("No PRDs found.")
            return
        print(f"{'ID':<20} {'Title':<30} {'Status':<20} {'Updated':<25}")
        print("-" * 95)
        for p in prds:
            print(f"{p['id']:<20} {p['title']:<30} {p['status']:<20} {p['updated'][:19]:<25}")
        return

    if sys.argv[1] == "--prd-status":
        if len(sys.argv) < 4:
            print("Usage: new_plan.py --prd-status <id> <new_status>")
            sys.exit(1)
        if update_prd_status(sys.argv[2], sys.argv[3].upper()):
            print(f"PRD {sys.argv[2]} → {sys.argv[3].upper()}")
        return

    title = sys.argv[1]
    use_prd = "--prd" in sys.argv
    now = datetime.datetime.now(datetime.timezone.utc)
    slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')
    filename = f"{slug}-{now.strftime('%Y%m%d-%H%M%S')}.md"
    filepath = PLANS_DIR / filename

    if TEMPLATE.exists():
        content = TEMPLATE.read_text(encoding="utf-8")
        content = content.replace('title: ""', f'title: "{title}"')
        content = content.replace('created: ""', f'created: "{now.isoformat()}"')
    else:
        content = f"""---
title: "{title}"
created: "{now.isoformat()}"
status: active
phase: research
prd_id: ""
---

## Objective

## Approach

## Deliverables

## ISC Criteria
<!-- Ideal State Criteria — one per line with verification method:
     # [PRIORITY] description — verify: <method> -->
1. [CRITICAL]
2. [HIGH]
3. [MEDIUM]

## Anti-Criteria
<!-- What we explicitly do NOT want -->

## Success Criteria

## Verification Methods
<!-- How each criterion will be verified:
     CLI | Test | Static | Browser | Grep | Read | Custom -->

## Resources

## Notes
"""

    if use_prd:
        prd_id = create_prd(title, filepath)
        content = content.replace('prd_id: ""', f'prd_id: "{prd_id}"')
        print(f"PRD created: {prd_id} (status: DRAFT)")

    PLANS_DIR.mkdir(parents=True, exist_ok=True)
    filepath.write_text(content, encoding="utf-8")
    print(f"Plan created: {filepath}")

    if use_prd:
        update_prd_status(prd_id, "CRITERIA_DEFINED")
        print(f"PRD {prd_id} -> CRITERIA_DEFINED")


if __name__ == "__main__":
    main()
