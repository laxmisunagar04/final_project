"""
pages/recommendations.py — Course & skill recommendations
Preserves original ML logic from app.py exactly.
"""

import streamlit as st
from auth import require_login, get_user
from database import init_db, get_student_profile
from components.sidebar import render_sidebar

# ── Your original ML modules (untouched) ────────────────────────────────────
from skill_gap import find_skill_gap
from recommender import recommend

st.set_page_config(page_title="Recommendations · AI Career Twin", page_icon="📚", layout="wide")
init_db()
render_sidebar()
require_login("student")

user    = get_user()
profile = get_student_profile(user["id"])

st.markdown("## 📚 Personalised Recommendations")
st.markdown("Courses and resources tailored to close your specific skill gaps.")
st.divider()

if not profile:
    st.warning("👆 Please upload your resume first to get personalised recommendations.")
    if st.button("📄 Go to Resume Analysis"):
        st.switch_page("pages/6_Resume_Analysis.py")
    st.stop()

skills = profile["skills"].split(",") if profile["skills"] else []
role   = profile.get("predicted_role", "")

if not role:
    st.warning("⚠️ No predicted role found. Please complete your resume analysis first.")
    if st.button("📄 Go to Resume Analysis"):
        st.switch_page("pages/6_Resume_Analysis.py")
    st.stop()

# ── Compute gaps & recommendations ──────────────────────────────────────────
gap, matched, required = find_skill_gap(skills, role)
recs = recommend(gap)

# ── Display ──────────────────────────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.markdown("#### ✅ Skills You Already Have")
    if matched:
        for s in matched:
            st.markdown(
                f'<span style="background:#1a3a1a;color:#86efac;padding:4px 12px;'
                f'border-radius:20px;font-size:0.82rem;margin:2px;display:inline-block;">✓ {s}</span>',
                unsafe_allow_html=True,
            )
    else:
        st.info("No matched skills found for this role.")

with col2:
    st.markdown("#### ❌ Skills to Develop")
    if gap:
        for s in gap:
            st.markdown(
                f'<span style="background:#3a1a1a;color:#fca5a5;padding:4px 12px;'
                f'border-radius:20px;font-size:0.82rem;margin:2px;display:inline-block;">✗ {s}</span>',
                unsafe_allow_html=True,
            )
    else:
        st.success("🎉 You have all required skills for this role!")

st.markdown("<br>", unsafe_allow_html=True)

if recs:
    st.markdown("#### 👉 Recommended Courses & Resources")
    for i, r in enumerate(recs, 1):
        st.markdown(
            f"""
            <div style="
                background:#1a1a2e;
                border-left:4px solid #e94560;
                padding:14px 18px;
                border-radius:8px;
                margin-bottom:10px;
            ">
                <span style="color:#e94560;font-weight:700;">#{i}</span>
                &nbsp;{r}
            </div>
            """,
            unsafe_allow_html=True,
        )
else:
    st.success("🎉 No recommendations needed — your skills are a great match for your predicted role!")

st.markdown("<br>", unsafe_allow_html=True)
if st.button("🏠 Back to Dashboard", use_container_width=True):
    st.switch_page("pages/4_Student_Dashboard.py")
