"""
pages/11_Career_Chatbot.py — TwinAdvisor AI Career Twin Assistant
Provides real-time platform guidance, career navigation, resume reviews, skill roadmaps,
interview prep, and recruiter talent-pool assistance using Streamlit chat primitives
and Google Gemini API (gemini-3.6-flash).
"""

import streamlit as st
from database import init_db, get_student_profile
from auth import is_logged_in, get_user, get_role
from components.sidebar import render_sidebar
from components.theme import get_current_theme
from interview import (
    chat_career_advisor,
    is_api_key_configured,
    get_gemini_api_key,
)

# ─── Bootstrap & Navigation ──────────────────────────────────────────────────
st.set_page_config(
    page_title="TwinAdvisor · AI Career Twin Assistant",
    page_icon="💬",
    layout="wide",
)

init_db()
render_sidebar()

# ─── High-Contrast Production Styling for Chat UI ─────────────────────────────
theme = get_current_theme()
is_light = (theme == "light")

if is_light:
    chat_css = """
    <style>
    /* ─── Light Mode Surface & Fixed Container Integration ──────────────────── */
    header[data-testid="stHeader"],
    [data-testid="stHeader"],
    .stAppHeader,
    .stApp > header {
        background: #f8fafc !important;
        background-color: #f8fafc !important;
        background-image: none !important;
        color: #0f172a !important;
        border-bottom: 1px solid transparent !important;
        box-shadow: none !important;
    }
    header[data-testid="stHeader"]::before,
    header[data-testid="stHeader"]::after,
    [data-testid="stHeader"]::before,
    [data-testid="stHeader"]::after {
        display: none !important;
        background: transparent !important;
    }
    [data-testid="stDecoration"] {
        display: none !important;
        height: 0 !important;
        background: transparent !important;
        background-image: none !important;
    }
    [data-testid="stBottom"],
    [data-testid="stBottom"] > div,
    [data-testid="stBottomBlockContainer"],
    [data-testid="stBottomBlockContainer"] > div,
    [data-testid="stChatFloatingInputContainer"],
    .stChatFloatingInputContainer,
    .stBottom,
    .stBottom > div,
    div:has(> div[data-testid="stChatInput"]),
    div:has(> [data-testid="stChatInput"]),
    footer,
    [data-testid="stFooter"] {
        background: #f8fafc !important;
        background-color: #f8fafc !important;
        background-image: none !important;
        border-top: none !important;
        box-shadow: none !important;
    }
    [data-testid="stBottom"]::before,
    [data-testid="stBottom"]::after,
    [data-testid="stBottomBlockContainer"]::before,
    [data-testid="stBottomBlockContainer"]::after {
        display: none !important;
        background: transparent !important;
        background-image: none !important;
    }

    /* ─── Light Mode Chat Input Styling ─────────────────────────────────────── */
    div[data-testid="stChatInput"] {
        background: transparent !important;
        background-color: transparent !important;
        padding-bottom: 1.25rem !important;
    }
    div[data-testid="stChatInput"] > div {
        background-color: #ffffff !important;
        border: 1.5px solid #cbd5e1 !important;
        border-radius: 12px !important;
        box-shadow: 0 2px 10px rgba(15, 23, 42, 0.06) !important;
        transition: all 0.2s ease !important;
    }
    div[data-testid="stChatInput"] > div:focus-within {
        border-color: #e94560 !important;
        box-shadow: 0 0 0 2px rgba(233, 69, 96, 0.22) !important;
    }
    div[data-testid="stChatInput"] textarea,
    div[data-testid="stChatInput"] textarea[data-testid="stChatInputTextArea"] {
        color: #0f172a !important;
        -webkit-text-fill-color: #0f172a !important;
        background-color: transparent !important;
        font-size: 0.95rem !important;
        font-weight: 500 !important;
        line-height: 1.5 !important;
        caret-color: #e94560 !important;
    }
    div[data-testid="stChatInput"] textarea::placeholder,
    div[data-testid="stChatInput"] textarea::-webkit-input-placeholder {
        color: #475569 !important;
        -webkit-text-fill-color: #475569 !important;
        opacity: 1 !important;
        font-weight: 400 !important;
    }
    div[data-testid="stChatInput"] button {
        color: #e94560 !important;
        background-color: transparent !important;
        border: none !important;
        border-radius: 8px !important;
        transition: all 0.15s ease !important;
    }
    div[data-testid="stChatInput"] button:hover {
        background-color: rgba(233, 69, 96, 0.1) !important;
        transform: scale(1.05);
    }
    div[data-testid="stChatInput"] button svg {
        fill: #e94560 !important;
        stroke: #e94560 !important;
    }

    /* ─── Light Mode Chat Message Cards ─────────────────────────────────────── */
    div[data-testid="stChatMessage"] {
        background-color: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 12px !important;
        padding: 1rem 1.25rem !important;
        margin-bottom: 0.85rem !important;
        box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04) !important;
    }
    div[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]),
    div[data-testid="stChatMessage"]:has([aria-label="chat message from user"]) {
        background-color: #f8fafc !important;
        border: 1px solid #cbd5e1 !important;
        border-left: 4px solid #e94560 !important;
    }
    div[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]),
    div[data-testid="stChatMessage"]:has([aria-label="chat message from assistant"]) {
        background-color: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        border-left: 4px solid #3b82f6 !important;
    }

    /* ─── Light Mode Chat Typography Contrast ───────────────────────────────── */
    div[data-testid="stChatMessageContent"] {
        color: #1e293b !important;
    }
    div[data-testid="stChatMessageContent"] [data-testid="stMarkdownContainer"] p,
    div[data-testid="stChatMessageContent"] [data-testid="stMarkdownContainer"] li,
    div[data-testid="stChatMessageContent"] [data-testid="stMarkdownContainer"] span {
        color: #1e293b !important;
        -webkit-text-fill-color: #1e293b !important;
        font-size: 0.95rem !important;
        line-height: 1.6 !important;
    }
    div[data-testid="stChatMessageContent"] [data-testid="stMarkdownContainer"] h1,
    div[data-testid="stChatMessageContent"] [data-testid="stMarkdownContainer"] h2,
    div[data-testid="stChatMessageContent"] [data-testid="stMarkdownContainer"] h3,
    div[data-testid="stChatMessageContent"] [data-testid="stMarkdownContainer"] h4 {
        color: #0f172a !important;
        -webkit-text-fill-color: #0f172a !important;
        font-weight: 700 !important;
        margin-top: 0.75rem !important;
        margin-bottom: 0.5rem !important;
    }
    div[data-testid="stChatMessageContent"] [data-testid="stMarkdownContainer"] strong,
    div[data-testid="stChatMessageContent"] [data-testid="stMarkdownContainer"] b {
        color: #0f172a !important;
        -webkit-text-fill-color: #0f172a !important;
        font-weight: 700 !important;
    }
    div[data-testid="stChatMessageContent"] code {
        background-color: #f1f5f9 !important;
        color: #0f172a !important;
        -webkit-text-fill-color: #0f172a !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 6px !important;
        padding: 0.15rem 0.4rem !important;
        font-size: 0.88rem !important;
    }
    div[data-testid="stChatMessageContent"] pre {
        background-color: #f8fafc !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 8px !important;
    }
    div[data-testid="stChatMessageAvatar"] {
        background-color: #f1f5f9 !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 50% !important;
    }

    /* ─── Light Mode Buttons & Chip Controls ────────────────────────────────── */
    div.quick-chips-wrapper div[data-testid="stButton"] button {
        background-color: #ffffff !important;
        color: #0f172a !important;
        -webkit-text-fill-color: #0f172a !important;
        border: 1.5px solid #cbd5e1 !important;
        border-radius: 10px !important;
        font-size: 0.82rem !important;
        font-weight: 500 !important;
        padding: 0.45rem 0.65rem !important;
        transition: all 0.15s ease !important;
    }
    div.quick-chips-wrapper div[data-testid="stButton"] button:hover {
        background-color: #f1f5f9 !important;
        border-color: #e94560 !important;
        color: #e94560 !important;
        -webkit-text-fill-color: #e94560 !important;
        transform: translateY(-1px);
    }
    button[kind="secondary"] {
        background-color: #ffffff !important;
        color: #0f172a !important;
        -webkit-text-fill-color: #0f172a !important;
        border: 1.5px solid #cbd5e1 !important;
    }
    </style>
    """
else:
    chat_css = """
    <style>
    /* ─── Dark Mode Surface & Fixed Container Integration ───────────────────── */
    header[data-testid="stHeader"],
    [data-testid="stHeader"],
    .stAppHeader,
    .stApp > header {
        background: #0e1117 !important;
        background-color: #0e1117 !important;
        background-image: none !important;
        color: #f8fafc !important;
        border-bottom: 1px solid transparent !important;
        box-shadow: none !important;
    }
    header[data-testid="stHeader"]::before,
    header[data-testid="stHeader"]::after,
    [data-testid="stHeader"]::before,
    [data-testid="stHeader"]::after {
        display: none !important;
        background: transparent !important;
    }
    [data-testid="stDecoration"] {
        display: none !important;
        height: 0 !important;
        background: transparent !important;
        background-image: none !important;
    }
    header[data-testid="stHeader"] button,
    [data-testid="stHeader"] button,
    header[data-testid="stHeader"] svg,
    [data-testid="stHeader"] svg {
        color: #f8fafc !important;
        fill: #f8fafc !important;
    }
    [data-testid="stBottom"],
    [data-testid="stBottom"] > div,
    [data-testid="stBottomBlockContainer"],
    [data-testid="stBottomBlockContainer"] > div,
    [data-testid="stChatFloatingInputContainer"],
    .stChatFloatingInputContainer,
    .stBottom,
    .stBottom > div,
    div:has(> div[data-testid="stChatInput"]),
    div:has(> [data-testid="stChatInput"]),
    footer,
    [data-testid="stFooter"] {
        background: #0e1117 !important;
        background-color: #0e1117 !important;
        background-image: none !important;
        border-top: none !important;
        box-shadow: none !important;
    }
    [data-testid="stBottom"]::before,
    [data-testid="stBottom"]::after,
    [data-testid="stBottomBlockContainer"]::before,
    [data-testid="stBottomBlockContainer"]::after {
        display: none !important;
        background: transparent !important;
        background-image: none !important;
    }

    /* ─── Dark Mode Chat Input Styling ──────────────────────────────────────── */
    div[data-testid="stChatInput"] {
        background: transparent !important;
        background-color: transparent !important;
        padding-bottom: 1.25rem !important;
    }
    div[data-testid="stChatInput"] > div {
        background-color: #1a1a2e !important;
        border: 1.5px solid #2a2a4a !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4) !important;
        transition: all 0.2s ease !important;
    }
    div[data-testid="stChatInput"] > div:focus-within {
        border-color: #e94560 !important;
        box-shadow: 0 0 0 2px rgba(233, 69, 96, 0.3) !important;
    }
    div[data-testid="stChatInput"] textarea,
    div[data-testid="stChatInput"] textarea[data-testid="stChatInputTextArea"] {
        color: #f8fafc !important;
        -webkit-text-fill-color: #f8fafc !important;
        background-color: transparent !important;
        font-size: 0.95rem !important;
        font-weight: 500 !important;
        line-height: 1.5 !important;
        caret-color: #e94560 !important;
    }
    div[data-testid="stChatInput"] textarea::placeholder,
    div[data-testid="stChatInput"] textarea::-webkit-input-placeholder {
        color: #94a3b8 !important;
        -webkit-text-fill-color: #94a3b8 !important;
        opacity: 1 !important;
        font-weight: 400 !important;
    }
    div[data-testid="stChatInput"] button {
        color: #e94560 !important;
        background-color: transparent !important;
        border: none !important;
        border-radius: 8px !important;
        transition: all 0.15s ease !important;
    }
    div[data-testid="stChatInput"] button:hover {
        background-color: rgba(233, 69, 96, 0.18) !important;
        transform: scale(1.05);
    }
    div[data-testid="stChatInput"] button svg {
        fill: #e94560 !important;
        stroke: #e94560 !important;
    }

    /* ─── Dark Mode Chat Message Cards ──────────────────────────────────────── */
    div[data-testid="stChatMessage"] {
        background-color: #1a1a2e !important;
        border: 1px solid #2a2a4a !important;
        border-radius: 12px !important;
        padding: 1rem 1.25rem !important;
        margin-bottom: 0.85rem !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.25) !important;
    }
    div[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]),
    div[data-testid="stChatMessage"]:has([aria-label="chat message from user"]) {
        background-color: #1e1e38 !important;
        border: 1px solid #2d2d52 !important;
        border-left: 4px solid #e94560 !important;
    }
    div[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]),
    div[data-testid="stChatMessage"]:has([aria-label="chat message from assistant"]) {
        background-color: #151928 !important;
        border: 1px solid #252e42 !important;
        border-left: 4px solid #3b82f6 !important;
    }

    /* ─── Dark Mode Chat Typography Contrast ────────────────────────────────── */
    div[data-testid="stChatMessageContent"] {
        color: #e2e8f0 !important;
    }
    div[data-testid="stChatMessageContent"] [data-testid="stMarkdownContainer"] p,
    div[data-testid="stChatMessageContent"] [data-testid="stMarkdownContainer"] li,
    div[data-testid="stChatMessageContent"] [data-testid="stMarkdownContainer"] span {
        color: #e2e8f0 !important;
        -webkit-text-fill-color: #e2e8f0 !important;
        font-size: 0.95rem !important;
        line-height: 1.6 !important;
    }
    div[data-testid="stChatMessageContent"] [data-testid="stMarkdownContainer"] h1,
    div[data-testid="stChatMessageContent"] [data-testid="stMarkdownContainer"] h2,
    div[data-testid="stChatMessageContent"] [data-testid="stMarkdownContainer"] h3,
    div[data-testid="stChatMessageContent"] [data-testid="stMarkdownContainer"] h4 {
        color: #f8fafc !important;
        -webkit-text-fill-color: #f8fafc !important;
        font-weight: 700 !important;
        margin-top: 0.75rem !important;
        margin-bottom: 0.5rem !important;
    }
    div[data-testid="stChatMessageContent"] [data-testid="stMarkdownContainer"] strong,
    div[data-testid="stChatMessageContent"] [data-testid="stMarkdownContainer"] b {
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        font-weight: 700 !important;
    }
    div[data-testid="stChatMessageContent"] code {
        background-color: #111827 !important;
        color: #f8fafc !important;
        -webkit-text-fill-color: #f8fafc !important;
        border: 1px solid #1f2937 !important;
        border-radius: 6px !important;
        padding: 0.15rem 0.4rem !important;
        font-size: 0.88rem !important;
    }
    div[data-testid="stChatMessageContent"] pre {
        background-color: #0f172a !important;
        border: 1px solid #1f2937 !important;
        border-radius: 8px !important;
    }
    div[data-testid="stChatMessageAvatar"] {
        background-color: #252542 !important;
        border: 1px solid #35355e !important;
        border-radius: 50% !important;
    }

    /* ─── Dark Mode Buttons & Chip Controls ─────────────────────────────────── */
    div.quick-chips-wrapper div[data-testid="stButton"] button {
        background-color: #1a1a2e !important;
        color: #f8fafc !important;
        -webkit-text-fill-color: #f8fafc !important;
        border: 1.5px solid #2a2a4a !important;
        border-radius: 10px !important;
        font-size: 0.82rem !important;
        font-weight: 500 !important;
        padding: 0.45rem 0.65rem !important;
        transition: all 0.15s ease !important;
    }
    div.quick-chips-wrapper div[data-testid="stButton"] button:hover {
        background-color: #252542 !important;
        border-color: #e94560 !important;
        color: #ff5c7c !important;
        -webkit-text-fill-color: #ff5c7c !important;
        transform: translateY(-1px);
    }
    button[kind="secondary"] {
        background-color: #1a1a2e !important;
        color: #f8fafc !important;
        -webkit-text-fill-color: #f8fafc !important;
        border: 1.5px solid #2a2a4a !important;
    }
    </style>
    """

st.markdown(chat_css, unsafe_allow_html=True)

# ─── Session State Keys ───────────────────────────────────────────────────────
CHAT_KEY = "career_chat_messages"

# ─── Existing User Role & Profile Context Resolution ──────────────────────────
user_context = {}
role_type = "guest"
display_user_name = ""

if is_logged_in():
    user = get_user() or {}
    role_type = get_role() or "guest"
    if role_type == "student":
        student_id = user.get("id")
        student_name = user.get("name", "Student")
        display_user_name = student_name
        profile = get_student_profile(student_id) if student_id else None

        target_role = (profile.get("predicted_role") if profile else None) or "Software Engineer"
        raw_skills = (profile.get("skills") if profile else None) or ""
        skills_list = [s.strip() for s in raw_skills.split(",") if s.strip()]

        user_context = {
            "role": "student",
            "name": student_name,
            "target_role": target_role,
            "skills": skills_list,
            "college": user.get("college", ""),
            "branch": user.get("branch", ""),
            "placement_prob": profile.get("placement_prob") if profile else None,
            "cgpa": profile.get("cgpa") if profile else None,
            "projects": profile.get("projects") if profile else None,
            "internships": profile.get("internships") if profile else None,
            "communication": profile.get("communication") if profile else None,
        }
    elif role_type == "company":
        company_name = user.get("name", "Recruiter")
        display_user_name = company_name
        user_context = {
            "role": "company",
            "company_name": company_name,
            "name": company_name,
            "industry": user.get("industry", ""),
            "website": user.get("website", ""),
        }
    else:
        user_context = {"role": "guest"}
else:
    user_context = {"role": "guest"}


# ─── Welcome Message Builder ──────────────────────────────────────────────────
def build_welcome_message(role: str, name: str, ctx: dict) -> str:
    """Build the clean whole-project welcome message for TwinAdvisor."""
    user_greeting = f" **{name}**" if name else ""
    context_note = ""

    if role == "student":
        target = ctx.get("target_role", "Software Engineer")
        skills = ctx.get("skills", [])
        skills_str = f" with skills in **{', '.join(skills[:4])}**" if skills else ""
        context_note = f"\n\n*Student Profile Active: Tailored for your **{target}** track{skills_str}.*"
    elif role == "company":
        comp_name = ctx.get("company_name", "Recruiter")
        context_note = f"\n\n*Recruiter Context Active: Tailored for **{comp_name}** talent search and candidate evaluations.*"

    return (
        f"### 👋 TwinAdvisor — Your AI Career Twin Assistant\n\n"
        f"Hello{user_greeting}! I am **TwinAdvisor**, your dedicated intelligent assistant across the entire **AI Career Twin** platform.{context_note}\n\n"
        "I can help you with:\n"
        "- 🚀 **Platform Guidance**: Navigating tools like Resume Analysis, Placement Predictor, Recommendations, AI Mock Interviews, and Talent Pool.\n"
        "- 🎯 **Career Guidance**: Strategic tech roadmaps, role specialization, and milestone planning.\n"
        "- 📄 **Resume Optimization**: Crafting quantifiable Google X-Y-Z bullet points and maximizing ATS alignment.\n"
        "- 💡 **Skills & Recommendations**: Prioritizing frameworks, projects, and learning pathways.\n"
        "- 🎤 **Interviews & Placement**: High-yield technical topics, behavioral STAR strategies, and placement odds improvement.\n"
        "- 🏢 **Company & Talent Pool**: Search filters, role benchmarking, and candidate evaluation metrics.\n\n"
        "How can I help you today?"
    )


new_welcome = build_welcome_message(role_type, display_user_name, user_context)

# Initialize conversation history or refresh old student-only welcome
if CHAT_KEY not in st.session_state or not st.session_state[CHAT_KEY]:
    st.session_state[CHAT_KEY] = [{"role": "assistant", "content": new_welcome}]
elif (
    len(st.session_state[CHAT_KEY]) == 1
    and "TwinAdvisor — Your AI Career Twin Assistant" not in st.session_state[CHAT_KEY][0].get("content", "")
):
    st.session_state[CHAT_KEY][0]["content"] = new_welcome

# ─── Clean Professional Header ───────────────────────────────────────────────
col_head, col_btn = st.columns([4, 1.2])
with col_head:
    st.markdown(
        """
        <div style="display:flex; align-items:center; gap:10px; margin-bottom:4px;">
            <h2 style="margin:0; font-size:1.6rem; font-weight:700; color:var(--ct-text-title);">
                💬 TwinAdvisor
            </h2>
            <span style="background:rgba(233,69,96,0.15); color:#e94560; font-size:0.75rem; font-weight:600; padding:3px 8px; border-radius:12px; border:1px solid rgba(233,69,96,0.3);">
                Whole-Platform AI Assistant
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if is_api_key_configured():
        st.caption("🟢 **Connected:** Google Gemini 3.6 Flash · Personalized live reasoning active.")
    else:
        st.caption("💡 **Advisory Mode:** Built-in guidance active. Set `GEMINI_API_KEY` in secrets or sidebar for live Gemini.")

with col_btn:
    if st.button("🗑️ Clear Chat", use_container_width=True, help="Reset conversation history"):
        st.session_state[CHAT_KEY] = [{"role": "assistant", "content": new_welcome}]
        st.rerun()

# ─── Optional Sidebar Key Settings ───────────────────────────────────────────
with st.sidebar.expander("🔑 Google Gemini API Key Settings", expanded=False):
    st.markdown(
        "<div style='font-size:0.75rem; color:var(--ct-text-muted); margin-bottom:8px;'>"
        "Securely enter a session-only key if not using <code>.streamlit/secrets.toml</code>."
        "</div>",
        unsafe_allow_html=True,
    )
    temp_key = st.text_input(
        "Gemini API Key",
        value=st.session_state.get("custom_gemini_api_key", ""),
        type="password",
        placeholder="AIzaSy...",
        key="_temp_gemini_api_key_input",
    )
    if temp_key != st.session_state.get("custom_gemini_api_key", ""):
        st.session_state["custom_gemini_api_key"] = temp_key.strip().strip('"\'')
        st.rerun()

    if is_api_key_configured():
        st.success("✅ Key detected and active.")
    else:
        st.caption("No key set in secrets or environment.")

st.markdown("<div style='margin-bottom: 0.75rem;'></div>", unsafe_allow_html=True)

# ─── Dynamic Suggested Questions ──────────────────────────────────────────────
st.markdown(
    "<div style='font-size:0.78rem; font-weight:600; letter-spacing:0.03em; color:var(--ct-text-muted); margin-bottom:6px;'>"
    "💡 SUGGESTED QUESTIONS"
    "</div>",
    unsafe_allow_html=True,
)

if role_type == "student":
    target_role = user_context.get("target_role", "Software Engineer")
    quick_prompts = [
        f"📝 How can I optimize my resume for {target_role}?",
        "🎯 What skills should I prioritize to improve placement odds?",
        "🎤 Give me 3 high-yield mock interview questions.",
        "🚀 How do I navigate the AI Career Twin features?",
    ]
elif role_type == "company":
    quick_prompts = [
        "🏢 How can I filter candidates in the Talent Pool?",
        "📊 What metrics determine candidate placement readiness?",
        "🎯 How do I design a role-specific interview rubric?",
        "🚀 How do I navigate the AI Career Twin features?",
    ]
else:
    quick_prompts = [
        "🚀 What features does AI Career Twin offer?",
        "📝 How do I craft high-impact resume bullet points?",
        "🔮 How does the Placement Predictor work?",
        "🏢 How does the Company Talent Pool work?",
    ]

st.markdown('<div class="quick-chips-wrapper">', unsafe_allow_html=True)
qp_cols = st.columns(4)
clicked_prompt = None
for idx, qp in enumerate(quick_prompts):
    with qp_cols[idx]:
        if st.button(qp, key=f"qp_{idx}", use_container_width=True):
            clicked_prompt = qp
st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div style='margin-bottom: 0.85rem;'></div>", unsafe_allow_html=True)

# ─── Display Existing Chat History ────────────────────────────────────────────
for msg in st.session_state[CHAT_KEY]:
    role = msg.get("role", "user")
    with st.chat_message(role, avatar="🧑‍🎓" if role == "user" else "🤖"):
        st.markdown(msg.get("content", ""))

# ─── Process User Input ───────────────────────────────────────────────────────
user_query = st.chat_input("Ask for platform guidance, career tips, resume polish, or interview prep...")

prompt_to_submit = clicked_prompt if clicked_prompt else user_query

if prompt_to_submit:
    # 1. Append and render user message
    st.session_state[CHAT_KEY].append({"role": "user", "content": prompt_to_submit})
    with st.chat_message("user", avatar="🧑‍🎓"):
        st.markdown(prompt_to_submit)

    # 2. Generate assistant response
    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("TwinAdvisor is thinking..."):
            ok, reply = chat_career_advisor(
                messages=st.session_state[CHAT_KEY],
                student_context=user_context,
            )
            st.markdown(reply)

    # 3. Save assistant message to history
    st.session_state[CHAT_KEY].append({"role": "assistant", "content": reply})
    st.rerun()
