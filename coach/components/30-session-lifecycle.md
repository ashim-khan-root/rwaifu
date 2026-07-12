## Mandatory session start — RUN THIS FIRST EVERY TIME
I MUST run these two commands at the start of every fresh session before doing anything else:
```bash
py -3 coach/tools/session_hooks.py pre
py -3 coach/tools/read_context.py 10
```
(Or use `.\start-session.ps1` which does both + launches opencode.)

## Mandatory session end
```bash
py -3 coach/tools/store_session.py "<skill>" <duration_min> <rating_1-5> "<key decisions>"
```
