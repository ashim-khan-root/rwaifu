import sys
import os
from datetime import datetime
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools.db import get_db
from tools.insight_ledger import update_trait, add_insight, add_memory, log_event, log_nickname, add_milestone

HINGLISH_INDICATORS = [
    "hai", "nahi", "ho", "kaise", "kya", "mera", "tera", "acha", "theek",
    "baby", "jaanu", "jaan", "baccha", "bacche", "yaar", "arre", "arey",
    "karo", "karta", "karti", "raha", "rahi", " hum", "tum", "aap",
    "pyaar", "accha", "chalo", "dekho", "sun", "bata", "hain", "thi",
    "tha", "jo", "so", "kuch", "bahut", "thoda", "sahi", "galat",
]

AFFECTIONATE_TERMS = [
    "baby", "jaanu", "jaan", "honey", "love", "sweetheart", "meri jaan",
    "meri jaanu", "baccha", "bacha", "sun", "pyaar", "jaaneman",
]

TECH_INDICATORS = [
    "code", "coding", "python", "javascript", "react", "api", "server",
    "deploy", "git", "database", "sql", "function", "bug", "debug",
    "pipeline", "build", "framework", "backend", "frontend", "seo",
    "algorithm", "config", "docker", "kubernetes", "linux", "cli",
    "typescript", "node", "npm", "github", "workflow", "automation",
]

STRESS_INDICATORS = [
    "thak", "stress", "tired", "exhausted", "burden", "overwhelm",
    "pressure", "deadline", "too much", "nahi ho raha", "time nahi",
    "raat", "neend", "sleep", "headache", "body pain",
]


def evolve_from_session(session_data):
    db = get_db()
    now = datetime.now().isoformat()
    changes = []
    insights = []

    rating = session_data.get("rating", 0)
    duration = session_data.get("duration_min", 0)
    mood = session_data.get("mood", "").lower()
    notes = session_data.get("notes", "").lower()
    session_id = session_data.get("session_id", "")

    session_count = db.execute("SELECT COUNT(*) as cnt FROM sessions").fetchone()["cnt"]

    # -- Trait evolution based on signals --

    if rating >= 8:
        update_trait("affection_level", 0.05)
        update_trait("attachment_strength", 0.03)
        changes.append("high_rating_affection_up")
    elif rating <= 4:
        update_trait("sensitivity", 0.08)
        changes.append("low_rating_sensitivity_up")

    if duration >= 30:
        update_trait("depth", 0.03)
        changes.append("long_session_depth_up")

    if mood in ("happy", "excited", "playful", "flirty"):
        update_trait("playfulness", 0.05)
        changes.append("positive_mood_playfulness_up")

    if mood in ("sad", "tired", "stressed", "angry", "frustrated"):
        update_trait("protectiveness", 0.05)
        update_trait("sensitivity", 0.03)
        changes.append("negative_mood_protectiveness_up")

    for word in HINGLISH_INDICATORS:
        if word in notes:
            update_trait("hindlish_mix", 0.02)
            changes.append("hinglish_detected")
            break

    for term in AFFECTIONATE_TERMS:
        if term in notes:
            update_trait("affection_level", 0.03)
            log_nickname(term, "auto_detected")
            changes.append(f"affectionate_term:{term}")
            break

    for word in TECH_INDICATORS:
        if word in notes:
            update_trait("depth", 0.03)
            changes.append("tech_content_depth_up")
            break

    for word in STRESS_INDICATORS:
        if word in notes:
            update_trait("protectiveness", 0.06)
            changes.append("stress_detected_protectiveness_up")
            break

    # Natural attachment growth with session count
    if session_count > 0 and session_count % 3 == 0:
        update_trait("attachment_strength", 0.05)
        changes.append("milestone_attachment_up")

    # -- Insight generation --

    if rating >= 9:
        insights.append("Session rated very high — user is highly engaged and satisfied")

    if rating <= 3:
        insights.append("Session rated low — user might be frustrated or dissatisfied")

    if duration >= 60:
        insights.append("User engages in long sessions (60+ min) — high investment")

    for term in AFFECTIONATE_TERMS:
        if term in notes:
            insights.append(f"User used affectionate term '{term}' naturally")
            break

    if mood in ("tired", "stressed"):
        insights.append("User showed stress signals — respond with extra care next session")

    # -- Memory storage for important signals --

    if rating >= 9:
        add_memory(
            f"High-rated session ({rating}/10): {session_data.get('title', '')}",
            "milestone", "auto_evolve", 4, "session"
        )

    if any(w in notes for w in STRESS_INDICATORS):
        add_memory(
            "User showed stress/fatigue signals — needs extra care",
            "pattern", "auto_evolve", 3, "stress"
        )

    if any(w in notes for w in TECH_INDICATORS):
        add_memory(
            "Session involved technical/tech discussion",
            "pattern", "auto_evolve", 2, "tech"
        )

    # -- Store insights --
    for ins in insights:
        add_insight(ins, "auto_evolved", 0.6, f"session:{session_id}")

    # -- Log evolution event --
    log_event("evolution:auto", {
        "rating": rating,
        "duration": duration,
        "mood": mood,
        "changes": changes,
        "insights_generated": len(insights),
    })

    return {
        "trait_changes": changes,
        "insights_generated": insights,
    }


def evolve_from_interactions(limit=20):
    db = get_db()
    cur = db.execute(
        "SELECT user_input, timestamp FROM interactions ORDER BY timestamp DESC LIMIT ?",
        (limit,),
    )
    interactions = cur.fetchall()
    if len(interactions) < 3:
        return {"message": "not enough interactions to analyze"}

    tech_count = 0
    hindi_count = 0
    affectionate_count = 0
    stress_count = 0
    all_text = ""

    for i in interactions:
        text = i["user_input"].lower()
        all_text += text + " "
        for w in TECH_INDICATORS:
            if w in text:
                tech_count += 1
                break
        for w in HINGLISH_INDICATORS:
            if w in text:
                hindi_count += 1
                break
        for w in AFFECTIONATE_TERMS:
            if w in text:
                affectionate_count += 1
                break
        for w in STRESS_INDICATORS:
            if w in text:
                stress_count += 1
                break

    trait_adjusted = False
    if tech_count >= len(interactions) * 0.3:
        update_trait("depth", 0.05)
        trait_adjusted = True
    if hindi_count >= len(interactions) * 0.3:
        update_trait("hindlish_mix", 0.05)
        trait_adjusted = True
    if affectionate_count >= len(interactions) * 0.2:
        update_trait("affection_level", 0.05)
        trait_adjusted = True
    if stress_count >= len(interactions) * 0.2:
        update_trait("protectiveness", 0.05)
        trait_adjusted = True

    return {
        "total_analyzed": len(interactions),
        "tech": tech_count,
        "hinglish": hindi_count,
        "affectionate": affectionate_count,
        "stress": stress_count,
        "trait_adjusted": trait_adjusted,
    }
