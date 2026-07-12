import re
from pathlib import Path
import sys

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))

try:
    from tools.db import init_db, match_intent_correction, record_intent_correction, get_intent_corrections
    init_db()
except Exception:
    match_intent_correction = lambda _: None
    record_intent_correction = lambda *a, **kw: None
    get_intent_corrections = lambda: []


def forget_correction(input_text: str) -> bool:
    try:
        from tools.db import get_db
        db = get_db()
        db.execute("DELETE FROM intent_corrections WHERE input_pattern = ?", (input_text,))
        db.commit()
        return True
    except Exception:
        return False


def learn_correction(input_text: str, correct_mode: str, correct_intent: str = "general", notes: str = ""):
    record_intent_correction(input_text, correct_mode, correct_intent, notes)


INTENT_MAP = [
    ("doc", r"make (a |an |)(schedule|document|spreadsheet|xlsx|docx|report)", "MINIMAL"),
    ("quick", r"^(hi|hello|hey|thanks|ok|yes|no|sure|got it|good|bye)", "MINIMAL"),
    ("bug", r"\b(bug|broken|not working|crash|error)\b", "ALGORITHM"),
    ("feature", r"\b(build|create|implement|write( a| an| new|)|add a|new feature|i need a)\b", "ALGORITHM"),
    ("fix", r"\b(fix|repair|correct|resolve)\b", "ALGORITHM"),
    ("plan", r"\b(plan|roadmap|milestone|outline|scaffold)\b", "ALGORITHM"),
    ("deploy", r"\b(deploy|push|release|publish|ship)\b", "ALGORITHM"),
    ("learn", r"\b(learn|teach|make you better|fix yourself|improve yourself)\b", "NATIVE"),
    ("session", r"\b(session|practice|worked on|practiced|studied)\b", "NATIVE"),
    ("review", r"\b(review|audit|inspect|look at)\b", "NATIVE"),
    ("research", r"\b(research|search|find out|investigate|look into)\b", "NATIVE"),
    ("question", r"^(what|how|why|when|where|which|who|can you|could you|tell me)", "NATIVE"),
    ("doc", r"\b(schedule|document|format|xlsx|docx|spreadsheet)\b", "MINIMAL"),
]

def classify(user_input: str) -> dict:
    text = user_input.lower().strip()
    if len(text) < 3:
        return {"mode": "MINIMAL", "intent": "greeting", "confidence": 1.0}

    correction = match_intent_correction(text)
    if correction:
        return correction

    for intent, pattern, default_mode in INTENT_MAP:
        if re.search(pattern, text):
            if intent == "question" and len(text) < 15:
                return {"mode": "MINIMAL", "intent": intent, "confidence": 0.8}
            return {"mode": default_mode, "intent": intent, "confidence": 0.7}

    session_words = {"session", "practice", "worked", "today", "yesterday"}
    conversation_triggers = {"what", "how", "why", "can you", "could you", "tell me", "think"}

    word_set = set(text.split())
    has_conversation = any(t in text for t in conversation_triggers)

    if word_set & session_words or has_conversation:
        return {"mode": "NATIVE", "intent": "conversation", "confidence": 0.6}

    if any(w in text for w in ("build", "make", "fix", "create", "implement")):
        return {"mode": "ALGORITHM", "intent": "unknown_task", "confidence": 0.5}

    return {"mode": "NATIVE", "intent": "general", "confidence": 0.4}


def effort_tier(user_input: str) -> str:
    text = user_input.lower()
    long_wind = len(text.split()) > 50
    mentions_multi = any(w in text for w in ("and", "then", "after", "also", "multiple", "all", "several"))
    mentions_test = "test" in text
    mentions_deploy = any(w in text for w in ("deploy", "push", "release"))

    if mentions_deploy and (long_wind or mentions_multi):
        return "E4"
    if long_wind and mentions_multi:
        return "E3"
    if long_wind or mentions_test or mentions_multi:
        return "E2"
    return "E1"
