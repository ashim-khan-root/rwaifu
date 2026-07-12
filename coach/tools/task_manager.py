"""Task manager: add, list, complete tasks with verification methods. Usage:
  py -3 coach/tools/task_manager.py add "<title>" [priority] [notes] [--verify METHOD]
  py -3 coach/tools/task_manager.py list [--all|--pending|--done|--overdue]
  py -3 coach/tools/task_manager.py done <id>
  py -3 coach/tools/task_manager.py delete <id>
  py -3 coach/tools/task_manager.py verify <id>     (run verification for a task)

Verification methods: CLI, Test, Static, Browser, Grep, Read, Custom
"""
import datetime, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from db import load_tasks, add_task as db_add_task, update_task_status, delete_task as db_delete_task
from db import init_db, migrate_tasks_from_md
from insight_ledger import log_insight


def _next_id(tasks):
    existing_ids = [t.get("id", "") for t in tasks]
    nums = []
    for eid in existing_ids:
        m = re.search(r"task-(\d+)", eid)
        if m:
            nums.append(int(m.group(1)))
    return f"task-{(max(nums) + 1) if nums else 1}"


def cmd_add(title, priority="medium", notes="", verify_method=""):
    tasks = load_tasks()
    new_id = _next_id(tasks)
    task = db_add_task(new_id, title, priority, notes, verify_method)
    vm = f" [verify: {task['verify_method']}]" if task.get("verify_method") else ""
    print(f"Task added: [{new_id}] {title} (priority: {task['priority']}){vm}")
    log_insight("task_added", {"task_id": new_id, "title": title[:60], "priority": task["priority"]})


def cmd_list(filter_mode="pending"):
    tasks = load_tasks()
    if not tasks:
        print("No tasks found.")
        return

    if filter_mode == "pending":
        tasks = [t for t in tasks if t.get("status") != "done"]
    elif filter_mode == "done":
        tasks = [t for t in tasks if t.get("status") == "done"]
    elif filter_mode == "overdue":
        today = datetime.date.today().isoformat()
        tasks = [t for t in tasks if t.get("due", "") and t["due"] < today and t.get("status") != "done"]

    if not tasks:
        print(f"No {filter_mode} tasks.")
        return

    for t in sorted(tasks, key=lambda x: {"high": 0, "medium": 1, "low": 2}.get(x.get("priority", "medium"), 3)):
        due = f" (due: {t['due']})" if t.get("due") else ""
        notes = f" -- {t['notes'][:40]}" if t.get("notes") else ""
        vm = f" [verify: {t['verify_method']}]" if t.get("verify_method") else ""
        print(f"  [{t['id']}] [{t.get('priority','?')}] {t.get('title','?')}{due}{vm}{notes}")


def cmd_done(task_id):
    update_task_status(task_id, "done")
    print(f"Task completed: {task_id}")
    log_insight("task_completed", {"task_id": task_id})


def cmd_delete(task_id):
    if db_delete_task(task_id):
        print(f"Task deleted: {task_id}")
        log_insight("task_deleted", {"task_id": task_id})
    else:
        log_insight("task_not_found", {"task_id": task_id})
        print(f"Task not found: {task_id}")


def cmd_verify(task_id):
    tasks = load_tasks()
    task = next((t for t in tasks if t["id"] == task_id), None)
    if not task:
        print(f"Task not found: {task_id}")
        return
    method = task.get("verify_method", "") or "Custom"
    print(f"=== Verify Task: {task['title']} ===")
    print(f"  ID: {task_id}")
    print(f"  Method: {method}")
    print(f"  Priority: {task.get('priority', 'medium')}")
    print(f"  Notes: {task.get('notes', '')[:100]}")
    print()
    print(f"To verify this task manually:")
    print(f"  1. Apply the {method} verification method")
    if method == "CLI":
        print("  2. Run the relevant command and check output")
    elif method == "Test":
        print("  2. Run `py -3 -m pytest coach/tests/ -v --tb=short`")
    elif method == "Grep":
        print("  2. Search files for the expected pattern")
    elif method == "Read":
        print("  2. Read the relevant file and validate structure")
    elif method == "Browser":
        print("  2. Open the page and verify behavior")
    else:
        print("  2. Follow the task-specific verification steps")
    print(f"  3. Run: task_manager.py done {task_id}")
    log_insight("task_verify", {"task_id": task_id, "method": method})


def main():
    init_db()
    migrate_tasks_from_md()

    import sys as _sys
    args = _sys.argv[1:]
    if not args:
        print(__doc__)
        _sys.exit(1)

    cmd = args[0]
    rest = args[1:]

    if cmd == "add":
        if not rest:
            print("Usage: task_manager.py add '<title>' [priority] [notes] [--verify METHOD]")
            _sys.exit(1)
        title = rest[0]
        priority = "medium"
        notes = ""
        verify_method = ""
        i = 1
        while i < len(rest):
            if rest[i] == "--verify" and i + 1 < len(rest):
                verify_method = rest[i + 1]
                i += 2
            elif rest[i] in ("low", "medium", "high"):
                priority = rest[i]
                i += 1
            else:
                notes = " ".join(rest[i:])
                break
        cmd_add(title, priority, notes, verify_method)
    elif cmd == "list":
        mode = rest[0] if rest else "pending"
        mode = mode.lstrip("-")
        cmd_list(mode)
    elif cmd == "done":
        if not rest:
            print("Usage: task_manager.py done <id>")
            _sys.exit(1)
        cmd_done(rest[0])
    elif cmd == "delete":
        if not rest:
            print("Usage: task_manager.py delete <id>")
            _sys.exit(1)
        cmd_delete(rest[0])
    elif cmd == "verify":
        if not rest:
            print("Usage: task_manager.py verify <id>")
            _sys.exit(1)
        cmd_verify(rest[0])
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)


if __name__ == "__main__":
    main()
