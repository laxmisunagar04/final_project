"""
pages/placement_predictor.py — Placement probability prediction
Preserves original ML logic from app.py exactly.
"""

import streamlit as st
from auth import require_login, get_user
from database import init_db, get_student_profile, save_student_profile
from components.sidebar import render_sidebar

# ── Your original ML module (untouched) ─────────────────────────────────────
from model import predict_placement

st.set_page_config(page_title="Placement Predictor · AI Career Twin", page_icon="🎯", layout="wide")
init_db()
render_sidebar()
require_login("student")

user    = get_user()
profile = get_student_profile(user["id"])

st.markdown("## 🎯 Placement Predictor")
st.markdown("Adjust the sliders to match your profile and predict your placement probability.")
st.divider()

# Pre-fill from saved profile if available
default_cgpa    = float(profile["cgpa"])          if profile and profile["cgpa"]          else 7.0
default_coding  = int(profile["coding_score"])    if profile and profile["coding_score"]  else 50
default_proj    = int(profile["projects"])        if profile and profile["projects"]      else 1
default_intern  = int(profile["internships"])     if profile and profile["internships"]   else 0
default_comm    = int(profile["communication"])   if profile and profile["communication"] else 5

col1, col2 = st.columns([2, 1])

with col1:
    cgpa          = st.slider("📚 CGPA",                  0.0, 10.0, default_cgpa,   step=0.1)
    coding        = st.slider("💻 Coding Score",           0,   100,  default_coding)
    projects      = st.slider("🔧 Projects Completed",    0,   5,    default_proj)
    internships   = st.slider("🏢 Internships",           0,   3,    default_intern)
    communication = st.slider("🗣️ Communication Skill",  1,   10,   default_comm)

with col2:
    st.markdown("#### 📋 Your Inputs")
    st.markdown(f"**CGPA:** {cgpa}")
    st.markdown(f"**Coding Score:** {coding}")
    st.markdown(f"**Projects:** {projects}")
    st.markdown(f"**Internships:** {internships}")
    st.markdown(f"**Communication:** {communication}/10")

st.markdown("<br>", unsafe_allow_html=True)

if st.button("🚀 Predict Placement Probability", use_container_width=True, type="primary"):
    with st.spinner("Running prediction model …"):
        prob = predict_placement(cgpa, coding, projects, internships, communication)

    st.divider()
    st.subheader("📈 Placement Readiness")
    st.progress(prob)

    if prob > 0.75:
        st.success(f"🔥 Excellent! Placement Probability: {round(prob * 100, 2)}%")
    elif prob > 0.5:
        st.info(f"👍 Good! Placement Probability: {round(prob * 100, 2)}%")
    else:
        st.warning(f"⚠️ Needs Improvement! Placement Probability: {round(prob * 100, 2)}%")

    # Persist updated values to DB
    if profile:
        save_student_profile(
            student_id=user["id"],
            skills=profile["skills"].split(",") if profile["skills"] else [],
            predicted_role=profile.get("predicted_role", ""),
            placement_prob=prob,
            cgpa=cgpa,
            coding_score=coding,
            projects=projects,
            internships=internships,
            communication=communication,
        )
    else:
        save_student_profile(
            student_id=user["id"],
            skills=[],
            predicted_role="",
            placement_prob=prob,
            cgpa=cgpa,
            coding_score=coding,
            projects=projects,
            internships=internships,
            communication=communication,
        )

    st.success("✅ Results saved to your profile!")

    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("📚 See Recommendations", use_container_width=True):
            st.switch_page("pages/8_Recommendations.py")
    with c2:
        if st.button("🏠 Back to Dashboard", use_container_width=True):
            st.switch_page("pages/4_Student_Dashboard.py")
