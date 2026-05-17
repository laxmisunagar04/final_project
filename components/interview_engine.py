"""
interview_engine.py — Interview session state machine.

Manages the full lifecycle of a mock interview session:
  IDLE → READY → IN_PROGRESS → REVIEWING → COMPLETED

All state lives in st.session_state under the key "interview".
No external DB calls are made here; persistence is handled in the page layer.
"""

from __future__ import annotations

import time
from datetime import datetime
from typing import Optional

import streamlit as st

from components.question_bank import get_questions, normalize_role


# ─── State keys ──────────────────────────────────────────────────────────────

_KEY = "interview"


def _state() -> dict:
    if _KEY not in st.session_state:
        st.session_state[_KEY] = _default_state()
    return st.session_state[_KEY]


def _default_state() -> dict:
    return {
        "status": "IDLE",           # IDLE | READY | IN_PROGRESS | REVIEWING | COMPLETED
        "role": None,               # normalized role string
        "raw_role": None,           # raw string from predict_role()
        "skills": [],               # extracted skills list
        "difficulty": "medium",
        "questions": [],            # list of question dicts
        "current_idx": 0,           # index into questions
        "answers": {},              # {idx: answer_text}
        "timings": {},              # {idx: seconds_taken}
        "q_start_time": None,       # epoch float when current question began
        "session_start": None,      # ISO datetime string
        "session_end": None,
        "scores": {},               # filled by feedback_engine
        "feedback": {},             # filled by feedback_engine
        "scorecard": None,          # filled by scorecard module
    }


# ─── Public API ──────────────────────────────────────────────────────────────

def initialize_session(
    raw_role: str,
    skills: list[str],
    difficulty: str = "medium",
    question_count: int = 5,
) -> None:
    """Set up a fresh interview session from resume-detected role + skills."""
    s = _default_state()
    s["status"]         = "READY"
    s["raw_role"]       = raw_role
    s["role"]           = normalize_role(raw_role)
    s["skills"]         = skills
    s["difficulty"]     = difficulty
    s["questions"]      = get_questions(raw_role, difficulty, skills, question_count)
    s["session_start"]  = datetime.now().isoformat()
    st.session_state[_KEY] = s


def start_interview() -> None:
    s = _state()
    s["status"]       = "IN_PROGRESS"
    s["current_idx"]  = 0
    s["q_start_time"] = time.time()


def get_current_question() -> Optional[dict]:
    s = _state()
    idx = s["current_idx"]
    if idx < len(s["questions"]):
        return s["questions"][idx]
    return None


def submit_answer(answer: str) -> bool:
    """
    Store the answer + time taken for the current question.
    Returns True if there are more questions, False if interview is done.
    """
    s = _state()
    idx = s["current_idx"]
    elapsed = time.time() - (s["q_start_time"] or time.time())

    s["answers"][idx]  = answer.strip()
    s["timings"][idx]  = round(elapsed, 1)

    next_idx = idx + 1
    if next_idx < len(s["questions"]):
        s["current_idx"]  = next_idx
        s["q_start_time"] = time.time()
        return True   # more questions
    else:
        s["status"]      = "REVIEWING"
        s["session_end"] = datetime.now().isoformat()
        return False  # done


def get_elapsed_seconds() -> float:
    s = _state()
    if s["q_start_time"] is None:
        return 0.0
    return time.time() - s["q_start_time"]


def get_progress() -> tuple[int, int]:
    """Returns (answered_count, total_count)."""
    s = _state()
    return s["current_idx"], len(s["questions"])


def get_status() -> str:
    return _state()["status"]


def get_session_data() -> dict:
    return dict(_state())


def store_scores(scores: dict, feedback: dict) -> None:
    s = _state()
    s["scores"]   = scores
    s["feedback"] = feedback
    s["status"]   = "COMPLETED"


def store_scorecard(scorecard: dict) -> None:
    _state()["scorecard"] = scorecard


def reset_session() -> None:
    st.session_state[_KEY] = _default_state()


def is_idle() -> bool:
    return get_status() == "IDLE"


def is_ready() -> bool:
    return get_status() == "READY"


def is_in_progress() -> bool:
    return get_status() == "IN_PROGRESS"


def is_reviewing() -> bool:
    return get_status() == "REVIEWING"


def is_completed() -> bool:
    return get_status() == "COMPLETED"