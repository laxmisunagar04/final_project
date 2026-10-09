"""
components/sidebar.py — Shared navigation sidebar for AI Career Twin
"""

import streamlit as st
from auth import get_user, get_role, logout, is_logged_in
from components.theme import inject_theme_css, render_theme_toggle


def render_sidebar():
    # Inject theme variables and styles on every page call
    inject_theme_css()

    with st.sidebar:
        st.markdown(
            """
            <div style="
                background: var(--ct-sidebar-header-bg);
                border: 1px solid var(--ct-sidebar-header-border);
                padding: 20px 16px 16px;
                border-radius: 12px;
                margin-bottom: 16px;
                text-align: center;
                box-shadow: var(--ct-card-shadow);
            ">
                <div style="font-size: 2rem;">🚀</div>
                <div style="color: #e94560; font-weight: 800; font-size: 1.1rem; letter-spacing: 1px;">
                    AI Career Twin
                </div>
                <div style="color: var(--ct-text-muted); font-size: 0.75rem; margin-top: 4px;">
                    Powered by ML · Built for You
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Persistent Theme Switcher
        render_theme_toggle()

        if is_logged_in():
            user = get_user()
            role = get_role()
            label = user.get("name", user.get("email", "User"))

            st.markdown(
                f"""
                <div style="
                    background: var(--ct-user-box-bg);
                    border: 1px solid var(--ct-user-box-border);
                    border-left: 3px solid #e94560;
                    padding: 10px 14px;
                    border-radius: 8px;
                    margin-bottom: 16px;
                    box-shadow: var(--ct-card-shadow);
                ">
                    <div style="color: var(--ct-text-muted); font-size: 0.75rem; text-transform: uppercase; letter-spacing: 1px;">
                        Logged in as
                    </div>
                    <div style="color: #e94560; font-weight: 700; font-size: 0.95rem;">
                        {label}
                    </div>
                    <div style="color: var(--ct-text-sub); font-size: 0.72rem; margin-top: 2px;">
                        {'🎓 Student' if role == 'student' else '🏢 Company'}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.markdown("**Navigation**")

            if role == "student":
                st.page_link("pages/4_Student_Dashboard.py", label="📊 My Dashboard", icon="🏠")
                st.page_link("pages/6_Resume_Analysis.py", label="📄 Resume Analysis", icon="📑")
                st.page_link("pages/7_Placement_Predictor.py", label="🎯 Placement Predictor", icon="🎯")
                st.page_link("pages/8_Recommendations.py", label="📚 Recommendations", icon="📚")
                st.page_link("pages/10_Mock_Interview.py", label="🎤 Mock Interview", icon="🎤")
                st.page_link("pages/11_Career_Chatbot.py", label="💬 AI Career Advisor", icon="💬")

            elif role == "company":
                st.page_link("pages/5_Company_Dashboard.py", label="🏢 Company Dashboard", icon="🏠")
                st.page_link("pages/9_Talent_Pool.py", label="🔍 Talent Pool", icon="🔍")
                st.page_link("pages/11_Career_Chatbot.py", label="💬 AI Career Advisor", icon="💬")

            st.divider()

            if st.button("🚪 Logout", use_container_width=True, type="secondary"):
                logout()
                st.rerun()

        else:
            st.markdown("**Get Started**")

            st.page_link("app.py", label="🏠 Home")
            st.page_link("pages/1_Student_Login.py", label="🎓 Student Login")
            st.page_link("pages/2_Company_Login.py", label="🏢 Company Login")
            st.page_link("pages/3_Signup.py", label="✍️ Sign Up")
            st.page_link("pages/11_Career_Chatbot.py", label="💬 AI Career Advisor")

        st.markdown(
            """
            <div style="
                margin-top: 24px;
                text-align: center;
                color: var(--ct-text-sub);
                font-size: 0.7rem;
            ">
                AI Career Twin © 2025
            </div>
            """,
            unsafe_allow_html=True,
        )