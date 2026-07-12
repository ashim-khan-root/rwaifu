"""In-process tool registry — replaces subprocess calls with direct imports.

Tools register themselves with a name, callable, arg schema, and optional
structured-result function. The dispatcher calls them in-process.
"""
import io
import sys
import json
from pathlib import Path
from typing import Any, Callable


class _CaptureIO(io.StringIO):
    def reconfigure(self, **kwargs):
        pass

BASE = Path(__file__).resolve().parent
TOOLS_DIR = BASE / "tools"

_entry: dict[str, dict] = {}


def _import_module(name: str):
    spec = __import__(f"tools.{name}", fromlist=["tools"])
    return spec


def _exec_via_argv(module, args: list[str]) -> str:
    old_argv = list(sys.argv)
    old_stdout = sys.stdout
    captured = _CaptureIO()
    try:
        sys.argv = [module.__file__ or name] + [str(a) for a in args]
        sys.stdout = captured
        if hasattr(module, "main"):
            module.main()
        else:
            if hasattr(module, "__name__"):
                old_name = module.__name__
                module.__name__ = "__main__"
                exec(open(module.__file__).read(), module.__dict__)
                module.__name__ = old_name
    except SystemExit:
        pass
    except Exception as e:
        return f"Error: {e}"
    finally:
        sys.argv = old_argv
        sys.stdout = old_stdout
    return captured.getvalue().strip()


def register(
    name: str,
    *,
    func: Callable = None,
    args_desc: list[dict] = None,
    description: str = "",
    fallback_module: bool = True,
):
    info = {
        "func": func,
        "args_desc": args_desc or [],
        "description": description,
        "fallback_module": fallback_module,
        "module": None,
    }
    _entry[name] = info


def execute(name: str, args: list[str]) -> str:
    info = _entry.get(name)
    if not info:
        mod = _import_module(name)
        if mod:
            return _exec_via_argv(mod, args)
        return f"Error: tool '{name}' not registered and not found in tools/"

    if info["func"]:
        try:
            result = info["func"](*args)
            if isinstance(result, dict):
                return json.dumps(result, ensure_ascii=False, indent=2)
            if isinstance(result, (list, tuple)):
                return json.dumps(result, ensure_ascii=False, indent=2)
            return str(result) if result is not None else ""
        except TypeError as e:
            if info["fallback_module"]:
                mod = _import_module(name)
                return _exec_via_argv(mod, args)
            return f"Error calling {name}: {e}"
        except Exception as e:
            return f"Error executing {name}: {e}"

    if info["fallback_module"]:
        mod = _import_module(name)
        return _exec_via_argv(mod, args)
    return f"Error: tool '{name}' has no callable function"


def tool_schemas() -> str:
    lines = []
    for name, info in sorted(_entry.items()):
        desc = info["description"]
        args = info["args_desc"]
        lines.append(f"{name}: {desc}")
        for a in args:
            pos = a.get("position", a.get("name", ""))
            required = a.get("required", True)
            lines.append(f"  [{pos}] {'req' if required else 'opt'}: {a.get('help', '')}")
    return "\n".join(lines)


def registered_tools() -> list[str]:
    return list(_entry.keys())


register("store_session",
    description="Store a practice session in memory.",
    args_desc=[
        {"name": "skill", "help": "skill name", "required": True},
        {"name": "duration_min", "help": "duration in minutes", "required": True},
        {"name": "rating", "help": "rating 1-10", "required": True},
        {"name": "notes", "help": "optional notes", "required": False},
    ])

register("morning_plan",
    description="Create or update today's daily note.",
    args_desc=[{"name": "brain_dump", "help": "brain dump text", "required": False}])

register("daily_review",
    description="Run end-of-day review.",
    args_desc=[{"name": "notes", "help": "extra notes", "required": False}])

register("thinking_partner",
    description="Socratic questioning mode.",
    args_desc=[{"name": "problem", "help": "the problem to think through", "required": True}])

register("seo_audit",
    description="Run SEO audit on a URL.",
    args_desc=[
        {"name": "url", "help": "URL to audit", "required": True},
        {"name": "--crawl", "help": "enable crawling", "required": False},
        {"name": "--backlinks", "help": "check backlinks", "required": False},
        {"name": "--speed", "help": "check speed", "required": False},
    ])

register("deep_research",
    description="Multi-source research on a topic.",
    args_desc=[
        {"name": "topic", "help": "research topic", "required": True},
        {"name": "--max", "help": "max results per query", "required": False},
    ])

register("web_search",
    description="Search the web.",
    args_desc=[
        {"name": "query", "help": "search query", "required": True},
        {"name": "--max", "help": "max results", "required": False},
        {"name": "--site", "help": "site filter", "required": False},
    ])

register("web_fetch",
    description="Fetch readable text from a URL.",
    args_desc=[
        {"name": "url", "help": "URL to fetch", "required": True},
        {"name": "--selector", "help": "CSS selector", "required": False},
    ])

register("weekly_synthesis",
    description="Run 7-day pattern analysis. No args.")

register("recap",
    description="Summarize last N days.",
    args_desc=[{"name": "days", "help": "number of days", "required": False}])

register("backup_memory",
    description="Git backup or ZIP archive of memory.",
    args_desc=[{"name": "--git-only", "help": "git only", "required": False}])

register("restore_memory",
    description="Restore memory from backup.",
    args_desc=[{"name": "--from-zip", "help": "restore from zip", "required": False}])

register("new_plan",
    description="Create a new plan file from template.",
    args_desc=[{"name": "title", "help": "plan title", "required": True}])
