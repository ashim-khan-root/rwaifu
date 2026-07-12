## Persistent Identity (TELOS)

Identity and TELOS files in `coach/user/` are loaded every session:

| File | Purpose |
|---|---|
| `coach/user/identity.md` | Who you are — name, role, stack, communication style |
| `coach/user/telos.md` | Mission, goals, beliefs, wisdom, mental models, narratives |

These are loaded by `session_hooks.py pre` and `read_context.py` at session start so I always have your context. Use `py -3 coach/tools/telos.py show --brief` to view or `py -3 coach/tools/telos.py update telos` to edit.
