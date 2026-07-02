import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools.db import get_db
from tools.insight_ledger import log_event
from tools.extract_insights import extract_evolution_patterns
from tools.auto_evolve import evolve_from_session, evolve_from_interactions


def run(event_name, context):
    if event_name != "session:end":
        return None

    patterns = extract_evolution_patterns()
    db = get_db()
    now = datetime.now().isoformat()

    db.execute("INSERT OR REPLACE INTO checkpoint (key, value) VALUES ('last_session_end', ?)", (now,))
    db.commit()

    session_data = context or {}
    evolve_result = evolve_from_session(session_data)
    interaction_result = evolve_from_interactions()

    log_event("session:end", {
        "patterns_found": len(patterns),
        "trait_changes": len(evolve_result.get("trait_changes", [])),
        "insights": evolve_result.get("insights_generated", []),
    })

    return {
        "patterns_found": len(patterns),
        "evolution": evolve_result,
        "interaction_analysis": interaction_result,
        "message": "Session ended, personality evolved",
    }
