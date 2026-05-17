"""
auth.py — Session state helpers for AI Career Twin
"""

import streamlit as st


def is_logged_in() -> bool:
    return st.session_state.get("user") is not None


def get_user():
    return st.session_state.get("user")


def get_role() -> str:
    """Returns 'student' | 'company' | None"""
    return st.session_state.get("role")


def login(user: dict, role: str):
    st.session_state["user"] = user
    st.session_state["role"] = role


def logout():
    st.session_state.clear()


def require_login(allowed_role: str = None):
    """
    Call at the top of any protected page.
    Redirects to login if not authenticated (or wrong role).
    Returns True if access is granted.
    """
    if not is_logged_in():
        st.warning("🔒 Please log in to access this page.")
        st.stop()

    if allowed_role and get_role() != allowed_role:
        st.error(f"⛔ This page is for {allowed_role}s only.")
        st.stop()

    return True
