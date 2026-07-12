"""Export personal-coach memory (SQLite) into an Open Knowledge Format (OKF) bundle.

Usage:
  py -3 coach/tools/okf_export.py build [--out PATH] [--pretty]

Produces a portable, human- and agent-readable directory of markdown files
with YAML frontmatter under the output path (default: coach/memory/okf).
"""
import argparse
import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from db import DB_PATH, SCHEMA_VERSION, init_db

OKF_DIR = Path(__file__).resolve().parent.parent / "okf"


def _dict_factory(cursor, row):
    return {col[0]: row[i] for i, col in enumerate(cursor.description)}


def get_db(dbfile=None):
    path = dbfile or DB_PATH
    conn = sqlite3.connect(str(path))
    conn.row_factory = _dict_factory
    return conn


def export_table(db, name, pretty=False):
    cols = [c["name"] for c in db.execute(f"PRAGMA table_info({name})").fetchall()]
    order_col = "created" if "created" in cols else ("id" if "id" in cols else cols[0])
    order_dir = "DESC" if order_col in ("created", "id") else "ASC"
    rows = db.execute(f"SELECT * FROM {name} ORDER BY {order_col} {order_dir}").fetchall()
    if not rows:
        return None
    lines = []
    for r in rows:
        rid = r.get("id") or r.get("key") or ""
        lines.append("---")
        lines.append(f"type: {name[:-1].title() if name.endswith('s') else name.title()}")
        lines.append(f"id: okf-{name}-{rid}")
        lines.append(f"created: {r.get('created', r.get('date', r.get('timestamp', '')))}")
        lines.append("---")
        lines.append("")
        for k, v in r.items():
            if v is None:
                v = ""
            v_str = str(v) if not isinstance(v, str) else v
            if pretty and len(v_str) > 80:
                lines.append(f"**{k}:**")
                lines.append("")
                lines.append(v_str)
                lines.append("")
            else:
                lines.append(f"- **{k}:** {v_str}")
        lines.append("")
    return "\n".join(lines)


def build(out_dir=None, pretty=False):
    out = Path(out_dir or OKF_DIR)
    out.mkdir(parents=True, exist_ok=True)
    db = get_db()

    skip = {"schema_version", "sqlite_sequence"}
    tables = [
        n["name"] for n in
        db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
        if n["name"] not in skip
    ]
    exports = []
    for t in tables:
        content = export_table(db, t, pretty=pretty)
        if content:
            (out / f"{t}.md").write_text(content, encoding="utf-8")
            exports.append(t)

    db.close()

    index = ["---",
             "type: Bundle",
             "id: okf-export",
             f"version: {SCHEMA_VERSION}",
             f"created: {datetime.now().strftime('%Y-%m-%d')}",
             f"description: SQLite export of {len(exports)} tables",
             "---",
             "",
             "# OKF Export",
             "",
             f"Auto-generated on {datetime.now().isoformat()}",
             "",
             "## Tables",
             ""]
    for t in exports:
        index.append(f"- `{t}.md`")
    index.append("")
    index.append(f"Schema version: {SCHEMA_VERSION}")
    (out / "export-index.md").write_text("\n".join(index), encoding="utf-8")
    print(f"Exported {len(exports)} tables to {out.resolve()}")
    return 0


def main():
    p = argparse.ArgumentParser(description="Export SQLite to OKF bundle")
    sub = p.add_subparsers(dest="command")
    b = sub.add_parser("build", help="Build OKF export")
    b.add_argument("--out", type=str, default=None, help="Output directory")
    b.add_argument("--pretty", action="store_true", help="Prettier multi-line values")
    args = p.parse_args()

    if args.command == "build":
        return build(out_dir=args.out, pretty=args.pretty)
    p.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
