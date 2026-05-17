"""
pages/company_login.py — Company authentication page
"""

import streamlit as st
from database import init_db, login_company
from auth import login, is_logged_in
from components.sidebar import render_sidebar

st.set_page_config(page_title="Company Login · AI Career Twin", page_icon="🏢", layout="wide")
init_db()
render_sidebar()

if is_logged_in():
    st.switch_page("pages/5_Company_Dashboard.py")

st.markdown("## 🏢 Company Login")
st.markdown("Access your talent portal and browse student profiles.")
st.divider()

with st.form("company_login_form"):
    email    = st.text_input("📧 Company Email")
    password = st.text_input("🔒 Password", type="password")
    submitted = st.form_submit_button("Login →", use_container_width=True, type="primary")

if submitted:
    if not email or not password:
        st.error("Please fill in both fields.")
    else:
        user = login_company(email.strip().lower(), password)
        if user:
            login(user, "company")
            st.success(f"Welcome, {user['name']}! 🎉")
            st.switch_page("pages/5_Company_dashboard.py")
        else:
            st.error("❌ Invalid email or password.")

st.markdown("---")
col1, col2 = st.columns(2)
with col1:
    st.markdown("New to the platform?")
    if st.button("✍️ Register Company", use_container_width=True):
        st.switch_page("pages/3_Signup.py")
with col2:
    st.markdown("Are you a student?")
    if st.button("🎓 Student Login", use_container_width=True):
        st.switch_page("pages/1_Student_login.py")
