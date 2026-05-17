"""
pages/mock_interview.py — AI Mock Interview (Role-Detection Based)

Flow:
  STEP 1 — Upload Resume   → extract skills + auto-predict role
  STEP 2 — Profile Review  → confirm role, choose difficulty & question count
  STEP 3 — Live Interview  → question-by-question with timer
  STEP 4 — Reviewing       → score + feedback computation
  STEP 5 — Scorecard       → competency radar, per-question feedback, roadmap

All role prediction reuses the existing resume_parser + model modules.
No webcam, no tab-monitoring, no proctoring dependencies.
"""

import time

import plotly.graph_objects as go
import streamlit as st

from components import feedback_engine as fe
from components import interview_engine as ie
from components import scorecard as sc
from auth import get_user, require_login
from components.sidebar import render_sidebar
from database import get_student_profile, init_db, save_student_profile
from model import predict_role
from resume_parser import extract_resume_data

# ─── Page setup ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Mock Interview · AI Career Twin",
    page_icon="🎤",
    layout="wide",
    initial_sidebar_state="expanded",
)
init_db()
render_sidebar()
require_login("student")

user = get_user()

# ─── Global CSS ──────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Syne:wght@400;700;800&display=swap');

        /* ── Typography ── */
        .interview-header {
            font-family: 'Syne', sans-serif;
            font-size: 2.4rem;
            font-weight: 800;
            background: linear-gradient(135deg, #e94560, #f5a623);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            line-height: 1.15;
        }
        .section-label {
            color: #9ca3af;
            font-size: 0.7rem;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            font-weight: 600;
            margin-bottom: 10px;
        }

        /* ── Role badge ── */
        .role-badge {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            background: linear-gradient(135deg, #1e3a5f, #0f3460);
            border: 1px solid #3b82f6;
            color: #93c5fd;
            padding: 10px 22px;
            border-radius: 30px;
            font-size: 1.05rem;
            font-weight: 700;
            letter-spacing: 0.5px;
        }
        .role-badge-sm {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: #1e3a5f22;
            border: 1px solid #3b82f6;
            color: #93c5fd;
            padding: 5px 14px;
            border-radius: 20px;
            font-size: 0.82rem;
            font-weight: 600;
        }

        /* ── Skill chips ── */
        .skill-chip {
            background: #1e3a1e;
            color: #86efac;
            padding: 4px 13px;
            border-radius: 20px;
            font-size: 0.78rem;
            margin: 3px;
            display: inline-block;
            border: 1px solid #166534;
        }
        .skill-chip-missing {
            background: #3a1a1a;
            color: #fca5a5;
            padding: 4px 13px;
            border-radius: 20px;
            font-size: 0.78rem;
            margin: 3px;
            display: inline-block;
            border: 1px solid #7f1d1d;
        }

        /* ── Step progress bar ── */
        .step-row {
            display: flex;
            align-items: center;
            gap: 6px;
            margin-bottom: 20px;
        }
        .step-pill {
            padding: 4px 14px;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
            letter-spacing: 0.5px;
        }
        .step-pill.done    { background: #166534; color: #86efac; }
        .step-pill.active  { background: #e94560; color: #fff; }
        .step-pill.pending { background: #1f2937; color: #4b5563; }
        .step-sep { color: #374151; font-size: 0.7rem; }

        /* ── Cards ── */
        .stat-card {
            background: #111827;
            border: 1px solid #1f2937;
            border-radius: 14px;
            padding: 20px 16px;
            text-align: center;
        }
        .stat-value {
            font-size: 1.9rem;
            font-weight: 800;
            color: #e94560;
        }
        .stat-label {
            color: #6b7280;
            font-size: 0.75rem;
            margin-top: 4px;
        }
        .info-card {
            background: #111827;
            border: 1px solid #1f2937;
            border-radius: 14px;
            padding: 20px 22px;
        }
        .question-card {
            background: linear-gradient(135deg, #0f172a, #1e1b4b);
            border: 1px solid #2a2a4a;
            border-left: 5px solid #e94560;
            border-radius: 18px;
            padding: 30px 34px;
            margin: 18px 0 12px;
        }
        .q-meta {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 14px;
        }
        .q-num {
            color: #e94560;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.8rem;
            font-weight: 700;
        }
        .q-topic {
            background: #2a1a3e;
            color: #c084fc;
            padding: 3px 11px;
            border-radius: 12px;
            font-size: 0.73rem;
            font-weight: 600;
        }
        .q-diff {
            padding: 3px 11px;
            border-radius: 12px;
            font-size: 0.73rem;
            font-weight: 600;
        }
        .q-diff.easy   { background: #1a3a1a; color: #86efac; }
        .q-diff.medium { background: #1a2a3a; color: #7dd3fc; }
        .q-diff.hard   { background: #3a1a1a; color: #fca5a5; }
        .q-text {
            font-size: 1.15rem;
            font-weight: 600;
            line-height: 1.6;
            color: #e2e8f0;
        }
        .follow-card {
            background: #0f172a;
            border: 1px dashed #374151;
            border-radius: 10px;
            padding: 12px 16px;
            margin-top: 14px;
            color: #6b7280;
            font-size: 0.83rem;
        }
        .feedback-card {
            background: #111827;
            border: 1px solid #1f2937;
            border-radius: 12px;
            padding: 18px;
            margin-bottom: 12px;
        }
        .roadmap-item {
            background: #0f172a;
            border-left: 3px solid #e94560;
            padding: 12px 16px;
            border-radius: 8px;
            margin-bottom: 10px;
            font-size: 0.88rem;
            color: #d1d5db;
        }
        .readiness-bar-wrap {
            background: #1f2937;
            border-radius: 6px;
            height: 8px;
            overflow: hidden;
            margin-top: 6px;
        }
        .readiness-bar-fill {
            height: 100%;
            border-radius: 6px;
            transition: width 0.6s ease;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# ─── Page header ─────────────────────────────────────────────────────────────
st.markdown('<div class="interview-header">🎤 AI Mock Interview</div>', unsafe_allow_html=True)
st.markdown(
    '<p style="color:#6b7280;margin-top:6px;">Role-detection based &nbsp;·&nbsp; '
    'Personalised questions &nbsp;·&nbsp; Instant feedback</p>',
    unsafe_allow_html=True,
)
st.divider()


# ─── Step progress bar ────────────────────────────────────────────────────────
_STEPS = ["Resume", "Profile", "Interview", "Scorecard"]


def _step_bar(current: int) -> None:
    """Render a pill-style step indicator. current = 0-indexed active step."""
    pills = []
    for i, label in enumerate(_STEPS):
        if i < current:
            cls = "done"
            prefix = "✓ "
        elif i == current:
            cls = "active"
            prefix = ""
        else:
            cls = "pending"
            prefix = ""
        pills.append(f'<span class="step-pill {cls}">{prefix}{label}</span>')
        if i < len(_STEPS) - 1:
            pills.append('<span class="step-sep">›</span>')

    st.markdown(
        f'<div class="step-row">{"".join(pills)}</div>',
        unsafe_allow_html=True,
    )


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _skill_chips(skills: list[str], variant: str = "match") -> str:
    css = "skill-chip" if variant == "match" else "skill-chip-missing"
    return " ".join(f'<span class="{css}">{s.strip()}</span>' for s in skills if s.strip())


def _role_badge(role: str, size: str = "lg") -> str:
    cls = "role-badge" if size == "lg" else "role-badge-sm"
    return f'<span class="{cls}">🎯 {role}</span>'


def _diff_color(diff: str) -> str:
    return {"easy": "#86efac", "medium": "#7dd3fc", "hard": "#fca5a5"}.get(diff, "#cdd6f4")


def _readiness_pct(skills: list[str], role: str) -> int:
    """Rough % of required skills the student already has."""
    from components.question_bank import normalize_role, QUESTION_BANK
    norm = normalize_role(role)
    pool = QUESTION_BANK.get(norm, {})
    all_topics = set()
    for qs in pool.values():
        for q in qs:
            all_topics.add(q["topic"].lower())
    if not all_topics:
        return 50
    skill_set = {s.lower() for s in skills}
    matched   = sum(1 for t in all_topics if any(w in t for w in skill_set))
    return min(int(matched / len(all_topics) * 100), 95)



def _do_upload_flow() -> None:
    """Render the file uploader + process resume + start interview."""
    uploaded = st.file_uploader(
        "Drop your resume PDF here",
        type="pdf",
        key="interview_upload",
        help="Supports standard PDF resumes up to 10 MB",
    )

    if not uploaded:
        st.markdown(
            """
            <div style="background:#111827;border:1px dashed #374151;border-radius:12px;
                        padding:28px;text-align:center;margin-top:12px;">
                <div style="font-size:2.5rem;margin-bottom:10px;">📄</div>
                <div style="color:#6b7280;font-size:0.88rem;">
                    Upload a PDF resume to auto-detect your role and generate personalised questions
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    # ── Parse ──────────────────────────────────────────────────────────────────
    with st.spinner("🔍 Parsing resume …"):
        skills_raw, text = extract_resume_data(uploaded)

    skills = [s.strip() for s in skills_raw if s.strip()] if skills_raw else []

    if not skills:
        st.warning(
            "⚠️ No skills could be extracted from this resume. "
            "Using a fallback set for demo purposes."
        )
        skills = ["python", "sql", "communication"]

    # ── Predict ────────────────────────────────────────────────────────────────
    with st.spinner("🎯 Predicting role …"):
        raw_role = predict_role(text)

    # ── Persist to DB so Resume Analysis page also benefits ───────────────────
    existing = get_student_profile(user["id"])
    save_student_profile(
        student_id    =user["id"],
        skills        =skills,
        predicted_role=raw_role,
        placement_prob=existing["placement_prob"]  if existing else None,
        cgpa          =existing["cgpa"]            if existing else 0.0,
        coding_score  =existing["coding_score"]   if existing else 0,
        projects      =existing["projects"]        if existing else 0,
        internships   =existing["internships"]     if existing else 0,
        communication =existing["communication"]  if existing else 5,
    )

    # ── Display detection result ───────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.success(f"✅ Role detected from your resume!")

    col_r, col_s = st.columns([1, 2])
    with col_r:
        readiness  = _readiness_pct(skills, raw_role)
        bar_color  = "#22c55e" if readiness >= 70 else "#fbbf24" if readiness >= 40 else "#ef4444"
        st.markdown(
            f"""
            <div class="stat-card">
                <div class="section-label">Detected Role</div>
                {_role_badge(raw_role)}
                <div style="margin-top:14px;" class="section-label">Role Readiness</div>
                <div style="font-size:2rem;font-weight:800;color:{bar_color};">{readiness}%</div>
                <div class="readiness-bar-wrap">
                    <div class="readiness-bar-fill"
                         style="width:{readiness}%;background:{bar_color};"></div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_s:
        st.markdown(
            f"""
            <div class="info-card">
                <div class="section-label">Extracted Skills ({len(skills)})</div>
                {_skill_chips(skills[:20])}
                {"" if len(skills) <= 20 else
                 f'<span style="color:#6b7280;font-size:0.75rem;margin-left:6px;">'
                 f'+{len(skills)-20} more</span>'}
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    col_a, col_b = st.columns(2)
    with col_a:
        diff = st.selectbox("🎚️ Difficulty", ["easy", "medium", "hard"], index=1, key="new_diff")
    with col_b:
        q_count = st.slider("❓ Questions", min_value=3, max_value=10, value=5, key="new_qcount")

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("🚀 Start Interview", type="primary", use_container_width=True, key="start_new"):
        ie.initialize_session(raw_role, skills, diff, q_count)
        st.session_state.pop("_show_upload", None)
        st.rerun()


# ════════════════════════════════════════════════════════════════════════════════
# STEP 2 — READY: Profile confirmation before interview

# ════════════════════════════════════════════════════════════════════════════════
# STEP 1 — IDLE: Resume upload + role detection
# ════════════════════════════════════════════════════════════════════════════════
if ie.is_idle():
    _step_bar(0)

    profile = get_student_profile(user["id"])

    # ── Option A: resume already analysed ─────────────────────────────────────
    if profile and profile.get("predicted_role") and profile.get("skills"):
        stored_role   = profile["predicted_role"]
        stored_skills = [s.strip() for s in profile["skills"].split(",") if s.strip()]
        readiness     = _readiness_pct(stored_skills, stored_role)
        bar_color     = "#22c55e" if readiness >= 70 else "#fbbf24" if readiness >= 40 else "#ef4444"

        st.markdown("## 📁 Saved Resume Profile")
        st.markdown(
            '<p style="color:#6b7280;font-size:0.88rem;">'
            'Your last resume analysis was found. You can start immediately or re-upload a new resume.</p>',
            unsafe_allow_html=True,
        )
        st.markdown("<br>", unsafe_allow_html=True)

        # Role + readiness row
        col_role, col_ready = st.columns([2, 1])
        with col_role:
            st.markdown(
                f"""
                <div class="info-card">
                    <div class="section-label">Detected Role</div>
                    {_role_badge(stored_role)}
                    <div style="margin-top:16px;">
                        <div class="section-label">Extracted Skills ({len(stored_skills)})</div>
                        {_skill_chips(stored_skills[:16])}
                        {"" if len(stored_skills) <= 16 else
                         f'<span style="color:#6b7280;font-size:0.75rem;margin-left:6px;">'
                         f'+{len(stored_skills)-16} more</span>'}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with col_ready:
            st.markdown(
                f"""
                <div class="stat-card" style="height:100%;">
                    <div class="section-label">Role Readiness</div>
                    <div style="font-size:2.6rem;font-weight:800;color:{bar_color};">{readiness}%</div>
                    <div class="readiness-bar-wrap">
                        <div class="readiness-bar-fill"
                             style="width:{readiness}%;background:{bar_color};"></div>
                    </div>
                    <div style="color:#6b7280;font-size:0.72rem;margin-top:8px;">
                        Based on skill overlap
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)

        col_a, col_b, col_c = st.columns(3)
        with col_a:
            diff = st.selectbox(
                "🎚️ Difficulty",
                ["easy", "medium", "hard"],
                index=1,
                key="stored_diff",
                help="Easy: conceptual | Medium: applied | Hard: system design",
            )
        with col_b:
            q_count = st.slider("❓ Questions", min_value=3, max_value=10, value=5, key="stored_qcount")
        with col_c:
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown(
                f'<div style="background:#0d2a1a;border:1px solid #166534;border-radius:10px;'
                f'padding:10px 14px;color:#86efac;font-size:0.82rem;">'
                f'⚡ {q_count} {diff} questions for <b>{stored_role}</b></div>',
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)
        col_btn1, col_btn2, _ = st.columns([1, 1, 2])
        with col_btn1:
            if st.button("🚀 Start Interview", type="primary", use_container_width=True, key="start_saved"):
                ie.initialize_session(stored_role, stored_skills, diff, q_count)
                st.rerun()
        with col_btn2:
            if st.button("🔄 Upload New Resume", use_container_width=True, key="toggle_upload"):
                st.session_state["_show_upload"] = True
                st.rerun()

        if st.session_state.get("_show_upload"):
            st.markdown("---")
            st.markdown("#### 📎 Upload New Resume")
            _do_upload_flow()

    # ── Option B: no saved profile ─────────────────────────────────────────────
    else:
        st.markdown("## 📄 Upload Your Resume")
        st.markdown(
            '<p style="color:#6b7280;">Your role will be automatically detected from your resume. '
            'No manual selection required.</p>',
            unsafe_allow_html=True,
        )
        st.markdown("<br>", unsafe_allow_html=True)
        _do_upload_flow()


# ════════════════════════════════════════════════════════════════════════════════
elif ie.is_ready():
    _step_bar(1)
    data = ie.get_session_data()

    st.markdown("## ✅ Interview Ready")
    st.markdown(
        '<p style="color:#6b7280;">Review your profile below. Click Begin when you\'re ready.</p>',
        unsafe_allow_html=True,
    )
    st.markdown("<br>", unsafe_allow_html=True)

    # Summary metrics
    m1, m2, m3 = st.columns(3)
    with m1:
        st.markdown(
            f'<div class="stat-card">'
            f'<div class="section-label">Detected Role</div>'
            f'<div style="margin-top:6px;">{_role_badge(data["raw_role"], "sm")}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with m2:
        diff_col = _diff_color(data["difficulty"])
        st.markdown(
            f'<div class="stat-card">'
            f'<div class="section-label">Difficulty</div>'
            f'<div class="stat-value" style="color:{diff_col};">{data["difficulty"].capitalize()}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with m3:
        st.markdown(
            f'<div class="stat-card">'
            f'<div class="section-label">Questions</div>'
            f'<div class="stat-value">{len(data["questions"])}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    col_sk, col_tp = st.columns(2)
    with col_sk:
        st.markdown(
            f'<div class="info-card">'
            f'<div class="section-label">Your Skills</div>'
            f'{_skill_chips(data["skills"][:18])}'
            f'</div>',
            unsafe_allow_html=True,
        )
    with col_tp:
        topics    = list(dict.fromkeys(q["topic"] for q in data["questions"]))
        topic_str = " ".join(
            f'<span style="background:#1a1a3a;color:#c084fc;padding:4px 12px;'
            f'border-radius:20px;font-size:0.78rem;margin:2px;display:inline-block;">{t}</span>'
            for t in topics
        )
        st.markdown(
            f'<div class="info-card">'
            f'<div class="section-label">Topics Covered</div>'
            f'{topic_str}'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)
    st.info(
        "💡 **Tip:** Answer as if explaining to a technical interviewer. "
        "Use 'First … Then … Finally …' structure. Reference your past projects where relevant."
    )

    c1, c2 = st.columns([1, 1])
    with c1:
        if st.button("🎤 Begin Interview", type="primary", use_container_width=True):
            ie.start_interview()
            st.rerun()
    with c2:
        if st.button("🔄 Re-upload Resume", use_container_width=True):
            ie.reset_session()
            st.rerun()


# ════════════════════════════════════════════════════════════════════════════════
# STEP 3 — IN_PROGRESS: Live question-by-question
# ════════════════════════════════════════════════════════════════════════════════
elif ie.is_in_progress():
    _step_bar(2)

    q              = ie.get_current_question()
    answered, total = ie.get_progress()
    data           = ie.get_session_data()
    diff           = data["difficulty"]
    diff_col       = _diff_color(diff)

    # ── Top progress strip ────────────────────────────────────────────────────
    pct = answered / total
    st.markdown(
        f"""
        <div style="display:flex;align-items:center;justify-content:space-between;
                    margin-bottom:6px;">
            <span style="color:#6b7280;font-size:0.82rem;">
                Question <b style="color:#e2e8f0;">{answered + 1}</b> of {total}
            </span>
            <span style="gap:8px;display:flex;align-items:center;">
                {_role_badge(data["raw_role"], "sm")}
                <span class="q-diff {diff}">{diff.capitalize()}</span>
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.progress(pct)
    st.markdown("<br>", unsafe_allow_html=True)

    # ── Two-column layout: question left, sidebar right ───────────────────────
    left, right = st.columns([3, 1])

    with right:
        # Session summary panel
        st.markdown(
            f"""
            <div class="info-card">
                <div class="section-label">Session Info</div>
                <div style="color:#d1d5db;font-size:0.82rem;line-height:2;">
                    🎯 {data["raw_role"]}<br>
                    🎚️ {diff.capitalize()}<br>
                    ❓ {total} questions<br>
                    ✅ {answered} answered<br>
                    ⏳ {total - answered} remaining
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("<br>", unsafe_allow_html=True)

        # Skills reminder
        skill_preview = data["skills"][:8]
        st.markdown(
            f'<div class="info-card">'
            f'<div class="section-label">Your Skills</div>'
            f'{_skill_chips(skill_preview)}'
            f'</div>',
            unsafe_allow_html=True,
        )

        st.markdown("<br>", unsafe_allow_html=True)

        # Timer display (approximate — updates on rerun)
        elapsed = int(ie.get_elapsed_seconds())
        mins, secs = divmod(elapsed, 60)
        timer_color = "#ef4444" if elapsed > 120 else "#fbbf24" if elapsed > 60 else "#22c55e"
        st.markdown(
            f"""
            <div class="stat-card">
                <div class="section-label">Time on Question</div>
                <div style="font-size:1.8rem;font-weight:800;color:{timer_color};
                            font-family:'JetBrains Mono',monospace;">
                    {mins:02d}:{secs:02d}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with left:
        # Question card
        st.markdown(
            f"""
            <div class="question-card">
                <div class="q-meta">
                    <span class="q-num">Q{answered + 1} / {total}</span>
                    <span class="q-topic">📌 {q["topic"]}</span>
                    <span class="q-diff {diff}">{diff.capitalize()}</span>
                </div>
                <div class="q-text">{q["question"]}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Answer area
        answer = st.text_area(
            "✍️ Your Answer",
            placeholder=(
                "Write a clear, structured answer.\n\n"
                "Good structure: Define the concept → Explain how it works → "
                "Give a real-world example → Mention tradeoffs."
            ),
            height=180,
            key=f"ans_{answered}",
        )

        # Follow-up hint (collapsed)
        if q.get("follow_up"):
            with st.expander("💡 Possible follow-up question"):
                st.markdown(
                    f'<div class="follow-card">🔍 Be ready for: <i>{q["follow_up"]}</i></div>',
                    unsafe_allow_html=True,
                )

        st.markdown("<br>", unsafe_allow_html=True)

        btn_label = "Next Question →" if (answered + 1) < total else "Finish & Get Feedback ✓"
        col_submit, col_skip = st.columns([4, 1])
        with col_submit:
            if st.button(btn_label, type="primary", use_container_width=True):
                if not answer.strip():
                    st.warning("⚠️ Please write an answer before continuing.")
                else:
                    ie.submit_answer(answer)
                    st.rerun()
        with col_skip:
            if st.button("Skip ⏭️", use_container_width=True, help="Skip this question"):
                ie.submit_answer("[SKIPPED]")
                st.rerun()


# ════════════════════════════════════════════════════════════════════════════════
# STEP 4 — REVIEWING: Compute scores (no UI, auto-transitions)
# ════════════════════════════════════════════════════════════════════════════════
elif ie.is_reviewing():
    _step_bar(3)

    st.markdown(
        """
        <div style="text-align:center;padding:48px 0;">
            <div style="font-size:3rem;margin-bottom:12px;">⚙️</div>
            <div style="font-size:1.3rem;font-weight:600;color:#e2e8f0;margin-bottom:6px;">
                Analysing your answers…
            </div>
            <div style="color:#6b7280;font-size:0.88rem;">
                Running feedback engine and building your scorecard
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.spinner("Computing scores and generating personalised feedback …"):
        data   = ie.get_session_data()
        scores = fe.score_all_answers(data)
        feedbk = fe.generate_feedback(data, scores)
        card   = sc.build_scorecard(data, scores, feedbk)
        ie.store_scores(scores, feedbk)
        ie.store_scorecard(card)

    st.rerun()


# ════════════════════════════════════════════════════════════════════════════════
# STEP 5 — COMPLETED: Full scorecard
# ════════════════════════════════════════════════════════════════════════════════
elif ie.is_completed():
    _step_bar(3)

    data   = ie.get_session_data()
    card   = data.get("scorecard", {})
    feedbk = data.get("feedback",  {})

    if not card:
        st.error("Scorecard data is missing. Please restart the interview.")
        if st.button("🔄 Restart"):
            ie.reset_session()
            st.rerun()
        st.stop()

    # ── Hero banner ───────────────────────────────────────────────────────────
    st.markdown(
        f"""
        <div style="text-align:center;padding:36px;
                    background:linear-gradient(135deg,#0f172a,#1e1b4b);
                    border-radius:22px;border:1px solid #2a2a4a;margin-bottom:28px;">
            <div style="font-size:3.5rem;margin-bottom:8px;">{card["overall_emoji"]}</div>
            <div style="font-size:3.2rem;font-weight:800;color:{card["overall_color"]};">
                {card["overall_score"]}%
            </div>
            <div style="font-size:1.25rem;color:#cdd6f4;font-weight:600;margin-top:4px;">
                {card["overall_label"]} Performance
            </div>
            <div style="color:#6b7280;font-size:0.85rem;margin-top:10px;">
                {card["role"]} &nbsp;·&nbsp; {card["difficulty"]} &nbsp;·&nbsp;
                {card["total_questions"]} Questions &nbsp;·&nbsp; {card["duration_min"]} min
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Four key metrics ──────────────────────────────────────────────────────
    m1, m2, m3, m4 = st.columns(4)
    for col, (label, val, color) in zip(
        [m1, m2, m3, m4],
        [
            ("🎯 Role Readiness",        card["role_readiness_score"], card["rr_color"]),
            ("🗣️ Interview Confidence",  card["interview_confidence"], card["ic_color"]),
            ("💻 Technical Depth",       card["technical_score"],      "#7dd3fc"),
            ("📐 Answer Structure",      card["structure_score"],      "#c084fc"),
        ],
    ):
        col.markdown(
            f'<div class="stat-card">'
            f'<div class="stat-value" style="color:{color};">{val}%</div>'
            f'<div class="stat-label">{label}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Radar chart + question breakdown ─────────────────────────────────────
    col_chart, col_breakdown = st.columns([1, 1])

    with col_chart:
        st.markdown("#### 📊 Competency Radar")
        r_labels = card["radar_labels"] + [card["radar_labels"][0]]
        r_values = card["radar_values"] + [card["radar_values"][0]]

        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=r_values, theta=r_labels, fill="toself",
            name="Your Score",
            line_color="#e94560",
            fillcolor="rgba(233,69,96,0.15)",
        ))
        fig.add_trace(go.Scatterpolar(
            r=[75] * len(r_labels), theta=r_labels,
            name="Target (75%)",
            line=dict(color="#22c55e", dash="dot", width=1.5),
            fillcolor="rgba(34,197,94,0.04)",
        ))
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True, range=[0, 100],
                    tickfont=dict(size=9, color="#6b7280"),
                    gridcolor="#1f2937",
                ),
                angularaxis=dict(tickfont=dict(size=10, color="#9ca3af")),
                bgcolor="#0f172a",
            ),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            showlegend=True,
            legend=dict(font=dict(color="#9ca3af", size=10), bgcolor="rgba(0,0,0,0)"),
            margin=dict(t=20, b=20, l=20, r=20),
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_breakdown:
        st.markdown("#### 📋 Question Breakdown")
        for row in card["breakdown"]:
            s     = row["score"]
            color = "#22c55e" if s >= 75 else "#fbbf24" if s >= 50 else "#ef4444"
            st.markdown(
                f"""
                <div class="feedback-card">
                    <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:10px;">
                        <div style="flex:1;">
                            <span style="color:#6b7280;font-size:0.72rem;">
                                Q{row["index"]} · {row["topic"]}
                            </span>
                            <div style="font-size:0.85rem;color:#d1d5db;margin-top:3px;">
                                {row["question"]}
                            </div>
                        </div>
                        <div style="color:{color};font-weight:800;font-size:1.05rem;
                                    white-space:nowrap;">{s}%</div>
                    </div>
                    <div style="background:#1f2937;border-radius:4px;height:4px;
                                overflow:hidden;margin-top:10px;">
                        <div style="width:{s}%;height:100%;background:{color};
                                    border-radius:4px;"></div>
                    </div>
                    <div style="color:#4b5563;font-size:0.7rem;margin-top:5px;">
                        ⏱ {row["time_sec"]}s
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.divider()

    # ── Per-question detailed feedback ────────────────────────────────────────
    st.markdown("#### 💬 Detailed Answer Feedback")
    per_q = feedbk.get("per_question", {})

    for idx, fb in per_q.items():
        q_obj  = data["questions"][idx]
        ans    = data["answers"].get(idx, "[No answer given]")
        header = f"{fb['emoji']} Q{idx+1} · {q_obj['topic']} — {fb['rating']}"

        with st.expander(header):
            st.markdown(f"**❓ Question:** {q_obj['question']}")
            ans_display = ans if ans != "[SKIPPED]" else "*(Skipped)*"
            st.markdown(f"**✍️ Your Answer:** {ans_display}")
            st.divider()
            st.markdown(f"**📝 Feedback:** {fb['summary']}")

            if fb.get("tips"):
                st.markdown("**💡 Improvement Tips:**")
                for tip in fb["tips"]:
                    if tip.strip():
                        st.markdown(f"- {tip}")

            if fb.get("follow_up"):
                st.markdown(
                    f'<div class="follow-card">'
                    f'🔍 Possible follow-up: <i>{fb["follow_up"]}</i>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

    st.divider()

    # ── Improvement roadmap + recommended resources ───────────────────────────
    col_road, col_rec = st.columns(2)

    with col_road:
        st.markdown("#### 🗺️ Improvement Roadmap")
        for item in card.get("roadmap", []):
            st.markdown(f'<div class="roadmap-item">{item}</div>', unsafe_allow_html=True)

        if card.get("unused_skills"):
            unused_chips = _skill_chips(card["unused_skills"][:6], "missing")
            st.markdown(
                f'<div class="roadmap-item" style="border-color:#fbbf24;">'
                f'🔦 <b>Underused skills from your resume — reference these in answers:</b>'
                f'<div style="margin-top:8px;">{unused_chips}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

        if card.get("weak_topics"):
            weak_str = " · ".join(card["weak_topics"][:4])
            st.markdown(
                f'<div class="roadmap-item" style="border-color:#f59e0b;">'
                f'📚 <b>Priority study areas:</b> {weak_str}'
                f'</div>',
                unsafe_allow_html=True,
            )

    with col_rec:
        st.markdown("#### 📚 Recommended Resources")
        if card.get("recommended"):
            for rec in card["recommended"]:
                st.markdown(f"**{rec['topic']}**")
                for r in rec["resources"]:
                    st.markdown(f"  - {r}")
                st.markdown("")
        else:
            st.success("🎉 Excellent! No major weak areas detected for your role.")

    st.divider()

    # ── Session statistics ────────────────────────────────────────────────────
    st.markdown("#### ⏱️ Session Statistics")
    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Questions",       card["total_questions"])
    s2.metric("Answered",        card["answered"])
    s3.metric("Avg. Time / Q",   f"{card['avg_time_sec']}s")
    s4.metric("Total Duration",  f"{card['duration_min']} min")

    st.divider()

    # ── Missing skills detection ──────────────────────────────────────────────
    if card.get("weak_topics") or card.get("unused_skills"):
        st.markdown("#### 🔍 Missing Skills Detection")
        col_w, col_u = st.columns(2)
        with col_w:
            st.markdown("**Weak topic areas:**")
            if card.get("weak_topics"):
                for t in card["weak_topics"]:
                    st.markdown(
                        f'<span class="skill-chip-missing">{t}</span>',
                        unsafe_allow_html=True,
                    )
            else:
                st.success("No weak topics detected!")
        with col_u:
            st.markdown("**Skills not demonstrated in answers:**")
            if card.get("unused_skills"):
                chips = _skill_chips(card["unused_skills"], "missing")
                st.markdown(chips, unsafe_allow_html=True)
            else:
                st.success("All your skills were referenced!")
        st.divider()

    # ── Action buttons ────────────────────────────────────────────────────────
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("🔁 Retake Interview", use_container_width=True, type="primary"):
            ie.reset_session()
            st.rerun()
    with c2:
        if st.button("📚 View Recommendations", use_container_width=True):
            st.switch_page("pages/recommendations.py")
    with c3:
        if st.button("🏠 Back to Dashboard", use_container_width=True):
            st.switch_page("pages/student_dashboard.py")