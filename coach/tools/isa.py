"""Ideal State Artifact (ISA) management tool.
Inspired by PAI v5.0.0's ISA primitive -- one document, twelve sections, ID-stable criteria.

Usage:
  py -3 coach/tools/isa.py scaffold "<title>" [--tier E2] [--dir process/plans/active]
  py -3 coach/tools/isa.py check <path>
  py -3 coach/tools/isa.py reconcile <path>
  py -3 coach/tools/isa.py verify <path> --isc ISC-1 --pass
  py -3 coach/tools/isa.py verify <path> --isc ISC-1 --fail
  py -3 coach/tools/isa.py list [--dir process/plans/active]
"""
import sys, datetime, re, uuid, argparse
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_DIR = PROJECT_ROOT / "process" / "plans" / "active"
TEMPLATE = PROJECT_ROOT / "process" / "plans" / "_isa_template.md"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from db import init_db, get_db

TIER_REQUIREMENTS = {
    "E1": {"sections": ["goal", "criteria"], "label": "< 90s"},
    "E2": {"sections": ["problem", "vision", "goal", "criteria", "test_strategy"], "label": "< 15min"},
    "E3": {"sections": ["problem", "vision", "principles", "constraints", "goal", "criteria", "test_strategy", "features"], "label": "< 1h"},
    "E4": {"sections": "all", "label": "< 2h"},
    "E5": {"sections": "all", "label": "2h+"},
}

SECTION_MAP = {
    "problem": (1, "Problem"),
    "vision": (2, "Vision"),
    "out_of_scope": (3, "Out of Scope"),
    "principles": (4, "Principles"),
    "constraints": (5, "Constraints"),
    "goal": (6, "Goal"),
    "criteria": (7, "Criteria"),
    "test_strategy": (8, "Test Strategy"),
    "features": (9, "Features"),
    "decisions": (10, "Decisions"),
    "changelog": (11, "Changelog"),
    "verification": (12, "Verification"),
}


def init_isa_table():
    init_db()
    db = get_db()
    db.executescript("""
        CREATE TABLE IF NOT EXISTS isas (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            tier TEXT DEFAULT 'E2',
            status TEXT DEFAULT 'draft',
            created TEXT NOT NULL,
            updated TEXT NOT NULL,
            path TEXT,
            supersedes TEXT DEFAULT '',
            isc_count INTEGER DEFAULT 0,
            isc_passed INTEGER DEFAULT 0,
            isc_failed INTEGER DEFAULT 0
        );
    """)
    db.commit()


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"\s+", "-", text)
    return text[:60]


def parse_isc_section(content: str) -> list[dict]:
    criteria = []
    for line in content.splitlines():
        m = re.match(r"\s*-\s*\[\s*[ x]?\s*\]\s*(ISC-[\d.]+)\s*\[(\w+)\]\s*(.*?)(?:--\s*verify:\s*(\w+))?\s*$", line)
        if m:
            criteria.append({
                "id": m.group(1),
                "priority": m.group(2),
                "description": m.group(3).strip(),
                "method": m.group(4) or "custom",
                "status": "pass" if "[x]" in line.lower() else "fail" if line.strip().endswith("[FAIL]") else "pending",
            })
    return criteria


def next_isc_id(criteria: list[dict]) -> str:
    if not criteria:
        return "ISC-1"
    existing = sorted(criteria, key=lambda c: [int(x) if x.isdigit() else 0 for x in re.findall(r"[\d.]+", c["id"])])
    last = existing[-1]["id"]
    parts = last.split("-")
    if "." in parts[-1]:
        base, sub = parts[-1].split(".")
        return f"ISC-{int(base)}.{int(sub) + 1}"
    return f"ISC-{int(parts[-1]) + 1}"


def get_required_sections(tier: str) -> list[str]:
    if tier.upper() in TIER_REQUIREMENTS:
        req = TIER_REQUIREMENTS[tier.upper()]
        if req["sections"] == "all":
            return list(SECTION_MAP.keys())
        return req["sections"]
    return TIER_REQUIREMENTS["E2"]["sections"]


def scaffold(title: str, tier: str = "E2", target_dir: str = None) -> Path:
    init_isa_table()
    dir_path = Path(target_dir) if target_dir else DEFAULT_DIR
    dir_path.mkdir(parents=True, exist_ok=True)

    now = datetime.datetime.now()
    timestamp = now.strftime("%Y%m%d-%H%M%S")
    slug = slugify(title)
    filename = f"{slug}-{timestamp}.md"
    filepath = dir_path / filename
    isa_id = str(uuid.uuid4())[:8]

    if not TEMPLATE.exists():
        print(f"Error: template not found at {TEMPLATE}")
        sys.exit(1)

    template_content = TEMPLATE.read_text(encoding="utf-8")

    frontmatter = f"""---
title: "{title}"
created: "{now.strftime("%Y-%m-%d %H:%M")}"
status: draft
tier: {tier.upper()}
isa_id: "{isa_id}"
supersedes: ""
---"""

    content = re.sub(r"^---.*?---", frontmatter, template_content, flags=re.DOTALL)
    content = content.replace("<Title>", title)

    filepath.write_text(content, encoding="utf-8")

    db = get_db()
    db.execute(
        "INSERT OR REPLACE INTO isas (id, title, tier, status, created, updated, path) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (isa_id, title, tier.upper(), "draft", now.isoformat(), now.isoformat(), str(filepath)),
    )
    db.commit()

    print(f"ISA created: {filepath}")
    print(f"  ID:     {isa_id}")
    print(f"  Tier:   {tier.upper()} ({TIER_REQUIREMENTS[tier.upper()]['label']})")
    print(f"  Status: draft")

    required = get_required_sections(tier.upper())
    print(f"  Required sections ({len(required)}): {', '.join(s.title() for s in required)}")
    print(f"  Optional: {', '.join(s.title() for s in SECTION_MAP if s not in required)}")

    return filepath


def check_completeness(path: str) -> dict:
    filepath = Path(path)
    if not filepath.exists():
        print(f"Error: file not found: {path}")
        sys.exit(1)

    content = filepath.read_text(encoding="utf-8")

    tier_match = re.search(r"tier:\s*(\S+)", content)
    tier = tier_match.group(1).upper() if tier_match else "E2"

    required = get_required_sections(tier)

    results = {"tier": tier, "required": [], "optional": [], "criteria": [], "score": 0, "total": 0}
    section_found = {s: False for s in SECTION_MAP}

    for key, (num, name) in SECTION_MAP.items():
        pattern = rf"##\s*{num}\.\s*{re.escape(name)}"
        found = bool(re.search(pattern, content))
        section_found[key] = found

        entry = {"section": name, "key": key, "required": key in required, "found": found}
        if key in required:
            results["required"].append(entry)
        else:
            results["optional"].append(entry)

    results["criteria"] = parse_isc_section(content)

    results["total"] = len(required)
    results["score"] = sum(1 for e in results["required"] if e["found"])

    return results


def cmd_check(path: str):
    results = check_completeness(path)
    print(f"\nISA Check: {Path(path).name}")
    print(f"  Tier: {results['tier']}")
    print(f"  Score: {results['score']}/{results['total']} required sections\n")

    all_good = True
    for entry in results["required"]:
        status = "[x]" if entry["found"] else "[ ]"
        if not entry["found"]:
            all_good = False
        print(f"  {status} [{entry['key']}] {entry['section']}")

    if results["optional"]:
        print()
        for entry in results["optional"]:
            status = "+" if entry["found"] else "."
            print(f"  {status} [{entry['key']}] {entry['section']} (optional)")

    print(f"\n  Criteria: {len(results['criteria'])} found")
    for c in results["criteria"]:
        icon = {"pass": "[x]", "fail": "[!]", "pending": "[ ]"}.get(c["status"], "[ ]")
        print(f"    {icon} {c['id']} [{c['priority']}] {c['description'][:60]}")

    if all_good and results["score"] == results["total"]:
        print(f"\n  [OK] All required sections present for tier {results['tier']}")
    else:
        print(f"\n  [!] Missing {results['total'] - results['score']} required section(s). Complete them before EXECUTE.")
    return all_good


def reconcile(path: str):
    filepath = Path(path)
    if not filepath.exists():
        print(f"Error: not found: {path}")
        sys.exit(1)

    content = filepath.read_text(encoding="utf-8")

    criteria = parse_isc_section(content)
    if not criteria:
        print("No ISC criteria found. Nothing to reconcile.")
        return

    expected = [f"ISC-{i}" for i in range(1, len(criteria) + 1)]
    actual = [c["id"] for c in criteria]

    if expected == actual:
        print("[OK] No reconciliation needed.")
        return

    renumber_map = {}
    for i, c in enumerate(criteria, 1):
        old = c["id"]
        new = f"ISC-{i}"
        if old != new:
            renumber_map[old] = new

    if not renumber_map:
        print("[OK] No gaps to fix.")
        return

    print(f"Renumbering {len(renumber_map)} criteria:")
    for old, new in renumber_map.items():
        content = content.replace(old, new)
        print(f"  {old} -> {new}")

    filepath.write_text(content, encoding="utf-8")
    print("[OK] Reconciled.")


def verify_isc(path: str, isc_id: str, status: str):
    filepath = Path(path)
    if not filepath.exists():
        print(f"Error: not found: {path}")
        sys.exit(1)

    content = filepath.read_text(encoding="utf-8")
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    if status == "pass":
        old = f"[ ] {isc_id}"
        new = f"[x] {isc_id}"
        if old in content:
            content = content.replace(old, new)
        content = content.replace(f"| {isc_id} | [ ] Pending |", f"| {isc_id} | [OK] Pass | {now} |")
    else:
        content = content.replace(f"| {isc_id} | [ ] Pending |", f"| {isc_id} | [FAIL] Fail | {now} |")

    filepath.write_text(content, encoding="utf-8")

    isa_id_m = re.search(r'isa_id:\s*"([^"]+)"', content)
    if isa_id_m:
        db = get_db()
        field = "isc_passed" if status == "pass" else "isc_failed"
        db.execute(f"UPDATE isas SET {field} = {field} + 1, updated = ? WHERE id = ?",
                   (datetime.datetime.now().isoformat(), isa_id_m.group(1)))
        db.commit()

    print(f"[OK] {isc_id} marked as {status}")


def list_isas(target_dir: str = None):
    dir_path = Path(target_dir) if target_dir else DEFAULT_DIR
    if not dir_path.exists():
        print(f"No ISAs found in {dir_path}")
        return

    files = sorted(dir_path.glob("*.md"))

    init_isa_table()
    db = get_db()

    print(f"\nISAs in {dir_path}:\n")
    for f in files:
        content = f.read_text(encoding="utf-8")
        title_m = re.search(r'title:\s*"([^"]+)"', content)
        tier_m = re.search(r"tier:\s*(\S+)", content)
        status_m = re.search(r"status:\s*(\S+)", content)
        criteria = parse_isc_section(content)
        passed = sum(1 for c in criteria if c["status"] == "pass")
        failed = sum(1 for c in criteria if c["status"] == "fail")

        title = title_m.group(1) if title_m else f.name
        tier = tier_m.group(1) if tier_m else "?"
        status = status_m.group(1) if status_m else "?"
        print(f"  {status} [{tier}] {title}")
        print(f"    File: {f.name}")
        print(f"    Criteria: {len(criteria)} ({passed} pass, {failed} fail)")
        print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ideal State Artifact (ISA) management")
    sub = parser.add_subparsers(dest="command")

    p_scaffold = sub.add_parser("scaffold", help="Create a new ISA")
    p_scaffold.add_argument("title", help="ISA title")
    p_scaffold.add_argument("--tier", default="E2", choices=["E1", "E2", "E3", "E4", "E5"])
    p_scaffold.add_argument("--dir", default=str(DEFAULT_DIR))

    p_check = sub.add_parser("check", help="Check ISA completeness")
    p_check.add_argument("path", help="Path to ISA file")

    p_reconcile = sub.add_parser("reconcile", help="Reconcile ISC numbering")
    p_reconcile.add_argument("path", help="Path to ISA file")

    p_verify = sub.add_parser("verify", help="Mark ISC as pass/fail")
    p_verify.add_argument("path", help="Path to ISA file")
    p_verify.add_argument("--isc", required=True, help="ISC ID (e.g., ISC-1)")
    p_verify.add_argument("--pass", dest="status_pass", action="store_true", help="Mark as passed")
    p_verify.add_argument("--fail", dest="status_fail", action="store_true", help="Mark as failed")

    p_list = sub.add_parser("list", help="List ISAs")
    p_list.add_argument("--dir", default=str(DEFAULT_DIR))

    args = parser.parse_args()

    if args.command == "scaffold":
        scaffold(args.title, args.tier, args.dir)
    elif args.command == "check":
        cmd_check(args.path)
    elif args.command == "reconcile":
        reconcile(args.path)
    elif args.command == "verify":
        if args.status_pass:
            verify_isc(args.path, args.isc, "pass")
        elif args.status_fail:
            verify_isc(args.path, args.isc, "fail")
        else:
            print("Specify --pass or --fail")
            sys.exit(1)
    elif args.command == "list":
        list_isas(args.dir)
    else:
        parser.print_help()
