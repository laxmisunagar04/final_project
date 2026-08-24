"""
components/sidebar.py — Shared navigation sidebar for AI Career Twin
"""

import streamlit as st
from auth import get_user, get_role, logout, is_logged_in


def render_sidebar():
    with st.sidebar:
        st.markdown(
            """
            <div style="
                background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
                padding: 20px 16px 16px;
                border-radius: 12px;
                margin-bottom: 20px;
                text-align: center;
            ">
                <div style="font-size: 2rem;">🚀</div>
                <div style="color: #e94560; font-weight: 800; font-size: 1.1rem; letter-spacing: 1px;">
                    AI Career Twin
                </div>
                <div style="color: #a0a0b0; font-size: 0.75rem; margin-top: 4px;">
                    Powered by ML · Built for You
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if is_logged_in():
            user = get_user()
            role = get_role()
            label = user.get("name", user.get("email", "User"))

            st.markdown(
                f"""
                <div style="
                    background: #1e1e2e;
                    border-left: 3px solid #e94560;
                    padding: 10px 14px;
                    border-radius: 8px;
                    margin-bottom: 16px;
                ">
                    <div style="color: #cdd6f4; font-size: 0.78rem; text-transform: uppercase; letter-spacing: 1px;">
                        Logged in as
                    </div>
                    <div style="color: #e94560; font-weight: 700; font-size: 0.95rem;">
                        {label}
                    </div>
                    <div style="color: #6c7086; font-size: 0.72rem; margin-top: 2px;">
                        {'🎓 Student' if role == 'student' else '🏢 Company'}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.markdown("**Navigation**")

            if role == "student":
                st.page_link("pages/4_Student_dashboard.py", label="📊 My Dashboard", icon="🏠")
                st.page_link("pages/6_Resume_Analysis.py", label="📄 Resume Analysis", icon="📑")
                st.page_link("pages/7_Placement_Predictor.py", label="🎯 Placement Predictor", icon="🎯")
                st.page_link("pages/8_Recommendations.py", label="📚 Recommendations", icon="📚")

            elif role == "company":
                st.page_link("pages/5_Company_dashboard.py", label="🏢 Company Dashboard", icon="🏠")
                st.page_link("pages/9_Talent_Pool.py", label="🔍 Talent Pool", icon="🔍")

            st.divider()

            if st.button("🚪 Logout", use_container_width=True, type="secondary"):
                logout()
                st.rerun()

        else:
            st.markdown("**Get Started**")

            if st.button("🏠 Home", use_container_width=True):
                st.switch_page("app.py")

            if st.button("🎓 Student Login", use_container_width=True):
                st.switch_page("pages/1_Student_login.py")

            if st.button("🏢 Company Login", use_container_width=True):
                st.switch_page("pages/2_Company_login.py")

            if st.button("✍️ Sign Up", use_container_width=True):
                st.switch_page("pages/3_Signup.py")

        st.markdown(
            """
            <div style="
                position: fixed;
                bottom: 20px;
                left: 0;
                width: 240px;
                text-align: center;
                color: #45475a;
                font-size: 0.68rem;
            ">
                AI Career Twin © 2025
            </div>
            """,
            unsafe_allow_html=True,
        )