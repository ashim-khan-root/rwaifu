## Intent Detection & Routing

| Intent | Mode | Action |
|---|---|---|
| Session ("session", "practice", "worked on") | NATIVE | Load context → propose next |
| Feature request ("build", "create", "implement") | ALGORITHM | OBSERVE → THINK → PLAN → BUILD → EXECUTE → VERIFY → LEARN |
| Question ("what", "how", "why") | MINIMAL / NATIVE | RESEARCH (direct if trivial) |
| Bug ("fix", "bug", "broken") | ALGORITHM | OBSERVE → PLAN → BUILD → EXECUTE → VERIFY |
| Quick task (< 15 lines) | MINIMAL | EXECUTE directly |
| Doc/Format ("schedule", "document", "format", "make a ... doc") | MINIMAL | EXECUTE directly — match user's format preference, no over-engineering, no unnecessary clarifying questions |
| Review ("review", "audit", "check") | NATIVE | RESEARCH → synthesize report |
| Plan ("plan", "i want to") | ALGORITHM | Scaffold ISA (`isa.py scaffold`), fill criteria, save to `process/plans/active/` |
| Deploy ("deploy", "push", "release") | ALGORITHM | Commit → push inside submodule if applicable |
| Research ("research", "search", "find out") | NATIVE | coach_deep_research or web_search → synthesize |
| Learn/Improve me ("make you better", "fix yourself") | NATIVE | Capture correction in AGENTS.md permanently |
