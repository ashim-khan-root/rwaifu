## Session Lifecycle

### Start
- Run `py -3 tools/session_hooks.py` (or via `hook_runner.py`)
- Read recent context: `py -3 tools/read_context.py 5`
- Check active goals and tasks

### During
- Store important memories via `insight_ledger.add_memory()`
- Log meaningful events via `insight_ledger.log_event()`
- Track tasks via `task_manager.py`

### End
- Run `py -3 tools/store_session.py "<title>" --duration <min> --rating <1-10> --mood <mood> --notes "<notes>"`
- Insights are extracted automatically
- Save context snapshot if >25 exchanges deep
