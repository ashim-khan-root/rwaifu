import sys
import os
import uuid
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools.db import get_db


def add_task(title, priority="medium", notes="", category="general", due=""):
    db = get_db()
    task_id = str(uuid.uuid4())[:8]
    now = datetime.now().isoformat()
    db.execute(
        "INSERT INTO tasks (id, title, created, priority, status, due, notes, category) VALUES (?, ?, ?, ?, 'pending', ?, ?, ?)",
        (task_id, title, now, priority, due, notes, category),
    )
    db.commit()
    return task_id


def list_tasks(status=None):
    db = get_db()
    if status:
        cur = db.execute("SELECT * FROM tasks WHERE status=? ORDER BY created DESC", (status,))
    else:
        cur = db.execute("SELECT * FROM tasks ORDER BY created DESC")
    return cur.fetchall()


def done_task(task_id):
    db = get_db()
    db.execute("UPDATE tasks SET status='done' WHERE id=?", (task_id,))
    db.commit()


def delete_task(task_id):
    db = get_db()
    db.execute("DELETE FROM tasks WHERE id=?", (task_id,))
    db.commit()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["add", "list", "done", "delete"])
    parser.add_argument("--title", default="")
    parser.add_argument("--priority", default="medium")
    parser.add_argument("--notes", default="")
    parser.add_argument("--category", default="general")
    parser.add_argument("--id", default="")
    args = parser.parse_args()

    if args.action == "add":
        tid = add_task(args.title, args.priority, args.notes, args.category)
        print(f"Task added: {tid}")
    elif args.action == "list":
        for t in list_tasks():
            print(f"  [{t['status']}] {t['id']}: {t['title']} ({t['priority']})")
    elif args.action == "done":
        done_task(args.id)
        print(f"Task {args.id} done")
    elif args.action == "delete":
        delete_task(args.id)
        print(f"Task {args.id} deleted")
