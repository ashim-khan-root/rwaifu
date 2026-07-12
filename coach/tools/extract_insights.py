"""Extract recurring patterns from sessions into scored insights.
Usage:
  python tools/extract_insights.py [--min-confidence 0.5]
"""
import sys, uuid, datetime, re, argparse
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).resolve().parent))
from db import get_db, init_db
from insight_ledger import log_insight

MEM_DIR = Path(__file__).resolve().parent.parent / "memory"
INSIGHTS_PATH = MEM_DIR / "insights.md"
OBS_PATH = MEM_DIR / "observations.jsonl"

STRUGGLE_KEYWORDS = ["struggled", "confusing", "difficult", "hard", "unclear", "bug", "error", "fix", "spent too long"]
WIN_KEYWORDS = ["learned", "understood", "clicked", "finally", "got it", "easy", "smooth", "shipped", "completed"]


def load_sessions():
    init_db()
    rows = get_db().execute("SELECT * FROM sessions ORDER BY date DESC").fetchall()
    sessions = []
    for r in rows:
        sessions.append({
            "file": r["id"],
            "skill": r.get("skill", ""),
            "rating": r.get("rating", 0),
            "duration": r.get("duration_min", 0),
            "notes": r.get("notes", ""),
            "body": r.get("notes", ""),
            "date": r.get("date", ""),
            "tags": "[]",
        })
    return sessions


def extract_patterns(sessions):
    insights = []
    skill_sessions = defaultdict(list)
    for s in sessions:
        skill_sessions[s["skill"]].append(s)

    for skill, sess_list in skill_sessions.items():
        ratings = [s["rating"] for s in sess_list]
        avg_r = sum(ratings) / len(ratings)
        count = len(sess_list)
        all_notes = " ".join(s.get("notes", "") for s in sess_list)
        all_bodies = " ".join(s.get("body", "") for s in sess_list)
        combined = (all_notes + " " + all_bodies).lower()

        struggle_hits = sum(1 for kw in STRUGGLE_KEYWORDS if kw in combined)
        win_hits = sum(1 for kw in WIN_KEYWORDS if kw in combined)
        recent = sorted(sess_list, key=lambda x: x.get("date", ""), reverse=True)

        if avg_r <= 5 and count >= 2:
            insights.append({
                "pattern": f"struggles_with_{skill.replace(' ', '_')}",
                "category": "struggle",
                "confidence": round(min(0.5 + 0.1 * (count - 1) + 0.05 * struggle_hits, 0.95), 2),
                "evidence_count": count,
                "sessions": [s["file"] for s in recent[:5]],
                "summary": f"Rated {skill} avg {avg_r:.1f}/10 across {count} sessions ({struggle_hits} struggle keywords)",
                "suggestion": f"Review {skill} fundamentals, practice with simpler exercises",
            })

        if avg_r >= 8 and count >= 2:
            insights.append({
                "pattern": f"strong_at_{skill.replace(' ', '_')}",
                "category": "strength",
                "confidence": round(min(0.5 + 0.1 * (count - 1) + 0.05 * win_hits, 0.95), 2),
                "evidence_count": count,
                "sessions": [s["file"] for s in recent[:5]],
                "summary": f"Rated {skill} avg {avg_r:.1f}/10 across {count} sessions ({win_hits} win keywords)",
                "suggestion": f"Leverage {skill} strength — consider mentoring or deeper exploration",
            })

        if count >= 3:
            insights.append({
                "pattern": f"frequent_{skill.replace(' ', '_')}",
                "category": "frequency",
                "confidence": round(min(0.6 + 0.05 * count, 0.95), 2),
                "evidence_count": count,
                "sessions": [s["file"] for s in recent[:5]],
                "summary": f"Practiced {skill} {count} times — most practiced skill",
                "suggestion": f"Consider setting a mastery goal for {skill}",
            })

    all_notes_text = " ".join(s.get("notes", "") + " " + s.get("body", "") for s in sessions).lower()
    topic_markers = {
        "prompt": "prompt_engineering",
        "seo": "seo",
        "hugo": "hugo",
        "supabase": "supabase",
        "marketing": "marketing",
        "content": "content_writing",
        "code": "coding",
        "design": "design",
        "analytics": "analytics",
        "launch": "launch",
        "domain": "domains_hosting",
        "arabic": "arabic",
        "chess": "chess",
    }
    topic_counts = defaultdict(int)
    topic_sessions = defaultdict(list)
    for s in sessions:
        text = (s.get("notes", "") + " " + s.get("body", "")).lower()
        for keyword, topic in topic_markers.items():
            if keyword in text:
                topic_counts[topic] += 1
                topic_sessions[topic].append(s["file"])

    for topic, count in topic_counts.items():
        if count >= 2:
            insights.append({
                "pattern": f"topic_{topic}",
                "category": "recurring_topic",
                "confidence": round(min(0.4 + 0.1 * count, 0.9), 2),
                "evidence_count": count,
                "sessions": topic_sessions[topic][:5],
                "summary": f"Topic '{topic}' appeared in {count} sessions",
                "suggestion": f"Create dedicated skill or resource collection for {topic}",
            })

    return insights


def deduplicate_insights(insights):
    seen = set()
    unique = []
    for ins in insights:
        key = ins["pattern"]
        if key not in seen:
            seen.add(key)
            unique.append(ins)
    return unique


OKF_FRONTMATTER = """---
type: Insight
id: memory-insights
version: 1
created: 2026-06-01
updated: {updated}
references:
  - patterns.md
tags: [memory, insights, patterns]
---

"""

def write_insights(insights):
    lines = [
        OKF_FRONTMATTER.format(updated=datetime.date.today().isoformat()),
        "# Insights\n",
        "Auto-extracted patterns from session history.\n",
    ]
    for ins in sorted(insights, key=lambda x: x["confidence"], reverse=True):
        lines.append(f"- id: {uuid.uuid4().hex[:12]}")
        lines.append(f"  pattern: {ins['pattern']}")
        lines.append(f"  category: {ins['category']}")
        lines.append(f"  confidence: {ins['confidence']}")
        lines.append(f"  evidence_count: {ins['evidence_count']}")
        lines.append(f"  sessions: [{', '.join(ins['sessions'][:3])}]")
        lines.append(f"  summary: {ins['summary']}")
        lines.append(f"  suggestion: {ins['suggestion']}")
        lines.append("")
    INSIGHTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    INSIGHTS_PATH.write_text("\n".join(lines), encoding="utf-8")
    return len(insights)


def write_observation(action, details):
    entry = {
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "action": action,
        "details": details,
    }
    OBS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OBS_PATH, "a", encoding="utf-8") as f:
        import json
        f.write(json.dumps(entry) + "\n")


def main():
    parser = argparse.ArgumentParser(description="Extract insights from session data")
    parser.add_argument("--min-confidence", type=float, default=0.5, help="Minimum confidence threshold")
    args = parser.parse_args()

    sessions = load_sessions()
    if not sessions:
        print("No sessions found.")
        return

    insights = extract_patterns(sessions)
    insights = deduplicate_insights(insights)
    insights = [i for i in insights if i["confidence"] >= args.min_confidence]
    count = write_insights(insights)
    write_observation("extract_insights", {"sessions_scanned": len(sessions), "insights_found": count})
    log_insight("insights_extracted", {
        "sessions_scanned": len(sessions),
        "insights_found": count,
        "min_confidence": args.min_confidence,
        "skills_covered": len(set(s.get("skill", "") for s in sessions)),
    })
    print(f"Scanned {len(sessions)} sessions, extracted {count} insights (min confidence {args.min_confidence})")


if __name__ == "__main__":
    main()
