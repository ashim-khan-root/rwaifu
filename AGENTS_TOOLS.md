# Personal Coach — Tool Reference

All commands run from `personal-coach/` root.

## Core Session & Context
| Command | Purpose |
|---|---|
| `py -3 coach/tools/read_context.py [N]` | Full memory summary (last N sessions, default 5) |
| `py -3 coach/tools/read_goals.py` | Print goals.md |
| `py -3 coach/tools/read_habits.py` | Print habits.md |
| `py -3 coach/tools/read_checkpoint.py` | Print current coaching checkpoint |
| `py -3 coach/tools/store_session.py <skill> <duration> <rating> [notes]` | Save a session entry |
| `py -3 coach/tools/session_hooks.py pre` | Print pre-session context summary |
| `py -3 coach/tools/session_hooks.py post <skill> <duration> <rating> [notes]` | Post-session insight extraction (auto by store_session.py) |
| `py -3 coach/tools/save_context_snapshot.py "<task>" "<files>" "<decisions>" "<next>"` | Prevent data loss on context overflow |
| `py -3 coach/tools/load_context_snapshot.py` | Load most recent context snapshot |

## Goals, Habits, Checkpoints
| Command | Purpose |
|---|---|
| `py -3 coach/tools/add_goal.py "<title>" <target_date> <metric> [notes]` | Add goal |
| `py -3 coach/tools/add_habit.py "<title>" "<cue>" "<action>" [reward]` | Add habit |
| `py -3 coach/tools/write_checkpoint.py "<phase>" "<topic>" "<next_task>" [notes]` | Save checkpoint |

## Plans & Tasks
| Command | Purpose |
|---|---|
| `py -3 coach/tools/new_plan.py "<title>"` | Create plan from template in `process/plans/active/` |
| `py -3 coach/tools/task_manager.py add "<title>" [priority] [notes]` | Add task (priority: low/medium/high) |
| `py -3 coach/tools/task_manager.py list [--all\|--pending\|--done]` | List tasks |
| `py -3 coach/tools/task_manager.py done <id>` | Mark task complete |
| `py -3 coach/tools/task_manager.py delete <id>` | Delete task |

## Daily & Weekly Reviews
| Command | Purpose |
|---|---|
| `py -3 coach/tools/morning_plan.py ["brain dump..."]` | Create/update today's daily note |
| `py -3 coach/tools/daily_review.py ["extra notes..."]` | End-of-day review |
| `py -3 coach/tools/weekly_synthesis.py` | 7-day pattern analysis |
| `py -3 coach/tools/recap.py [N]` | Summarize last N days (default 7) |
| `py -3 coach/tools/thinking_partner.py "problem"` | Socratic questioning mode |
| `py -3 coach/tools/inbox_processor.py [--auto]` | Show/organize inbox captures |

## Memory & Search
| Command | Purpose |
|---|---|
| `py -3 coach/tools/memory_search.py "query" [--keyword]` | Search memory (vector first, fallback keyword) |
| `py -3 coach/tools/index_memory.py` | Build/rebuild TF-IDF index (auto on session store) |
| `py -3 coach/tools/index_memory.py --search "query"` | Direct vector search |
| `py -3 coach/tools/index_memory.py --info` | Index stats |
| `py -3 coach/tools/index_memory_lightrag.py` | Build LightRAG index (falls back to TF-IDF) |
| `py -3 coach/tools/index_memory_lightrag.py --search "query"` | Search via LightRAG/TF-IDF |
| `py -3 coach/tools/index_memory_lightrag.py --info` | Index stats |
| `py -3 coach/tools/ask_memory.py "question" [--ask]` | Semantic search + optional Ollama summarization |
| `py -3 coach/tools/extract_insights.py [--min-confidence 0.5]` | Extract patterns from sessions |
| `py -3 coach/tools/evolve_skill.py [--min-cluster 3] [--min-confidence 0.7]` | Cluster insights into skill suggestions |
| `py -3 coach/tools/export_anki.py [out_file]` | Export sessions as Anki JSON |

## Web & Research
| Command | Purpose |
|---|---|
| `py -3 coach/tools/web_search.py "query" [--max N] [--site domain]` | DuckDuckGo search |
| `py -3 coach/tools/web_fetch.py <url> [--selector "css"]` | Fetch and extract readable text |
| `py -3 coach/tools/deep_research.py "<topic>" [--max 4] [--no-llm]` | Multi-source research brief |

## Quotations (MOI/Security)
| Command | Purpose |
|---|---|
| `py -3 coach/tools/make_quotation.py "<input>"` | AI quotation: "8 cameras 2MP" etc. |
| `py -3 coach/tools/make_quotation.py --interactive` | Interactive chat mode |
| `py -3 coach/tools/make_quotation.py --list-rates` | Show rate card |
| `py -3 coach/tools/make_quotation.py --update-rates <file.xlsx>` | Import prices |
| `py -3 coach/tools/make_quotation.py "<input>" --moi [--arabic]` | MOI-compliant quotation |
| `py -3 coach/tools/learn_quotation.py <file.xlsx>` | Learn products from real quotation |
| `py -3 coach/tools/learn_quotation.py --all-existing [--write]` | Scan all quotations, optionally save |

## SEO
| Command | Purpose |
|---|---|
| `py -3 coach/tools/seo_audit.py <url> [--json]` | On-page SEO audit |
| `py -3 coach/tools/seo_audit.py <url> --crawl [--max-pages N]` | Multi-page content audit |
| `py -3 coach/tools/seo_audit.py <url> --backlinks` | Backlink check via Common Crawl |
| `py -3 coach/tools/seo_audit.py <url> --speed` | Page speed check |
| `py -3 coach/tools/seo_audit.py <url> --crawl --backlinks --speed` | Full audit |

## Site Surveys (MOI)
| Command | Purpose |
|---|---|
| `py -3 coach/tools/site_survey.py add "<client>" "<location>" [contact] [notes]` | Record visit |
| `py -3 coach/tools/site_survey.py list [--open\|--all\|--today]` | List surveys |
| `py -3 coach/tools/site_survey.py view <id>` | Show details |
| `py -3 coach/tools/site_survey.py close <id> [summary]` | Close survey |

## Backup & Restore
| Command | Purpose |
|---|---|
| `py -3 coach/tools/backup_memory.py [--git-only\|--zip-only]` | Git commit+push + ZIP archive |
| `py -3 coach/tools/restore_memory.py [--from-zip [path]\|--list]` | Restore from git or ZIP |

## Utilities
| Command | Purpose |
|---|---|
| `py -3 coach/tools/mcp_server.py [--interactive]` | Start stdio MCP server |
| `py -3 coach/tools/serve.py [--open] [/path/to/site]` | Dev server for preview |
