---
type: Bundle
id: okf-catalog
version: 1
created: 2026-07-07
updated: 2026-07-07
description: Agent-discoverable knowledge catalog for the Personal Coach
---

# OKF Catalog — Observable Knowledge Format

This index lets agents discover all structured knowledge in the Personal Coach system. Each concept file has YAML frontmatter following the OKF convention.

## User Knowledge

| File | Type | Description |
|---|---|---|
| `coach/user/identity.md` | `Identity` | Who you are — name, role, stack, communication style |
| `coach/user/telos.md` | `Telos` | Mission, goals, beliefs, wisdom, mental models, narratives |

## Memory Knowledge

| File | Type | Description |
|---|---|---|
| `coach/memory/profile.md` | `Profile` | Detailed user profile, current focus, aspirations, roadmap |
| `coach/memory/patterns.md` | `Pattern` | Behavioral patterns — communication, work style, motivation |
| `coach/memory/insights.md` | `Insight` | Auto-extracted patterns from session history |
| `coach/memory/resources.md` | `Resource` | External resource links (Spanish, Running, Design, Dev tiers) |

## Transactional Layer (SQLite — not OKF)

These are stored in `coach/memory/coach.db` and not migrated to OKF:

- Sessions, tasks, goals, habits, checkpoint, prds

## Changelog

See `log.md` for knowledge changes.
