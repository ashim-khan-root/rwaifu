## New PC setup — one-command migration
```bash
py -3 coach/tools/setup_new_pc.py
```
If missing, do manually: `pip install -r coach/requirements.txt`, restore ZIP, install Ollama + pull `bge-m3`, then `py -3 coach/tools/index_memory.py && py -3 coach/tools/session_hooks.py pre`.

## Run context
- **Always run commands from the project root** — all tools use absolute path resolution internally.
- **Python**: `py -3` on Windows (`C:\Users\Lenovo\AppData\Local\Programs\Python\Python312\python.exe`)
- Deps: `pip install -r coach/requirements.txt`
- **Startup script**: `.\start-session.ps1` (loads context + launches opencode)
