"""
app.py — Landing page for AI Career Twin (multi-page Streamlit app)
"""

import streamlit as st
from database import init_db
from components.sidebar import render_sidebar
from auth import is_logged_in, get_role

# ─── Bootstrap ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Career Twin",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_db()  # Ensure tables exist on every cold start

render_sidebar()

# ─── Redirect logged-in users ─────────────────────────────────────────────────
if is_logged_in():
    role = get_role()
    if role == "student":
        st.switch_page("pages/4_Student_Dashboard.py")
    elif role == "company":
        st.switch_page("pages/5_Company_Dashboard.py")

# ─── Landing page ─────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;800&display=swap');
        .hero-title {
            font-family: 'Space Grotesk', sans-serif;
            font-size: 3.2rem;
            font-weight: 800;
            background: linear-gradient(135deg, #e94560, #f5a623);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            line-height: 1.15;
        }
        .hero-sub {
            font-size: 1.15rem;
            color: var(--ct-text-muted);
            margin-top: 12px;
            max-width: 560px;
        }
        .feature-card {
            background: var(--ct-bg-card);
            border: 1px solid var(--ct-border);
            border-radius: 16px;
            padding: 28px;
            height: 100%;
            transition: border-color 0.2s, box-shadow 0.2s;
            box-shadow: var(--ct-card-shadow);
        }
        .feature-card:hover {
            border-color: #e94560;
        }
        .feature-icon { font-size: 2.5rem; margin-bottom: 12px; }
        .feature-title { font-size: 1.1rem; font-weight: 700; margin-bottom: 8px; color: var(--ct-text-title); }
        .feature-desc  { color: var(--ct-text-muted); font-size: 0.88rem; line-height: 1.6; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="hero-title">Your AI-Powered<br>Career Co-Pilot</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="hero-sub">Upload your resume, discover skill gaps, predict placement '
    'probability, and connect with top companies — all in one intelligent platform.</div>',
    unsafe_allow_html=True,
)

st.markdown("<br>", unsafe_allow_html=True)

c1, c2, c3 = st.columns(3)
with c1:
    if st.button("🎓  Student Login", use_container_width=True, type="primary"):
        st.switch_page("pages/1_Student_Login.py")
with c2:
    if st.button("🏢  Company Login", use_container_width=True):
        st.switch_page("pages/2_Company_Login.py")
with c3:
    if st.button("✍️  Create Account", use_container_width=True):
        st.switch_page("pages/3_Signup.py")

st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("### What AI Career Twin Does For You")
st.markdown("<br>", unsafe_allow_html=True)

features = [
    ("📄", "Resume Parsing",        "Extracts skills and context from your PDF resume using NLP."),
    ("🎯", "Role Prediction",       "ML model predicts the best-fit job role based on your profile."),
    ("📊", "Skill Gap Analysis",    "Radar chart visualization showing matched vs missing skills."),
    ("📚", "Smart Recommendations", "Course and certification recommendations to close skill gaps."),
    ("🔮", "Placement Predictor",   "Predict your placement probability using CGPA, projects & more."),
    ("💬", "AI Career Advisor",     "Interactive AI mentor for interview prep, resume reviews & career roadmaps."),
]

cols = st.columns(3)
for i, (icon, title, desc) in enumerate(features):
    with cols[i % 3]:
        st.markdown(
            f"""
            <div class="feature-card">
                <div class="feature-icon">{icon}</div>
                <div class="feature-title">{title}</div>
                <div class="feature-desc">{desc}</div>
            </div><br>
            """,
            unsafe_allow_html=True,
        )