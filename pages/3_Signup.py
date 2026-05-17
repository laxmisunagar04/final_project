"""
pages/signup.py — Unified signup page for students and companies
"""

import streamlit as st
from database import init_db, register_student, register_company
from components.sidebar import render_sidebar

st.set_page_config(page_title="Sign Up · AI Career Twin", page_icon="✍️", layout="wide")
init_db()
render_sidebar()

st.markdown("## ✍️ Create Account")
st.markdown("Join AI Career Twin as a student or a company.")
st.divider()

account_type = st.radio(
    "I am a …",
    ["🎓 Student", "🏢 Company"],
    horizontal=True,
)

st.markdown("<br>", unsafe_allow_html=True)

# ─── Student signup ───────────────────────────────────────────────────────────
if account_type == "🎓 Student":
    with st.form("student_signup"):
        col1, col2 = st.columns(2)
        with col1:
            name    = st.text_input("Full Name *")
            email   = st.text_input("Email *")
            password = st.text_input("Password *", type="password")
        with col2:
            confirm = st.text_input("Confirm Password *", type="password")
            college = st.text_input("College / University")
            branch  = st.text_input("Branch / Major")

        submitted = st.form_submit_button("Create Student Account →", use_container_width=True, type="primary")

    if submitted:
        if not all([name, email, password, confirm]):
            st.error("Please fill in all required fields.")
        elif password != confirm:
            st.error("❌ Passwords do not match.")
        elif len(password) < 6:
            st.error("Password must be at least 6 characters.")
        else:
            ok, msg = register_student(name, email.strip().lower(), password, college, branch)
            if ok:
                st.success(f"🎉 {msg} Please log in.")
                st.balloons()
                if st.button("Go to Student Login →"):
                    st.switch_page("pages/1_Student_Login.py")
            else:
                st.error(f"❌ {msg}")

# ─── Company signup ───────────────────────────────────────────────────────────
else:
    with st.form("company_signup"):
        col1, col2 = st.columns(2)
        with col1:
            name     = st.text_input("Company Name *")
            email    = st.text_input("Company Email *")
            password = st.text_input("Password *", type="password")
        with col2:
            confirm  = st.text_input("Confirm Password *", type="password")
            industry = st.text_input("Industry")
            website  = st.text_input("Website")

        submitted = st.form_submit_button("Register Company →", use_container_width=True, type="primary")

    if submitted:
        if not all([name, email, password, confirm]):
            st.error("Please fill in all required fields.")
        elif password != confirm:
            st.error("❌ Passwords do not match.")
        elif len(password) < 6:
            st.error("Password must be at least 6 characters.")
        else:
            ok, msg = register_company(name, email.strip().lower(), password, industry, website)
            if ok:
                st.success(f"🎉 {msg} Please log in.")
                st.balloons()
                if st.button("Go to Company Login →"):
                    st.switch_page("pages/3_Company_Login.py")
            else:
                st.error(f"❌ {msg}")
