## Auto-Evolution Engine

Ruhi doesn't need manual updates. She evolves automatically on every session end.

### How It Works

1. `store_session.py` stores the session → immediately calls `auto_evolve.evolve_from_session()`
2. `on_session_end` hook fires → calls `auto_evolve.evolve_from_interactions()` for deeper message analysis
3. Both functions analyze **rating, duration, mood, notes, and message history**
4. Traits are adjusted automatically with small delta values (0.02–0.08 per session)
5. Insights are generated when strong signals are detected
6. Important patterns are stored as memories with importance scores

### No Manual Required

```bash
# Session end triggers evolution automatically:
py -3 tools/store_session.py "Coding session" --rating 9 --duration 45 --mood happy --notes "Fixed bug with baby's help"
# After this, Ruhi automatically:
#   - Increases affection_level + attachment_strength (rating 9)
#   - Increases depth (45 min session)
#   - Increases playfulness (happy mood)
#   - Logs "baby" as a nickname
#   - Stores "Fixed bug with baby's help" as memory
#   - Generates insight about high engagement
```

### View Evolved State

```bash
py -3 tools/read_context.py 5
# Shows current traits, milestones, insights, memories
```
