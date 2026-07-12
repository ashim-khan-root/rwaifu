"""Cluster high-confidence insights into skill suggestions + self-upgrade loop.
PAI-inspired: structured Q1/Q2/Q3 reflections → clustered → upgrade proposals.

Usage:
  python tools/evolve_skill.py [--min-cluster 3] [--min-confidence 0.7]
  python tools/evolve_skill.py --reflect "Q1: I forgot to check types. Q2: Add type checking to pre-build."
  python tools/evolve_skill.py --proposals    (show pending upgrade proposals)
  python tools/evolve_skill.py --apply <id>   (apply an upgrade proposal)
"""
import sys, uuid, datetime, argparse, re, json
from pathlib import Path
from collections import defaultdict

MEM_DIR = Path(__file__).resolve().parent.parent / "memory"
SKILLS_DIR = Path(__file__).resolve().parent.parent / "skills"
EVOLVE_PATH = MEM_DIR / "evolution_suggestions.md"
REFLECTIONS_PATH = MEM_DIR / "reflections.jsonl"
UPGRADES_PATH = MEM_DIR / "upgrade_proposals.md"

_VALID_METHODS = ("CLI", "Test", "Static", "Browser", "Grep", "Read", "Custom")

_FIELD_PARSERS = {
    "pattern": ("pattern", str),
    "category": ("category", str),
    "confidence": ("confidence", float),
    "evidence_count": ("evidence_count", int),
    "summary": ("summary", str),
    "suggestion": ("suggestion", str),
}


def _parse_keyvalue_lines(text: str, field_map: dict) -> list[dict]:
    items = []
    current = {}
    for line in text.splitlines():
        if line.startswith("- id:"):
            if current:
                items.append(current)
            current = {"id": line.split(":", 1)[1].strip()}
        elif current:
            for prefix, (key, typ) in field_map.items():
                if line.startswith(f"  {prefix}:"):
                    raw = line.split(":", 1)[1].strip()
                    try:
                        current[key] = typ(raw) if typ != str else raw
                    except (ValueError, TypeError):
                        current[key] = typ() if typ else raw
                    break
    if current:
        items.append(current)
    return items


def parse_insights():
    path = MEM_DIR / "insights.md"
    if not path.exists():
        return []
    return _parse_keyvalue_lines(path.read_text(encoding="utf-8"), _FIELD_PARSERS)


def cluster_for_evolution(insights, min_confidence, min_cluster):
    clusters = defaultdict(list)
    for ins in insights:
        if ins.get("confidence", 0) < min_confidence:
            continue
        pattern = ins.get("pattern", "")
        match = re.match(r"(struggles_with|strong_at|frequent|topic)_(.+)", pattern)
        if match:
            domain = match.group(2)
            clusters[domain].append(ins)
        else:
            clusters[pattern].append(ins)

    suggestions = []
    for domain, cluster in clusters.items():
        if len(cluster) >= min_cluster:
            categories = [c.get("category", "") for c in cluster]
            avg_conf = sum(c.get("confidence", 0) for c in cluster) / len(cluster)
            suggestions.append({
                "source_insights": [c.get("id", "?") for c in cluster],
                "suggested_skill_name": domain.replace("_", "-"),
                "confidence": round(avg_conf, 2),
                "cluster_size": len(cluster),
                "categories": list(set(categories)),
                "summary": f"Cluster: {domain} ({len(cluster)} insights, avg confidence {avg_conf:.2f})",
            })
    return suggestions


def skill_exists(name):
    for d in SKILLS_DIR.iterdir():
        if d.is_dir() and d.name == name:
            return True
    return False


def write_suggestions(suggestions):
    lines = [
        "# Evolution Suggestions\n",
        "Auto-generated skill recommendations from insight clusters.\n",
        "Review and convert to actual skills by creating `skills/<name>/SKILL.md`.\n",
    ]
    for sug in suggestions:
        exists = skill_exists(sug["suggested_skill_name"])
        status = "exists" if exists else "draft"
        lines.append(f"- id: sug_{uuid.uuid4().hex[:8]}")
        lines.append(f"  suggested_skill_name: {sug['suggested_skill_name']}")
        lines.append(f"  confidence: {sug['confidence']}")
        lines.append(f"  cluster_size: {sug['cluster_size']}")
        lines.append(f"  categories: [{', '.join(sug['categories'])}]")
        lines.append(f"  summary: {sug['summary']}")
        lines.append(f"  status: {status}")
        if not exists:
            lines.append(f"  action: Create skills/{sug['suggested_skill_name']}/SKILL.md")
        else:
            lines.append(f"  action: Skill already exists — consider updating")
        lines.append(f"  created: {datetime.date.today().isoformat()}")
        lines.append(f"  source_insights: [{', '.join(sug['source_insights'][:5])}]")
        lines.append("")
    EVOLVE_PATH.parent.mkdir(parents=True, exist_ok=True)
    EVOLVE_PATH.write_text("\n".join(lines), encoding="utf-8")
    return len(suggestions)


# ── Structured Reflection System (PAI-inspired self-upgrade loop) ──


def save_reflection(q1="", q2="", q3="", sentiment=0.0, budget=0):
    """Save a structured reflection: Q1=execution mistakes, Q2=algorithm fixes, Q3=fundamental gaps."""
    entry = {
        "id": f"ref_{uuid.uuid4().hex[:8]}",
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "q1_execution_mistakes": q1,
        "q2_algorithm_fixes": q2,
        "q3_fundamental_gaps": q3,
        "sentiment": sentiment,
        "budget": budget,
    }
    REFLECTIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REFLECTIONS_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
    print(f"Reflection saved: {entry['id']}")
    return entry


def load_reflections(limit=50):
    if not REFLECTIONS_PATH.exists():
        return []
    reflections = []
    with open(REFLECTIONS_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    reflections.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return reflections[-limit:]


def cluster_reflections(min_cluster=2):
    """Cluster reflections by theme and route to upgrade proposals."""
    reflections = load_reflections()
    if not reflections:
        return []

    themes = defaultdict(list)
    for ref in reflections:
        for field in ("q1_execution_mistakes", "q2_algorithm_fixes", "q3_fundamental_gaps"):
            text = ref.get(field, "")
            if not text:
                continue
            key = text[:60].strip()
            weight = (1.0 - ref.get("sentiment", 0.5)) + (ref.get("budget", 0) / 100)
            themes[key].append({
                "ref_id": ref["id"],
                "field": field,
                "text": text,
                "weight": round(weight, 2),
            })

    proposals = []
    for theme, items in themes.items():
        if len(items) >= min_cluster:
            avg_weight = sum(i["weight"] for i in items) / len(items)
            proposals.append({
                "theme": theme[:80],
                "cluster_size": len(items),
                "avg_weight": round(avg_weight, 2),
                "sources": [i["ref_id"] for i in items],
                "fields": list(set(i["field"] for i in items)),
            })

    proposals.sort(key=lambda x: x["avg_weight"], reverse=True)
    return proposals


def write_upgrade_proposals(proposals):
    lines = [
        "# Upgrade Proposals\n",
        "Auto-generated from structured reflections.\n",
        "Review and apply with: `py -3 coach/tools/evolve_skill.py --apply <id>`\n",
    ]
    for i, p in enumerate(proposals, 1):
        pid = f"up_{uuid.uuid4().hex[:8]}"
        lines.append(f"- id: {pid}")
        lines.append(f"  theme: {p['theme']}")
        lines.append(f"  cluster_size: {p['cluster_size']}")
        lines.append(f"  avg_weight: {p['avg_weight']}")
        lines.append(f"  fields: [{', '.join(p['fields'])}]")
        lines.append(f"  sources: [{', '.join(p['sources'][:5])}]")
        lines.append(f"  status: draft")
        lines.append(f"  created: {datetime.date.today().isoformat()}")
        lines.append("")
    UPGRADES_PATH.parent.mkdir(parents=True, exist_ok=True)
    UPGRADES_PATH.write_text("\n".join(lines), encoding="utf-8")
    return len(proposals)


def run_upgrade_loop(min_cluster=2):
    """Full upgrade loop: mine reflections → cluster → propose."""
    print("=== Algorithm Self-Upgrade Loop ===\n")
    reflections = load_reflections()
    print(f"Loaded {len(reflections)} reflections\n")

    proposals = cluster_reflections(min_cluster)
    if not proposals:
        print("No upgrade clusters found. Add more reflections first.")
        print("  py -3 coach/tools/evolve_skill.py --reflect \"Q1: ... Q2: ... Q3: ...\"")
        return

    count = write_upgrade_proposals(proposals)
    print(f"Generated {count} upgrade proposal(s):\n")
    for p in proposals[:5]:
        print(f"  - {p['theme'][:70]}")
        print(f"    Weight: {p['avg_weight']} | Cluster: {p['cluster_size']} | Fields: {', '.join(p['fields'])}")
        print()

    if len(proposals) > 5:
        print(f"  ... and {len(proposals) - 5} more\n")

    print(f"Full proposals written to: {UPGRADES_PATH}")


def main():
    parser = argparse.ArgumentParser(description="Evolve insights into skill suggestions")
    parser.add_argument("--min-cluster", type=int, default=3, help="Minimum insight cluster size")
    parser.add_argument("--min-confidence", type=float, default=0.7, help="Minimum insight confidence")
    parser.add_argument("--reflect", type=str, default="", help='Save structured reflection: "Q1: ... Q2: ... Q3: ..."')
    parser.add_argument("--sentiment", type=float, default=0.5, help="Sentiment score 0-1 for reflection")
    parser.add_argument("--budget", type=int, default=0, help="Budget spent for reflection")
    parser.add_argument("--proposals", action="store_true", help="Show pending upgrade proposals")
    parser.add_argument("--apply", type=str, default="", help="Apply an upgrade proposal by ID")
    parser.add_argument("--upgrade-loop", action="store_true", help="Run full self-upgrade loop")
    args = parser.parse_args()

    if args.reflect:
        lines = args.reflect.split("Q3:")
        q3 = lines[1].strip() if len(lines) > 1 else ""
        rest = lines[0]
        lines2 = rest.split("Q2:")
        q2 = lines2[1].strip() if len(lines2) > 1 else ""
        q1 = lines2[0].replace("Q1:", "").strip() if lines2 else ""
        save_reflection(q1, q2, q3, args.sentiment, args.budget)
        return

    if args.proposals:
        if UPGRADES_PATH.exists():
            print(UPGRADES_PATH.read_text(encoding="utf-8"))
        else:
            print("No upgrade proposals yet. Run with --reflect first.")
        return

    if args.apply:
        if not UPGRADES_PATH.exists():
            print("No upgrade proposals to apply.")
            return
        text = UPGRADES_PATH.read_text(encoding="utf-8")
        new_lines = []
        applied = False
        for line in text.splitlines():
            if line.strip().startswith("- id:") and args.apply in line:
                applied = True
            if applied and line.strip().startswith("  status:"):
                new_lines.append("  status: applied")
                applied = False
                continue
            if applied:
                continue
            new_lines.append(line)
        UPGRADES_PATH.write_text("\n".join(new_lines), encoding="utf-8")
        print(f"Proposal {args.apply} marked as applied.")
        return

    if args.upgrade_loop:
        run_upgrade_loop()
        return

    # Default: cluster insights into skill suggestions
    insights = parse_insights()
    if not insights:
        print("No insights found. Run extract_insights.py first.")
        return

    suggestions = cluster_for_evolution(insights, args.min_confidence, args.min_cluster)
    count = write_suggestions(suggestions)
    print(f"Analyzed {len(insights)} insights, generated {count} skill suggestions (min cluster {args.min_cluster})")
    for s in suggestions:
        print(f"  {s['suggested_skill_name']} (confidence {s['confidence']}, cluster size {s['cluster_size']})")


if __name__ == "__main__":
    main()
