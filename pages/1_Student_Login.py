"""
pages/student_login.py — Student authentication page
"""

import streamlit as st
from database import init_db, login_student
from auth import login, is_logged_in
from components.sidebar import render_sidebar

st.set_page_config(page_title="Student Login · AI Career Twin", page_icon="🎓", layout="wide")
init_db()
render_sidebar()

if is_logged_in():
    st.switch_page("pages/4_Student_Dashboard.py")

st.markdown("## 🎓 Student Login")
st.markdown("Access your personalized career dashboard.")
st.divider()

with st.form("student_login_form"):
    email    = st.text_input("📧 Email")
    password = st.text_input("🔒 Password", type="password")
    submitted = st.form_submit_button("Login →", use_container_width=True, type="primary")

if submitted:
    if not email or not password:
        st.error("Please fill in both fields.")
    else:
        user = login_student(email.strip().lower(), password)
        if user:
            login(user, "student")
            st.success(f"Welcome back, {user['name']}! 🎉")
            st.switch_page("pages/4_Student_dashboard.py")
        else:
            st.error("❌ Invalid email or password.")

st.markdown("---")
col1, col2 = st.columns(2)
with col1:
    st.markdown("Don't have an account?")
    if st.button("✍️ Sign Up", use_container_width=True):
        st.switch_page("pages/3_Signup.py")
with col2:
    st.markdown("Are you a company?")
    if st.button("🏢 Company Login", use_container_width=True):
        st.switch_page("pages/2_Company_Login.py")
