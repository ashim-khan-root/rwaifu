"""Component-based AGENTS.md builder.
Assembles coach/components/*.md into AGENTS.md in project root.

Usage:
  py -3 coach/tools/rebuild_agents.py
  py -3 coach/tools/rebuild_agents.py --watch   (auto-rebuild on component changes)
"""
import sys, os, time, re
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
COMPONENTS_DIR = BASE / "components"
AGENTS_PATH = BASE.parent / "AGENTS.md"


def sort_key(fp):
    m = re.match(r"(\d+)", fp.name)
    return int(m.group(1)) if m else 999


def rebuild():
    md_files = sorted(COMPONENTS_DIR.glob("*.md"), key=sort_key)
    if not md_files:
        print("No component files found in coach/components/")
        return False

    parts = []
    for fp in md_files:
        content = fp.read_text(encoding="utf-8").strip()
        if content:
            parts.append(content)

    output = "\n\n".join(parts) + "\n"
    AGENTS_PATH.write_text(output, encoding="utf-8")
    print(f"Assembled {len(md_files)} components -> {AGENTS_PATH}")
    return True


def watch():
    last_mtimes = {}
    while True:
        changed = False
        for fp in sorted(COMPONENTS_DIR.glob("*.md")):
            mtime = fp.stat().st_mtime
            if fp.name in last_mtimes and last_mtimes[fp.name] != mtime:
                print(f"[watch] {fp.name} changed, rebuilding...")
                changed = True
            last_mtimes[fp.name] = mtime
        if changed:
            rebuild()
        time.sleep(2)


if __name__ == "__main__":
    if "--watch" in sys.argv:
        print("Watching coach/components/ for changes...")
        rebuild()
        watch()
    else:
        rebuild()
