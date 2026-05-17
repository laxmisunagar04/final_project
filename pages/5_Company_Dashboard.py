"""
pages/company_dashboard.py — Company home dashboard
"""

import streamlit as st
from auth import require_login, get_user
from database import init_db, get_all_student_profiles
from components.sidebar import render_sidebar

st.set_page_config(page_title="Company Dashboard · AI Career Twin", page_icon="🏢", layout="wide")
init_db()
render_sidebar()
require_login("company")

user     = get_user()
profiles = get_all_student_profiles()

st.markdown(f"## 🏢 {user['name']} — Talent Dashboard")
if user.get("industry"):
    st.caption(f"🏭 {user['industry']}")
st.divider()

# ── Summary stats ─────────────────────────────────────────────────────────────
total    = len(profiles)
ready    = sum(1 for p in profiles if p.get("placement_prob") and p["placement_prob"] > 0.75)
avg_prob = (
    sum(p["placement_prob"] for p in profiles if p.get("placement_prob")) / total
    if total else 0
)

col1, col2, col3 = st.columns(3)
col1.metric("👥 Total Candidates",        total)
col2.metric("🔥 Placement-Ready (>75%)",  ready)
col3.metric("📈 Avg. Placement Prob.",    f"{round(avg_prob * 100, 1)}%")

st.markdown("<br>", unsafe_allow_html=True)

# ── Quick action ──────────────────────────────────────────────────────────────
if st.button("🔍 Browse Full Talent Pool", use_container_width=True, type="primary"):
    st.switch_page("pages/9_Talent_Pool.py")

st.divider()

# ── Top 5 candidates ─────────────────────────────────────────────────────────
st.markdown("#### 🏆 Top 5 Candidates by Placement Probability")

if profiles:
    top5 = profiles[:5]  # Already sorted DESC by DB query
    for i, p in enumerate(top5, 1):
        prob  = p.get("placement_prob")
        pct   = f"{round(prob * 100, 1)}%" if prob else "—"
        color = "#86efac" if prob and prob > 0.75 else ("#fde68a" if prob and prob > 0.5 else "#fca5a5")

        st.markdown(
            f"""
            <div style="
                background:#1a1a2e;
                border:1px solid #2a2a4a;
                border-radius:12px;
                padding:14px 20px;
                margin-bottom:10px;
                display:flex;
                align-items:center;
                justify-content:space-between;
            ">
                <div>
                    <span style="color:#e94560;font-weight:800;font-size:1rem;">#{i}</span>
                    &nbsp;&nbsp;
                    <span style="font-weight:600;">{p['name']}</span>
                    &nbsp;
                    <span style="color:#888;font-size:0.82rem;">
                        {p.get('college', '')} · {p.get('predicted_role', '')}
                    </span>
                </div>
                <div style="color:{color};font-weight:700;font-size:1rem;">{pct}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
else:
    st.info("No student profiles available yet. Check back once students complete their analysis.")
