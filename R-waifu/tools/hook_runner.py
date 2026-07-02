import sys
import os
import importlib.util
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools.db import get_db
from tools.insight_ledger import log_event


def run_hooks(event_name, context=None):
    hooks_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "hooks")
    if not os.path.isdir(hooks_dir):
        return

    results = []
    for fname in sorted(os.listdir(hooks_dir)):
        if fname.endswith(".py") and not fname.startswith("_"):
            hook_path = os.path.join(hooks_dir, fname)
            try:
                spec = importlib.util.spec_from_file_location(fname[:-3], hook_path)
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                if hasattr(mod, "run"):
                    result = mod.run(event_name, context or {})
                    results.append({"hook": fname, "result": result})
            except Exception as e:
                results.append({"hook": fname, "error": str(e)})

    log_event(f"hooks:{event_name}", {"count": len(results)})
    return results
