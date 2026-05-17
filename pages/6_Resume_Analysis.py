"""
pages/resume_analysis.py — Resume upload + skill gap + radar chart
Preserves original ML logic from app.py exactly.
"""

import streamlit as st
import plotly.graph_objects as go

from auth import require_login, get_user
from database import init_db, save_student_profile, get_student_profile
from components.sidebar import render_sidebar

# ── Your original ML modules (untouched) ────────────────────────────────────
from resume_parser import extract_resume_data
from model import predict_role
from skill_gap import find_skill_gap

st.set_page_config(page_title="Resume Analysis · AI Career Twin", page_icon="📄", layout="wide")
init_db()
render_sidebar()
require_login("student")

user = get_user()

st.markdown("## 📄 Resume Analysis")
st.markdown("Upload your PDF resume and let our ML pipeline do the heavy lifting.")
st.divider()

uploaded_file = st.file_uploader("📎 Upload Resume (PDF)", type="pdf")

if uploaded_file:
    with st.spinner("🔍 Parsing resume …"):
        skills, text = extract_resume_data(uploaded_file)

    if not skills:
        st.warning("⚠️ No skills detected. Using demo skills for demonstration.")
        skills = ["python", "sql"]

    # ── Role prediction ──────────────────────────────────────────────────────
    role = predict_role(text)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🎯 Predicted Role")
        st.success(role)
    with col2:
        st.subheader("📄 Extracted Skills")
        badge_html = " ".join(
            f'<span style="background:#1e3a5f;color:#7dd3fc;padding:4px 10px;'
            f'border-radius:20px;font-size:0.8rem;margin:2px;display:inline-block;">'
            f'{s}</span>'
            for s in skills
        )
        st.markdown(badge_html, unsafe_allow_html=True)

    # ── Skill gap ────────────────────────────────────────────────────────────
    gap, matched, required = find_skill_gap(skills, role)

    st.divider()
    st.subheader("📊 Skill Analysis")

    col3, col4 = st.columns(2)
    with col3:
        st.write("✅ Matched Skills")
        st.success(", ".join(matched) if matched else "None matched")
    with col4:
        st.write("❌ Missing Skills")
        st.error(", ".join(gap) if gap else "No gaps found! 🎉")

    # ── Radar chart ──────────────────────────────────────────────────────────
    st.divider()
    st.subheader("📊 Skill Radar Chart")

    labels = required
    values = [1 if skill in skills else 0 for skill in labels]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=labels,
        fill="toself",
        name="Your Skills",
        line_color="#e94560",
        fillcolor="rgba(233,69,96,0.2)",
    ))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 1]),
            bgcolor="#1a1a2e",
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        margin=dict(t=20, b=20),
    )
    st.plotly_chart(fig, use_container_width=True)

    # ── Persist to DB (skills + role; placement filled later) ────────────────
    existing = get_student_profile(user["id"])
    prob       = existing["placement_prob"]        if existing else None
    cgpa       = existing["cgpa"]                  if existing else 0.0
    coding     = existing["coding_score"]          if existing else 0
    projects   = existing["projects"]              if existing else 0
    internships= existing["internships"]           if existing else 0
    comm       = existing["communication"]         if existing else 5

    save_student_profile(
        student_id=user["id"],
        skills=skills,
        predicted_role=role,
        placement_prob=prob,
        cgpa=cgpa,
        coding_score=coding,
        projects=projects,
        internships=internships,
        communication=comm,
    )

    st.success("✅ Resume analysis saved to your profile!")

    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        if st.button("📚 View Recommendations", use_container_width=True, type="primary"):
            st.switch_page("pages/8_Recommendations.py")
    with c2:
        if st.button("🎯 Predict Placement", use_container_width=True):
            st.switch_page("pages/7_Placement_Predictor.py")
