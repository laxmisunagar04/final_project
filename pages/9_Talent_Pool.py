"""
pages/talent_pool.py — Company talent search & filter page
"""

import streamlit as st
from auth import require_login
from database import init_db, get_all_student_profiles
from components.sidebar import render_sidebar

st.set_page_config(page_title="Talent Pool · AI Career Twin", page_icon="🔍", layout="wide")
init_db()
render_sidebar()
require_login("company")

st.markdown("## 🔍 Talent Pool")
st.markdown("Search, filter, and shortlist student candidates for your openings.")
st.divider()

profiles = get_all_student_profiles()

if not profiles:
    st.info("No student profiles are available yet.")
    st.stop()

# ── Filters ───────────────────────────────────────────────────────────────────
with st.expander("🔧 Filters", expanded=True):
    col1, col2, col3 = st.columns(3)

    with col1:
        all_roles = sorted({p.get("predicted_role", "") for p in profiles if p.get("predicted_role")})
        role_filter = st.multiselect("🎯 Role", all_roles, placeholder="All roles")

    with col2:
        min_prob = st.slider("📈 Min. Placement Probability", 0, 100, 0)

    with col3:
        min_cgpa = st.slider("📚 Min. CGPA", 0.0, 10.0, 0.0, step=0.1)

    skill_search = st.text_input("🛠️ Required Skill (keyword)", placeholder="e.g. python, sql, react")

# ── Apply filters ─────────────────────────────────────────────────────────────
filtered = []
for p in profiles:
    prob = p.get("placement_prob") or 0
    cgpa = p.get("cgpa") or 0

    if role_filter and p.get("predicted_role") not in role_filter:
        continue
    if prob < min_prob / 100:
        continue
    if cgpa < min_cgpa:
        continue
    if skill_search:
        skills_str = (p.get("skills") or "").lower()
        if skill_search.strip().lower() not in skills_str:
            continue
    filtered.append(p)

st.markdown(f"**{len(filtered)}** candidate(s) match your filters.")
st.markdown("<br>", unsafe_allow_html=True)

# ── Results table ─────────────────────────────────────────────────────────────
if filtered:
    for p in filtered:
        prob  = p.get("placement_prob")
        pct   = f"{round(prob * 100, 1)}%" if prob else "—"
        color = "#86efac" if prob and prob > 0.75 else ("#fde68a" if prob and prob > 0.5 else "#fca5a5")
        skills_preview = ", ".join((p.get("skills") or "").split(",")[:6])

        with st.container():
            st.markdown(
                f"""
                <div style="
                    background:#1a1a2e;
                    border:1px solid #2a2a4a;
                    border-radius:12px;
                    padding:18px 22px;
                    margin-bottom:12px;
                ">
                    <div style="display:flex;justify-content:space-between;align-items:flex-start;">
                        <div>
                            <div style="font-weight:700;font-size:1.05rem;">{p['name']}</div>
                            <div style="color:#888;font-size:0.82rem;margin-top:2px;">
                                📧 {p['email']}
                                {'&nbsp;·&nbsp;🏫 ' + p['college'] if p.get('college') else ''}
                                {'&nbsp;·&nbsp;' + p.get('branch', '') if p.get('branch') else ''}
                            </div>
                            <div style="margin-top:8px;">
                                <span style="background:#1e3a5f;color:#7dd3fc;
                                    padding:3px 10px;border-radius:20px;font-size:0.78rem;">
                                    🎯 {p.get('predicted_role', 'Unknown')}
                                </span>
                                &nbsp;
                                <span style="background:#1e2a1e;color:#86efac;
                                    padding:3px 10px;border-radius:20px;font-size:0.78rem;">
                                    📚 CGPA: {p.get('cgpa', '—')}
                                </span>
                            </div>
                            <div style="color:#6c7086;font-size:0.78rem;margin-top:8px;">
                                🛠️ {skills_preview or 'No skills listed'}
                            </div>
                        </div>
                        <div style="text-align:right;">
                            <div style="color:{color};font-weight:800;font-size:1.4rem;">{pct}</div>
                            <div style="color:#888;font-size:0.72rem;">Placement Prob.</div>
                            <div style="color:#888;font-size:0.72rem;margin-top:4px;">
                                💻 {p.get('coding_score', '—')} coding
                                &nbsp;·&nbsp;
                                🔧 {p.get('projects', '—')} projects
                            </div>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
else:
    st.warning("No candidates match the selected filters. Try broadening your search.")

st.divider()
if st.button("🏠 Back to Company Dashboard", use_container_width=True):
    st.switch_page("pages/5_Company_Dashboard.py")
