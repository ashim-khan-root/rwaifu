## SQLite Storage Architecture

All persistent data lives in `coach/memory/coach.db` (auto-generated, .gitignored). The schema is managed by `coach/tools/db.py`.

| Table | Domain | Migrated from |
|---|---|---|
| `insight_events` | Event logging (every tool) | `insight_ledger.json` |
| `tasks` | Task CRUD | `tasks.md` |
| `sessions` | Practice sessions | `sessions/*.md` |
| `session_decisions` | Decisions per session | inline in sessions |
| `goals` | Active goals | `goals.md` |
| `habits` | Tracked habits | `habits.md` |
| `checkpoint` | Key-value state | `checkpoint.md` |
| `prds` | PRD lifecycle tracking | — |

**Pattern:** `init_db()` once at entry, then use `db.get_db().execute(...)` or domain helpers. Markdown originals still exist as read-only fallback.

**Not migrated** (stay as markdown): daily notes, conversations, snapshots, insights.md, evolution suggestions, profile/meta/resources, site surveys, reports.
