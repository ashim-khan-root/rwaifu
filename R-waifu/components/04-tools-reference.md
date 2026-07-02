## Tools Reference

| Tool | Purpose | Usage |
|---|---|---|
| `db.py` | SQLite storage (init, schema) | Imported by all tools |
| `session_hooks.py` | Pre/post session context | `py -3 tools/session_hooks.py` |
| `store_session.py` | Log session summary | `py -3 tools/store_session.py <title>` |
| `read_context.py` | Show recent context | `py -3 tools/read_context.py [n]` |
| `insight_ledger.py` | Memory + insight CRUD | `py -3 -c "from tools.insight_ledger import *"` |
| `task_manager.py` | Task CRUD | `py -3 tools/task_manager.py add/list/done/delete` |
| `context_snapshot.py` | Save/load snapshots | `py -3 -c "from tools.context_snapshot import *"` |
| `isa.py` | Goal tracking (ISA) | `py -3 -c "from tools.isa import *"` |
| `extract_insights.py` | Pattern extraction | `py -3 tools/extract_insights.py` |
| `hook_runner.py` | Event-driven hooks | `py -3 -c "from tools.hook_runner import run_hooks"` |
| `qwen_inference.py` | Local LLM inference | `py -3 tools/qwen_inference.py` |
