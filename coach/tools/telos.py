"""TELOS identity management — mission, goals, beliefs, wisdom.

Usage:
  py -3 coach/tools/telos.py show              # Show full TELOS
  py -3 coach/tools/telos.py show --brief      # Brief summary
  py -3 coach/tools/telos.py update telos      # Edit TELOS file
  py -3 coach/tools/telos.py update identity   # Edit identity file
  py -3 coach/tools/telos.py init              # Init from existing profile.md
"""
import sys, datetime, subprocess, argparse
from pathlib import Path

USER_DIR = Path(__file__).resolve().parent.parent / "user"
MEM_DIR = Path(__file__).resolve().parent.parent / "memory"


def read_file(path: Path, strip_yaml: bool = False) -> str:
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8")
    if strip_yaml and text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            text = text[end + 4:].lstrip()
    return text


def show(brief: bool = False):
    identity_path = USER_DIR / "identity.md"
    telos_path = USER_DIR / "telos.md"

    identity = read_file(identity_path)
    telos = read_file(telos_path)

    if not identity and not telos:
        print("TELOS not initialized. Run: py -3 coach/tools/telos.py init")
        return

    if brief:
        identity = read_file(identity_path, strip_yaml=True)
        telos = read_file(telos_path, strip_yaml=True)
        print("=== IDENTITY ===")
        for line in identity.splitlines():
            if line.startswith("- **"):
                print(f"  {line}")
        print()
        print("=== TELOS (brief) ===")
        in_section = False
        for line in telos.splitlines():
            if line.startswith("## "):
                in_section = True
                print(f"\n  {line}")
            elif in_section and line.strip() and not line.startswith("#"):
                print(f"    {line.strip()}")
        return

    if identity:
        print("=" * 50)
        print(read_file(identity_path, strip_yaml=True))
    if telos:
        print("=" * 50)
        print(read_file(telos_path, strip_yaml=True))
    print("=" * 50)


def init_from_profile():
    """Seed TELOS from existing profile.md and goals.md."""
    profile_path = MEM_DIR / "profile.md"
    goals_path = MEM_DIR / "goals.md"

    profile = read_file(profile_path)
    goals = read_file(goals_path)

    identity_path = USER_DIR / "identity.md"
    telos_path = USER_DIR / "telos.md"

    if identity_path.exists() and telos_path.exists():
        print("TELOS already initialized. Edit files directly or use 'update'.")
        return

    if not identity_path.exists():
        print("Creating identity.md from profile.md...")
        lines = ["# User Identity", "", "## Basics", ""]
        role = "Engineer"
        for line in profile.splitlines():
            if line.startswith("**Role:**"):
                role = line.split(":", 1)[1].strip().strip("*")
            if line.startswith("**Known languages:**"):
                langs = line.split(":", 1)[1].strip()
                lines.append(f"- **Stack:** {langs}")
        lines.append(f"- **Name:** Ashim")
        lines.append(f"- **Role:** {role}")
        lines.append("")
        lines.append("## About")
        lines.append("")
        for line in profile.splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("---") and not stripped.startswith("**"):
                lines.append(stripped)
        identity_path.write_text("\n".join(lines), encoding="utf-8")
        print(f"  -> {identity_path}")

    if not telos_path.exists():
        print("Creating telos.md from goals.md...")
        lines = ["# TELOS — Mission, Goals, Beliefs", "", "## Mission", "", "## Goals", ""]
        if goals:
            for line in goals.splitlines():
                m = __import__("re").match(r"\s*title:\s*\"(.+)\"", line)
                if m:
                    lines.append(f"- {m.group(1)}")
        lines.append("")
        lines.append("## Beliefs")
        lines.append("")

        # Extract from profile
        for line in profile.splitlines():
            stripped = line.strip()
            if stripped.startswith("**Aspiration:**") or stripped.startswith("**Learning style:**"):
                lines.append(stripped)

        telos_path.write_text("\n".join(lines), encoding="utf-8")
        print(f"  -> {telos_path}")

    print("Done. Edit files in coach/user/ to refine.")


def open_editor(path: str):
    filepath = USER_DIR / path
    if not filepath.exists():
        print(f"File not found: {filepath}")
        return
    try:
        subprocess.run(["notepad.exe", str(filepath)], check=True)
    except (subprocess.SubprocessError, FileNotFoundError):
        print(f"Open this file to edit: {filepath}")


def get_context_block() -> str:
    """Return TELOS block for session context injection."""
    identity = read_file(USER_DIR / "identity.md")
    telos = read_file(USER_DIR / "telos.md")

    parts = []
    if identity:
        for line in identity.splitlines():
            if line.startswith("## "):
                parts.append(line[2:].strip())

        parts.append("")

    if telos:
        in_goals = False
        for line in telos.splitlines():
            if line.startswith("## Goals"):
                in_goals = True
                parts.append("Goals:")
            elif line.startswith("## "):
                in_goals = False
            elif in_goals and line.strip().startswith("- "):
                parts.append(f"  {line.strip()}")

    return "\n".join(parts)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TELOS identity management")
    sub = parser.add_subparsers(dest="command")

    p_show = sub.add_parser("show", help="Show TELOS identity")
    p_show.add_argument("--brief", action="store_true", help="Brief summary")

    p_update = sub.add_parser("update", help="Edit TELOS or identity file")
    p_update.add_argument("target", choices=["telos", "identity"])

    p_init = sub.add_parser("init", help="Initialize from existing profile.md")

    args = parser.parse_args()

    if args.command == "show":
        show(args.brief)
    elif args.command == "update":
        open_editor(f"{args.target}.md")
    elif args.command == "init":
        init_from_profile()
    else:
        parser.print_help()
