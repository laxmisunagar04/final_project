"""
scorecard.py — Final interview scorecard computation.

Computes aggregate scores across all interview dimensions and
returns a dict consumed by the Streamlit scorecard UI.
"""

from __future__ import annotations

import statistics
from datetime import datetime


SCORE_LABELS = {
    (90, 101): ("Exceptional",  "#22c55e", "🏆"),
    (75, 90):  ("Excellent",    "#86efac", "🔥"),
    (60, 75):  ("Good",         "#fbbf24", "👍"),
    (45, 60):  ("Average",      "#fb923c", "⚠️"),
    (0,  45):  ("Needs Work",   "#ef4444", "❌"),
}


def _label(score: float) -> tuple[str, str, str]:
    for (lo, hi), (label, color, emoji) in SCORE_LABELS.items():
        if lo <= score < hi:
            return label, color, emoji
    return "N/A", "#888", "—"


def build_scorecard(session_data: dict, scores: dict[int, dict], feedback: dict) -> dict:
    """
    Build the final scorecard dict from session data, per-question scores,
    and feedback produced by feedback_engine.

    Returns a flat dict ready for rendering by the Streamlit scorecard page.
    """
    if not scores:
        return {}

    totals          = [s["total"]           for s in scores.values()]
    keyword_scores  = [s["keyword_score"]   for s in scores.values()]
    structure_scores= [s["structure_score"] for s in scores.values()]
    confidence_scores=[s["confidence_score"]for s in scores.values()]

    # Normalise sub-scores to 0-100
    def norm(vals: list[float], max_val: float) -> float:
        return round(statistics.mean(vals) / max_val * 100, 1) if vals else 0

    tech_score   = norm(keyword_scores,   40)   # keyword max = 40
    struct_score = norm(structure_scores, 20)   # structure max = 20
    conf_score   = norm(confidence_scores, 15)  # confidence max = 15

    overall = round(statistics.mean(totals), 1)

    # Role readiness: weighted toward technical depth
    role_readiness = round(tech_score * 0.55 + struct_score * 0.25 + conf_score * 0.20, 1)

    # Interview confidence: weighted toward confidence + structure
    interview_confidence = round(conf_score * 0.60 + struct_score * 0.40, 1)

    # Timing analysis
    timings = list(session_data.get("timings", {}).values())
    avg_time = round(statistics.mean(timings), 1) if timings else 0

    # Question-by-question breakdown
    breakdown = []
    for idx, s in scores.items():
        q = session_data["questions"][idx]
        breakdown.append({
            "index":    idx + 1,
            "topic":    q["topic"],
            "question": q["question"][:80] + "…" if len(q["question"]) > 80 else q["question"],
            "score":    s["total"],
            "time_sec": session_data["timings"].get(idx, 0),
        })

    # Session duration
    try:
        start = datetime.fromisoformat(session_data.get("session_start", datetime.now().isoformat()))
        end   = datetime.fromisoformat(session_data.get("session_end",   datetime.now().isoformat()))
        duration_min = round((end - start).total_seconds() / 60, 1)
    except Exception:
        duration_min = 0

    ol_label, ol_color, ol_emoji = _label(overall)
    rr_label, rr_color, rr_emoji = _label(role_readiness)
    ic_label, ic_color, ic_emoji = _label(interview_confidence)

    return {
        # ── Aggregate scores ─────────────────────────────────────────────────
        "overall_score":          overall,
        "role_readiness_score":   role_readiness,
        "interview_confidence":   interview_confidence,
        "technical_score":        tech_score,
        "structure_score":        struct_score,
        "communication_score":    conf_score,

        # ── Labels + colours ─────────────────────────────────────────────────
        "overall_label":    ol_label,
        "overall_color":    ol_color,
        "overall_emoji":    ol_emoji,
        "rr_label":         rr_label,
        "rr_color":         rr_color,
        "rr_emoji":         rr_emoji,
        "ic_label":         ic_label,
        "ic_color":         ic_color,
        "ic_emoji":         ic_emoji,

        # ── Session meta ─────────────────────────────────────────────────────
        "role":             session_data.get("raw_role", "Unknown"),
        "difficulty":       session_data.get("difficulty", "medium").capitalize(),
        "total_questions":  len(session_data["questions"]),
        "answered":         len(scores),
        "avg_time_sec":     avg_time,
        "duration_min":     duration_min,
        "skills":           session_data.get("skills", []),

        # ── Breakdown + feedback ─────────────────────────────────────────────
        "breakdown":        breakdown,
        "weak_topics":      feedback.get("weak_topics", []),
        "unused_skills":    feedback.get("unused_skills", []),
        "roadmap":          feedback.get("roadmap", []),
        "recommended":      feedback.get("recommended", []),

        # ── Radar chart data (for plotly) ────────────────────────────────────
        "radar_labels":     ["Technical Depth", "Communication", "Structure", "Confidence", "Role Readiness"],
        "radar_values":     [tech_score, conf_score * 1.0, struct_score, conf_score, role_readiness],
    }