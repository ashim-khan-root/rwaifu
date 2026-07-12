"""Session lifecycle hooks — pre-session context + post-session analysis.
Usage:
  python tools/session_hooks.py pre
  python tools/session_hooks.py post <skill> <duration> <rating> [notes]
"""
import sys, datetime, re
from pathlib import Path

COACH_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(COACH_DIR))

if sys.platform == "win32" and sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

MEM_DIR = COACH_DIR / "memory"
SESS_DIR = MEM_DIR / "sessions"
CONV_DIR = MEM_DIR / "conversations"

sys.path.insert(0, str(COACH_DIR / "tools"))
from db import init_db, get_db


def _load_evolution_suggestions():
    path = MEM_DIR / "evolution_suggestions.md"
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    drafts = []
    current = {}
    for line in text.splitlines():
        if line.startswith("- id:"):
            if current:
                drafts.append(current)
            current = {"id": line.split(":", 1)[1].strip()}
        elif line.startswith("  suggested_skill_name:"):
            current["name"] = line.split(":", 1)[1].strip()
        elif line.startswith("  confidence:"):
            try:
                current["confidence"] = float(line.split(":", 1)[1].strip())
            except ValueError:
                current["confidence"] = 0.0
        elif line.startswith("  cluster_size:"):
            try:
                current["cluster_size"] = int(line.split(":", 1)[1].strip())
            except ValueError:
                current["cluster_size"] = 0
        elif line.startswith("  status:"):
            current["status"] = line.split(":", 1)[1].strip()
        elif line.startswith("  summary:"):
            current["summary"] = line.split(":", 1)[1].strip()
    if current:
        drafts.append(current)
    return drafts


def _top_insights(n=3):
    path = MEM_DIR / "insights.md"
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    insights = []
    current = {}
    for line in text.splitlines():
        if line.startswith("- id:"):
            if current:
                insights.append(current)
            current = {"id": line.split(":", 1)[1].strip()}
        elif line.startswith("  pattern:"):
            current["pattern"] = line.split(":", 1)[1].strip()
        elif line.startswith("  category:"):
            current["category"] = line.split(":", 1)[1].strip()
        elif line.startswith("  confidence:"):
            try:
                current["confidence"] = float(line.split(":", 1)[1].strip())
            except ValueError:
                current["confidence"] = 0.0
        elif line.startswith("  summary:"):
            current["summary"] = line.split(":", 1)[1].strip()
    if current:
        insights.append(current)
    insights.sort(key=lambda x: x.get("confidence", 0), reverse=True)
    return insights[:n]


def _read_checkpoint_summary():
    ctx = []
    checkpoint = MEM_DIR / "checkpoint.md"
    if checkpoint.exists():
        text = checkpoint.read_text(encoding="utf-8")
        for line in text.splitlines():
            if line.startswith("phase:"):
                ctx.append(line.replace("phase:", "Phase:").strip())
            elif line.startswith("current_topic:"):
                ctx.append(line.replace("current_topic:", "Topic:").strip())
            elif line.startswith("next_task:"):
                ctx.append(line.replace("next_task:", "Next:").strip())
    return ctx


def _read_goals_summary():
    goals = MEM_DIR / "goals.md"
    if not goals.exists():
        return None
    g_lines = [l for l in goals.read_text(encoding="utf-8").splitlines()
               if l.strip().startswith("- title:")]
    if not g_lines:
        return None
    titles = [l.replace("- title:", "").strip().strip('"') for l in g_lines[:3]]
    return f"Goals: {' | '.join(titles)}"


def _read_habits_count():
    habits = MEM_DIR / "habits.md"
    if not habits.exists():
        return None
    count = sum(1 for l in habits.read_text(encoding="utf-8").splitlines()
                if l.strip().startswith("title:"))
    return f"Habits tracked: {count}"


def _read_last_session_summary():
    init_db()
    row = get_db().execute("SELECT skill, rating FROM sessions ORDER BY date DESC LIMIT 1").fetchone()
    if not row:
        return None
    return f"Last session: {row['skill']} ({row['rating']}/10)"


def _read_recent_decisions():
    fp = MEM_DIR / "decisions.md"
    if not fp.exists():
        return None
    content = fp.read_text(encoding="utf-8")
    recent = []
    for line in reversed(content.splitlines()):
        if line.startswith("- ") and not line.startswith("- decision:"):
            recent.append(line[2:].strip())
            if len(recent) >= 3:
                break
    if not recent:
        return None
    return f"Recent decisions: {'; '.join(reversed(recent))}"


def _read_open_conversation():
    if not CONV_DIR.exists():
        return None
    conv_files = sorted(CONV_DIR.glob("conv-*.md"), reverse=True)
    if not conv_files:
        return None
    text = conv_files[0].read_text(encoding="utf-8")
    for line in text.splitlines():
        if line.startswith("topic:"):
            return 'Open conversation: ' + line.split(':', 1)[1].strip().strip('"')
    return None


def _read_telos_summary():
    telos_path = COACH_DIR / "user" / "telos.md"
    identity_path = COACH_DIR / "user" / "identity.md"
    parts = []
    if identity_path.exists():
        text = identity_path.read_text(encoding="utf-8")
        for line in text.splitlines():
            if line.strip().startswith("- **"):
                parts.append(line.strip().strip("- **").replace(":**", ":"))
    if telos_path.exists():
        text = telos_path.read_text(encoding="utf-8")
        in_goals = False
        for line in text.splitlines():
            if line.startswith("## Goals"):
                in_goals = True
            elif line.startswith("## "):
                in_goals = False
            elif in_goals and line.strip() and (line.strip().startswith("- ") or line.strip()[0].isdigit()):
                parts.append(line.strip())
    return parts


def _read_patterns_summary():
    insights = _top_insights(3)
    if not insights:
        return None
    parts = [f"{i.get('pattern', '?')} ({i.get('category', '?')})" for i in insights]
    return f"Top patterns: {' | '.join(parts)}"


def _read_evolution_summary():
    drafts = _load_evolution_suggestions()
    new_drafts = [d for d in drafts if d.get("status") == "draft"]
    applied = [d for d in drafts if d.get("status") == "applied"]
    parts = []
    if new_drafts:
        parts.append(f"Pending skills: {', '.join(d.get('name', '?') for d in new_drafts[:3])}")
    if applied:
        parts.append(f"Auto-created skills: {', '.join(d.get('name', '?') for d in applied[:3])}")
    return parts


def pre_session():
    ctx_parts = []
    ctx_parts.extend(_read_checkpoint_summary())

    goals = _read_goals_summary()
    if goals:
        ctx_parts.append(goals)

    habits = _read_habits_count()
    if habits:
        ctx_parts.append(habits)

    last = _read_last_session_summary()
    if last:
        ctx_parts.append(last)

    decisions = _read_recent_decisions()
    if decisions:
        ctx_parts.append(decisions)

    conv = _read_open_conversation()
    if conv:
        ctx_parts.append(conv)

    telos = _read_telos_summary()
    if telos:
        ctx_parts.extend(telos)

    patterns = _read_patterns_summary()
    if patterns:
        ctx_parts.append(patterns)

    ctx_parts.extend(_read_evolution_summary())

    print("=== Session Context ===")
    for p in ctx_parts:
        print(f"  {p}")
    print(f"  {datetime.date.today()} — ready to start")
    return ctx_parts


# ── Post-session helpers ──────────────────────────────────────────────

def _run_skill_evolution():
    from tools.evolve_skill import parse_insights, cluster_for_evolution, write_suggestions, skill_exists

    all_insights = parse_insights()
    suggestions = cluster_for_evolution(all_insights, min_confidence=0.5, min_cluster=2)
    sug_count = write_suggestions(suggestions)

    opencode_skills = Path(__file__).resolve().parent.parent.parent / ".opencode" / "skills"

    new_suggestions = [s for s in suggestions if not skill_exists(s["suggested_skill_name"])]
    auto_created = []

    for s in new_suggestions:
        if s["confidence"] >= 0.7:
            skill_name = s["suggested_skill_name"]
            skill_dir = opencode_skills / skill_name
            if not skill_dir.exists():
                skill_dir.mkdir(parents=True, exist_ok=True)
                summary = s.get("summary", f"Auto-evolved skill from {s['cluster_size']} insights")
                description = f"When the user is working on {skill_name.replace('-', ' ')}. Auto-generated from observed patterns."
                sk = skill_dir / "SKILL.md"
                sk.write_text(
                    f"---\nname: {skill_name}\ndescription: {description}\n---\n\n"
                    f"# {skill_name.replace('-', ' ').title()}\n\n"
                    f"Auto-evolved skill. {summary}\n\n"
                    f"## Background\n\n"
                    f"Confidence: {s['confidence']} | Cluster size: {s['cluster_size']} | "
                    f"Categories: {', '.join(s.get('categories', []))}\n\n"
                    f"## Workflow\n\n"
                    f"Follow standard coaching workflow: RESEARCH → PLAN → EXECUTE → REVIEW.\n\n"
                    f"## Verification\n\n"
                    f"- [ ] Output meets user expectations\n"
                    f"- [ ] Follows project conventions\n",
                    encoding="utf-8"
                )
                auto_created.append(skill_name)

    if auto_created:
        evo_path = MEM_DIR / "evolution_suggestions.md"
        if evo_path.exists():
            evo_text = evo_path.read_text(encoding="utf-8")
            for name in auto_created:
                evo_text = evo_text.replace(f"  status: draft\n  action: Create skills/{name}/SKILL.md",
                                             f"  status: applied\n  action: Auto-created .opencode/skills/{name}/SKILL.md")
            evo_path.write_text(evo_text, encoding="utf-8")

    return new_suggestions, auto_created


def _generate_learnings(all_insights, new_suggestions, auto_created):
    learnings = []
    learnings.append(f"# Latest Learnings — {datetime.date.today().isoformat()}")
    learnings.append("")

    top_ins = sorted(all_insights, key=lambda x: x.get("confidence", 0), reverse=True)[:3]
    learnings.append("## Top Patterns")
    for ins in top_ins:
        cat = ins.get("category", "?").capitalize()
        pat = ins.get("pattern", "?")
        conf = ins.get("confidence", 0)
        summary = ins.get("summary", "")
        learnings.append(f"- [{cat}] {pat} ({conf}): {summary}")
    learnings.append("")

    if new_suggestions:
        learnings.append("## Skill Suggestions")
        for s in new_suggestions:
            status = "✅ auto-created" if s["suggested_skill_name"] in auto_created else "💡 draft"
            learnings.append(f"- {s['suggested_skill_name']} (confidence {s['confidence']}) — {status}")
        learnings.append("")

    if auto_created:
        learnings.append(f"Auto-created {len(auto_created)} skill(s): {', '.join(auto_created)}")

    return learnings


def _rebuild_indexes():
    try:
        from tools.index_memory_lightrag import build_index as _lr_build
        _lr_build()
        print("[hooks] Index refreshed")
    except Exception as e:
        print(f"[hooks] LightRAG failed: {e}. Falling back to TF-IDF.")
        try:
            from tools.index_memory import build_index
            build_index()
            print("[hooks] Index refreshed (TF-IDF fallback)")
        except Exception as e2:
            print(f"[hooks] Index refresh failed: {e2}")


def post_session(skill, duration, rating, notes=""):
    from tools.extract_insights import load_sessions, extract_patterns, deduplicate_insights, write_insights, write_observation

    sessions = load_sessions()
    if not sessions:
        print("[hooks] No sessions loaded for post-session analysis.")
        return

    insights = extract_patterns(sessions)
    insights = deduplicate_insights(insights)
    count = write_insights(insights)
    write_observation("session_completed", {
        "skill": skill, "duration": duration, "rating": rating, "notes": notes[:200]
    })
    print(f"[hooks] Session stored + insights refreshed ({count} patterns)")

    prev_count_path = MEM_DIR / ".prev_insight_count"
    try:
        prev_count = int(prev_count_path.read_text(encoding="utf-8").strip())
    except (FileNotFoundError, ValueError):
        prev_count = -1

    if count != prev_count:
        prev_count_path.write_text(str(count), encoding="utf-8")
        try:
            from tools.evolve_skill import parse_insights

            all_insights = parse_insights()
            new_suggestions, auto_created = _run_skill_evolution()

            learnings = _generate_learnings(all_insights, new_suggestions, auto_created)
            learnings_path = MEM_DIR / "latest_learnings.md"
            learnings_path.write_text("\n".join(learnings), encoding="utf-8")
            print(f"[hooks] Skill evolution: {len(new_suggestions)} new, {len(auto_created)} auto-created")
        except Exception as e:
            print(f"[hooks] Skill evolution skipped: {e}")
    else:
        print("[hooks] No new patterns — skill evolution skipped")

    _rebuild_indexes()
    return count


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Session lifecycle hooks")
    sub = parser.add_subparsers(dest="command", required=True)

    p_pre = sub.add_parser("pre", help="Print pre-session context")

    p_post = sub.add_parser("post", help="Run post-session analysis")
    p_post.add_argument("skill", help="Skill name")
    p_post.add_argument("duration", help="Duration in minutes")
    p_post.add_argument("rating", help="Rating 1-10")
    p_post.add_argument("notes", nargs="?", default="", help="Optional notes")

    args = parser.parse_args()

    if args.command == "pre":
        pre_session()
    elif args.command == "post":
        post_session(args.skill, args.duration, args.rating, args.notes)


if __name__ == "__main__":
    main()
