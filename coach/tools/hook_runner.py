"""Event-driven hook system — generalized from PAI's hook architecture.
Fires named events across registered handlers in coach/hooks/.

Usage:
  py -3 coach/tools/hook_runner.py <event> [--data key=val ...]
  py -3 coach/tools/hook_runner.py list

Events:
  session:start    — Pre-session context assembly
  session:end      — Post-session analysis + index rebuild
  session:fail     — Session error/abort
  plan:create      — New plan created
  plan:complete    — Plan marked complete
  task:done        — Task completed
  insight:new      — New insight extracted
  reflection:save  — Structured reflection written
  error            — Unhandled error
"""
import sys, subprocess, json, datetime
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent.parent / "hooks"
TOOLS_DIR = HOOKS_DIR.parent / "tools"


def parse_data(args):
    data = {}
    for arg in args:
        if "=" in arg:
            k, v = arg.split("=", 1)
            data[k] = v
    return data


def list_hooks():
    hook_files = sorted(HOOKS_DIR.glob("*.py"))
    if not hook_files:
        print("No hooks registered in coach/hooks/")
        return
    print("Registered hooks:")
    for fp in hook_files:
        print(f"  {fp.stem}")


def fire_event(event, data=None):
    data = data or {}
    hook_files = sorted(HOOKS_DIR.glob("*.py"))
    matched = []

    for fp in hook_files:
        hook_name = fp.stem
        if hook_name.startswith("on_"):
            handler_event = hook_name[3:].replace("_", ":")
            if handler_event == event or handler_event == "any":
                matched.append(fp)

    if not matched:
        print(f"[hook_runner] No handlers for event '{event}'")
        return

    for fp in matched:
        try:
            result = subprocess.run(
                ["py", "-3", str(fp)],
                input=json.dumps({"event": event, "data": data, "timestamp": datetime.datetime.now().isoformat()}),
                capture_output=True, text=True, timeout=30,
                cwd=TOOLS_DIR.parent
            )
            if result.stdout.strip():
                print(f"[{fp.stem}] {result.stdout.strip()}")
            if result.stderr.strip():
                print(f"[{fp.stem}] {result.stderr.strip()}")
        except subprocess.TimeoutExpired:
            print(f"[{fp.stem}] Timed out after 30s")
        except Exception as e:
            print(f"[{fp.stem}] Error: {e}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "list":
        list_hooks()
        return

    data = parse_data(sys.argv[2:])
    fire_event(cmd, data)


if __name__ == "__main__":
    main()
