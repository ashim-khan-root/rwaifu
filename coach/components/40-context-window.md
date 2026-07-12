## Context Window Management (200K tokens)
Snapshot at logical boundaries and when 25+ exchanges deep:
```bash
py -3 coach/tools/save_context_snapshot.py "<task>" "<files>" "<decisions>" "<next>"
```
Restore: `py -3 coach/tools/load_context_snapshot.py`
