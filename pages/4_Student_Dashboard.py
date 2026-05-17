"""
pages/student_dashboard.py — Student home dashboard
"""

import streamlit as st
from auth import require_login, get_user
from database import init_db, get_student_profile
from components.sidebar import render_sidebar

st.set_page_config(page_title="Student Dashboard · AI Career Twin", page_icon="📊", layout="wide")
init_db()
render_sidebar()
require_login("student")

user    = get_user()
profile = get_student_profile(user["id"])

# ─── Header ───────────────────────────────────────────────────────────────────
st.markdown(f"## 👋 Welcome back, {user['name']}!")
if user.get("college"):
    st.caption(f"🏫 {user['college']}  ·  {user.get('branch', '')}")
st.divider()

# ─── Quick stats ──────────────────────────────────────────────────────────────
if profile:
    skills    = profile["skills"].split(",") if profile["skills"] else []
    role      = profile.get("predicted_role", "—")
    prob      = profile.get("placement_prob")
    cgpa      = profile.get("cgpa", "—")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🎯 Predicted Role",     role)
    col2.metric("🛠️ Skills Detected",    len(skills))
    col3.metric("📈 Placement Prob.",    f"{round(prob*100, 1)}%" if prob else "—")
    col4.metric("📚 CGPA",               cgpa if cgpa else "—")

    st.markdown("<br>", unsafe_allow_html=True)

    # Placement readiness bar
    if prob is not None:
        st.markdown("#### 📈 Placement Readiness")
        st.progress(prob)
        if prob > 0.75:
            st.success(f"🔥 Excellent! You have a {round(prob*100,1)}% placement probability.")
        elif prob > 0.5:
            st.info(f"👍 Good! Placement probability: {round(prob*100,1)}%")
        else:
            st.warning(f"⚠️ Needs improvement. Placement probability: {round(prob*100,1)}%")

    st.markdown("<br>", unsafe_allow_html=True)

    # Skills chips
    st.markdown("#### 🛠️ Your Detected Skills")
    if skills:
        badge_html = " ".join(
            f'<span style="background:#1e3a5f;color:#7dd3fc;padding:4px 12px;'
            f'border-radius:20px;font-size:0.8rem;margin:3px;display:inline-block;">'
            f'{s.strip()}</span>'
            for s in skills if s.strip()
        )
        st.markdown(badge_html, unsafe_allow_html=True)
    else:
        st.info("No skills on record yet. Upload your resume to get started.")

else:
    # First-time user — nudge them to upload
    st.info("👆 You haven't uploaded your resume yet. Head to **Resume Analysis** to get started!")
    st.markdown("<br>", unsafe_allow_html=True)

# ─── Quick-action buttons ─────────────────────────────────────────────────────
st.markdown("#### ⚡ Quick Actions")
c1, c2, c3 = st.columns(3)
with c1:
    if st.button("📄 Analyse Resume", use_container_width=True, type="primary"):
        st.switch_page("pages/6_Resume_Analysis.py")
with c2:
    if st.button("🎯 Predict Placement", use_container_width=True):
        st.switch_page("pages/7_Placement_Predictor.py")
with c3:
    if st.button("📚 View Recommendations", use_container_width=True):
        st.switch_page("pages/8_Recommendations.py")
