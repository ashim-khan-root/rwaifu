## Memory System

### Storage
- **SQLite** via `tools/db.py` (5 tables: memories, sessions, interactions, insights, events)
- File location: `memory/rwaifu.db`

### Memory Types
| Type | Table | Purpose |
|---|---|---|
| Long-term | `memories` | Important facts with importance scoring |
| Session | `sessions` | Per-session metadata |
| Interaction | `interactions` | User input / response pairs |
| Insight | `insights` | Learned patterns with confidence scores |
| Event | `events` | All system events with JSON payloads |

### Adding Memories
```python
from tools.insight_ledger import add_memory, add_insight, log_event
add_memory("User prefers concise answers", category="preference", importance=3)
add_insight("User asks most questions in the evening", category="pattern", confidence=0.7)
log_event("milestone:first_project", {"project": "R-waifu"})
```
