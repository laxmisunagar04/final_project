"""
components/theme.py — Theme manager and dynamic style injector for AI Career Twin
Supports seamless Light / Dark mode switching with persistent session state and high contrast.
"""

import streamlit as st

_THEME_KEY = "app_theme"


def get_current_theme() -> str:
    """Return the active theme: 'dark' or 'light'. Defaults to 'dark'."""
    if _THEME_KEY not in st.session_state:
        st.session_state[_THEME_KEY] = "dark"
    return st.session_state[_THEME_KEY]


def set_theme(theme_name: str) -> None:
    """Set the active theme."""
    if theme_name in ("dark", "light"):
        st.session_state[_THEME_KEY] = theme_name


def get_chart_theme_colors(theme: str = None) -> dict:
    """Return Plotly radar and chart layout color tokens matching the current theme."""
    if theme is None:
        theme = get_current_theme()

    if theme == "light":
        return {
            "polar_bg": "#ffffff",
            "grid_color": "#e2e8f0",
            "tick_color": "#334155",
            "legend_color": "#1e293b",
            "line_target": "#16a34a",
            "fill_target": "rgba(22, 163, 74, 0.08)",
        }
    return {
        "polar_bg": "#0f172a",
        "grid_color": "#1f2937",
        "tick_color": "#6b7280",
        "legend_color": "#9ca3af",
        "line_target": "#22c55e",
        "fill_target": "rgba(34, 197, 94, 0.04)",
    }


def inject_theme_css() -> None:
    """Inject theme-aware CSS custom properties and element overrides into the page."""
    theme = get_current_theme()
    is_light = (theme == "light")

    css = f"""
    <style>
        :root {{
            --ct-theme: "{theme}";
            --ct-bg-app: {"#f8fafc" if is_light else "#0e1117"};
            --ct-bg-sidebar: {"#f1f5f9" if is_light else "#161b22"};
            --ct-bg-card: {"#ffffff" if is_light else "#1a1a2e"};
            --ct-bg-card-sub: {"#ffffff" if is_light else "#111827"};
            --ct-bg-card-alt: {"#f8fafc" if is_light else "#0f172a"};
            --ct-input-bg: {"#ffffff" if is_light else "#1a1a2e"};
            --ct-border: {"#e2e8f0" if is_light else "#2a2a4a"};
            --ct-border-sub: {"#cbd5e1" if is_light else "#1f2937"};
            --ct-text-title: {"#0f172a" if is_light else "#f8fafc"};
            --ct-text-main: {"#1e293b" if is_light else "#e2e8f0"};
            --ct-text-muted: {"#475569" if is_light else "#94a3b8"};
            --ct-text-sub: {"#64748b" if is_light else "#6b7280"};
            --ct-primary: #e94560;
            --ct-primary-hover: {"#d12e4b" if is_light else "#ff5c7c"};
            --ct-primary-glow: {"rgba(233, 69, 96, 0.15)" if is_light else "rgba(233, 69, 96, 0.25)"};

            /* Navigation link tokens */
            --ct-nav-link-bg: {"#ffffff" if is_light else "#1a1a2e"};
            --ct-nav-link-text: {"#0f172a" if is_light else "#f8fafc"};
            --ct-nav-link-border: {"#cbd5e1" if is_light else "#2a2a4a"};
            --ct-nav-link-hover-bg: {"#f1f5f9" if is_light else "#252542"};
            --ct-nav-link-hover-text: #e94560;

            /* Secondary button tokens */
            --ct-btn-sec-bg: {"#ffffff" if is_light else "#1a1a2e"};
            --ct-btn-sec-text: {"#0f172a" if is_light else "#f8fafc"};
            --ct-btn-sec-border: {"#cbd5e1" if is_light else "#2a2a4a"};
            --ct-btn-sec-hover-bg: {"#f1f5f9" if is_light else "#252542"};
            --ct-btn-sec-hover-text: #e94560;

            /* Sidebar header & user box */
            --ct-sidebar-header-bg: {
                "linear-gradient(135deg, #ffffff 0%, #f1f5f9 100%)"
                if is_light else
                "linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%)"
            };
            --ct-sidebar-header-border: {"#e2e8f0" if is_light else "#2a2a4a"};
            --ct-user-box-bg: {"#ffffff" if is_light else "#1e1e2e"};
            --ct-user-box-border: {"#e2e8f0" if is_light else "#2a2a4a"};

            /* Badge tokens */
            --ct-badge-blue-bg: {"#e0f2fe" if is_light else "#1e3a5f"};
            --ct-badge-blue-text: {"#0369a1" if is_light else "#7dd3fc"};
            --ct-badge-blue-border: {"#bae6fd" if is_light else "#2563eb"};
            --ct-badge-green-bg: {"#dcfce7" if is_light else "#1a3a1a"};
            --ct-badge-green-text: {"#15803d" if is_light else "#86efac"};
            --ct-badge-green-border: {"#bbf7d0" if is_light else "#166534"};
            --ct-badge-red-bg: {"#fee2e2" if is_light else "#3a1a1a"};
            --ct-badge-red-text: {"#b91c1c" if is_light else "#fca5a5"};
            --ct-badge-red-border: {"#fecaca" if is_light else "#7f1d1d"};
            --ct-badge-purple-bg: {"#f3e8ff" if is_light else "#2a1a3e"};
            --ct-badge-purple-text: {"#7e22ce" if is_light else "#c084fc"};
            --ct-banner-bg: {
                "linear-gradient(135deg, #ffffff, #f1f5f9)"
                if is_light else
                "linear-gradient(135deg, #0f172a, #1e1b4b)"
            };
            --ct-question-card-bg: {
                "linear-gradient(135deg, #ffffff, #f8fafc)"
                if is_light else
                "linear-gradient(135deg, #0f172a, #1e1b4b)"
            };
            --ct-progress-track: {"#e2e8f0" if is_light else "#1f2937"};
            --ct-card-shadow: {
                "0 4px 6px -1px rgba(0, 0, 0, 0.06), 0 2px 4px -2px rgba(0, 0, 0, 0.04)"
                if is_light else
                "0 4px 6px -1px rgba(0, 0, 0, 0.3)"
            };
        }}

        /* ─── App Canvas & Main Body ───────────────────────────────────────── */
        html, body, #root,
        .stApp,
        [data-testid="stAppViewContainer"],
        [data-testid="stAppViewBlockContainer"],
        section[data-testid="stMain"],
        .main {{
            background: var(--ct-bg-app) !important;
            background-color: var(--ct-bg-app) !important;
            color: var(--ct-text-main) !important;
        }}

        /* ─── Header & Top Viewport ────────────────────────────────────────── */
        header[data-testid="stHeader"],
        [data-testid="stHeader"],
        .stAppHeader,
        .stApp > header {{
            background: var(--ct-bg-app) !important;
            background-color: var(--ct-bg-app) !important;
            background-image: none !important;
            color: var(--ct-text-title) !important;
            border-bottom: 1px solid transparent !important;
            box-shadow: none !important;
        }}

        header[data-testid="stHeader"]::before,
        header[data-testid="stHeader"]::after,
        [data-testid="stHeader"]::before,
        [data-testid="stHeader"]::after {{
            display: none !important;
            background: transparent !important;
        }}

        [data-testid="stDecoration"] {{
            display: none !important;
            height: 0 !important;
            background: transparent !important;
            background-image: none !important;
        }}

        header[data-testid="stHeader"] button,
        [data-testid="stHeader"] button,
        header[data-testid="stHeader"] svg,
        [data-testid="stHeader"] svg,
        [data-testid="stToolbarActions"] button,
        [data-testid="stToolbarActions"] svg {{
            color: var(--ct-text-title) !important;
            fill: var(--ct-text-title) !important;
        }}

        /* ─── Bottom Area & Fixed Chat Container ───────────────────────────── */
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
        [data-testid="stFooter"] {{
            background: var(--ct-bg-app) !important;
            background-color: var(--ct-bg-app) !important;
            background-image: none !important;
            border-top: none !important;
            box-shadow: none !important;
        }}

        [data-testid="stBottom"]::before,
        [data-testid="stBottom"]::after,
        [data-testid="stBottomBlockContainer"]::before,
        [data-testid="stBottomBlockContainer"]::after {{
            display: none !important;
            background: transparent !important;
            background-image: none !important;
        }}

        div[data-testid="stChatInput"] {{
            background: transparent !important;
            background-color: transparent !important;
        }}

        /* General main app text */
        .stApp p,
        .stApp [data-testid="stMarkdownContainer"] p,
        .stApp [data-testid="stMarkdownContainer"] li,
        .stApp label {{
            color: var(--ct-text-main) !important;
        }}

        .stApp strong,
        .stApp [data-testid="stMarkdownContainer"] strong,
        .stApp b {{
            color: var(--ct-text-title) !important;
        }}

        h1, h2, h3, h4, h5, h6,
        .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6,
        .stApp [data-testid="stMarkdownContainer"] h1,
        .stApp [data-testid="stMarkdownContainer"] h2,
        .stApp [data-testid="stMarkdownContainer"] h3,
        .stApp [data-testid="stMarkdownContainer"] h4 {{
            color: var(--ct-text-title) !important;
        }}

        .hero-sub {{
            color: var(--ct-text-muted) !important;
        }}
        .section-label {{
            color: var(--ct-text-sub) !important;
        }}
        .stCaption,
        [data-testid="stCaptionContainer"] p {{
            color: var(--ct-text-muted) !important;
        }}

        /* ─── Sidebar Container ────────────────────────────────────────────── */
        [data-testid="stSidebar"] {{
            background-color: var(--ct-bg-sidebar) !important;
            border-right: 1px solid var(--ct-border) !important;
        }}

        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] span,
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] strong,
        [data-testid="stSidebar"] b {{
            color: var(--ct-text-main) !important;
        }}

        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3,
        [data-testid="stSidebar"] h4,
        [data-testid="stSidebar"] h5,
        [data-testid="stSidebar"] h6 {{
            color: var(--ct-text-title) !important;
        }}

        /* ─── Sidebar Navigation Items: Built-in & Custom ─────────────────── */
        /* Streamlit automatic sidebar navigation (top of sidebar) */
        [data-testid="stSidebarNav"],
        [data-testid="stSidebarNav"] *,
        [data-testid="stSidebarNavItems"],
        [data-testid="stSidebarNavItems"] *,
        [data-testid="stSidebarNavLink"],
        [data-testid="stSidebarNavLink"] *,
        [data-testid="stSidebar"] nav a,
        [data-testid="stSidebar"] nav a *,
        [data-testid="stSidebar"] nav span,
        [data-testid="stSidebar"] nav p {{
            color: var(--ct-nav-link-text) !important;
            font-weight: 500 !important;
        }}

        [data-testid="stSidebarNavLink"]:hover,
        [data-testid="stSidebarNavLink"]:hover *,
        [data-testid="stSidebar"] nav a:hover,
        [data-testid="stSidebar"] nav a:hover * {{
            color: var(--ct-nav-link-hover-text) !important;
        }}

        /* Custom st.page_link buttons in sidebar */
        [data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"],
        [data-testid="stSidebar"] [data-testid="stPageLink-NavLink"],
        [data-testid="stPageLink"] a,
        [data-testid="stPageLink"] [data-testid="stPageLink-NavLink"] {{
            background-color: var(--ct-nav-link-bg) !important;
            border: 1px solid var(--ct-nav-link-border) !important;
            border-radius: 10px !important;
            padding: 8px 14px !important;
            margin-bottom: 6px !important;
            display: flex !important;
            align-items: center !important;
            text-decoration: none !important;
            transition: all 0.2s ease !important;
            box-shadow: var(--ct-card-shadow);
        }}

        [data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"] *,
        [data-testid="stSidebar"] [data-testid="stPageLink-NavLink"] *,
        [data-testid="stPageLink"] a *,
        [data-testid="stPageLink"] [data-testid="stPageLink-NavLink"] * {{
            color: var(--ct-nav-link-text) !important;
            font-weight: 600 !important;
            font-size: 0.9rem !important;
        }}

        [data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"]:hover,
        [data-testid="stSidebar"] [data-testid="stPageLink-NavLink"]:hover,
        [data-testid="stPageLink"] a:hover,
        [data-testid="stPageLink"] [data-testid="stPageLink-NavLink"]:hover {{
            background-color: var(--ct-nav-link-hover-bg) !important;
            border-color: var(--ct-primary) !important;
        }}

        [data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"]:hover *,
        [data-testid="stSidebar"] [data-testid="stPageLink-NavLink"]:hover *,
        [data-testid="stPageLink"] a:hover *,
        [data-testid="stPageLink"] [data-testid="stPageLink-NavLink"]:hover * {{
            color: var(--ct-nav-link-hover-text) !important;
        }}

        /* ─── Buttons: Primary & Secondary ─────────────────────────────────── */
        /* Secondary Buttons (Must be high contrast in both themes) */
        button[data-testid="stBaseButton-secondary"],
        button[data-testid="baseButton-secondary"],
        button[kind="secondary"],
        .stButton > button:not([kind="primary"]):not([data-testid="stBaseButton-primary"]):not([data-testid="baseButton-primary"]),
        .stButton button:not([kind="primary"]):not([data-testid="stBaseButton-primary"]):not([data-testid="baseButton-primary"]) {{
            background-color: var(--ct-btn-sec-bg) !important;
            color: var(--ct-btn-sec-text) !important;
            border: 1.5px solid var(--ct-btn-sec-border) !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
            box-shadow: var(--ct-card-shadow);
            transition: all 0.2s ease !important;
        }}

        button[data-testid="stBaseButton-secondary"]:hover,
        button[data-testid="baseButton-secondary"]:hover,
        button[kind="secondary"]:hover,
        .stButton > button:not([kind="primary"]):not([data-testid="stBaseButton-primary"]):hover,
        .stButton button:not([kind="primary"]):not([data-testid="stBaseButton-primary"]):hover {{
            background-color: var(--ct-btn-sec-hover-bg) !important;
            border-color: var(--ct-primary) !important;
            color: var(--ct-btn-sec-hover-text) !important;
        }}

        button[data-testid="stBaseButton-secondary"] *,
        button[data-testid="baseButton-secondary"] *,
        button[kind="secondary"] *,
        .stButton > button:not([kind="primary"]):not([data-testid="stBaseButton-primary"]) *,
        .stButton button:not([kind="primary"]):not([data-testid="stBaseButton-primary"]) * {{
            color: inherit !important;
        }}

        /* Primary Buttons */
        button[data-testid="stBaseButton-primary"],
        button[data-testid="baseButton-primary"],
        button[kind="primary"],
        div[data-testid="stFormSubmitButton"] > button,
        div[data-testid="stFormSubmitButton"] button {{
            background-color: var(--ct-primary) !important;
            color: #ffffff !important;
            border: 1.5px solid var(--ct-primary) !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
            box-shadow: var(--ct-card-shadow);
            transition: all 0.2s ease !important;
        }}

        button[data-testid="stBaseButton-primary"]:hover,
        button[data-testid="baseButton-primary"]:hover,
        button[kind="primary"]:hover,
        div[data-testid="stFormSubmitButton"] > button:hover,
        div[data-testid="stFormSubmitButton"] button:hover {{
            background-color: var(--ct-primary-hover) !important;
            border-color: var(--ct-primary-hover) !important;
            color: #ffffff !important;
        }}

        button[data-testid="stBaseButton-primary"] *,
        button[data-testid="baseButton-primary"] *,
        button[kind="primary"] *,
        div[data-testid="stFormSubmitButton"] > button *,
        div[data-testid="stFormSubmitButton"] button * {{
            color: #ffffff !important;
        }}

        /* ─── Form Controls & Input Fields ─────────────────────────────────── */
        /* Widget Labels */
        label[data-testid="stWidgetLabel"],
        [data-testid="stWidgetLabel"],
        [data-testid="stWidgetLabel"] *,
        .stTextInput label,
        .stTextInput label *,
        .stTextArea label,
        .stTextArea label *,
        .stSelectbox label,
        .stSelectbox label *,
        .stSlider label,
        .stSlider label * {{
            color: var(--ct-text-title) !important;
            font-weight: 600 !important;
        }}

        /* Text Input & Text Area Boxes */
        div[data-baseweb="input"],
        div[data-baseweb="base-input"],
        .stTextInput input,
        .stTextArea textarea,
        div[data-baseweb="textarea"] {{
            background-color: var(--ct-input-bg) !important;
            color: var(--ct-text-title) !important;
            border: 1px solid var(--ct-border-sub) !important;
            border-radius: 8px !important;
        }}

        div[data-baseweb="input"] input,
        div[data-baseweb="base-input"] input,
        .stTextInput input {{
            background-color: transparent !important;
            color: var(--ct-text-title) !important;
            caret-color: var(--ct-text-title) !important;
        }}

        div[data-baseweb="input"]:focus-within,
        div[data-baseweb="textarea"]:focus-within {{
            border-color: var(--ct-primary) !important;
            box-shadow: 0 0 0 2px var(--ct-primary-glow) !important;
        }}

        [data-testid="stSelectbox"] div[data-baseweb="select"] > div {{
            background-color: var(--ct-input-bg) !important;
            color: var(--ct-text-title) !important;
            border: 1px solid var(--ct-border-sub) !important;
            border-radius: 8px !important;
        }}

        [data-testid="stSelectbox"] div[data-baseweb="select"] * {{
            color: var(--ct-text-title) !important;
        }}

        /* Slider */
        [data-testid="stSlider"] div {{
            color: var(--ct-text-main) !important;
        }}

        hr {{
            border-color: var(--ct-border) !important;
        }}

        /* ─── Metric Cards ─────────────────────────────────────────────────── */
        [data-testid="stMetricValue"] * {{
            color: var(--ct-text-title) !important;
        }}
        [data-testid="stMetricLabel"] * {{
            color: var(--ct-text-muted) !important;
        }}

        /* ─── Cards & Feature Containers ───────────────────────────────────── */
        .feature-card {{
            background: var(--ct-bg-card) !important;
            border: 1px solid var(--ct-border) !important;
            border-radius: 16px;
            padding: 28px;
            height: 100%;
            transition: border-color 0.2s, box-shadow 0.2s;
            box-shadow: var(--ct-card-shadow);
        }}
        .feature-card:hover {{
            border-color: var(--ct-primary) !important;
        }}
        .feature-title {{
            color: var(--ct-text-title) !important;
            font-size: 1.1rem;
            font-weight: 700;
            margin-bottom: 8px;
        }}
        .feature-desc {{
            color: var(--ct-text-muted) !important;
            font-size: 0.88rem;
            line-height: 1.6;
        }}

        .stat-card {{
            background: var(--ct-bg-card-sub) !important;
            border: 1px solid var(--ct-border-sub) !important;
            border-radius: 14px;
            padding: 20px 16px;
            text-align: center;
            box-shadow: var(--ct-card-shadow);
        }}
        .stat-label {{
            color: var(--ct-text-sub) !important;
            font-size: 0.75rem;
            margin-top: 4px;
        }}

        .info-card {{
            background: var(--ct-bg-card-sub) !important;
            border: 1px solid var(--ct-border-sub) !important;
            border-radius: 14px;
            padding: 20px 22px;
            box-shadow: var(--ct-card-shadow);
        }}

        .theme-card {{
            background: var(--ct-bg-card) !important;
            border: 1px solid var(--ct-border) !important;
            border-radius: 12px;
            padding: 16px 20px;
            margin-bottom: 12px;
            box-shadow: var(--ct-card-shadow);
        }}

        .question-card {{
            background: var(--ct-question-card-bg) !important;
            border: 1px solid var(--ct-border) !important;
            border-left: 5px solid var(--ct-primary) !important;
            border-radius: 18px;
            padding: 30px 34px;
            margin: 18px 0 12px;
            box-shadow: var(--ct-card-shadow);
        }}
        .q-text {{
            color: var(--ct-text-title) !important;
        }}

        .follow-card {{
            background: var(--ct-bg-card-alt) !important;
            border: 1px dashed var(--ct-border-sub) !important;
            border-radius: 10px;
            padding: 12px 16px;
            margin-top: 14px;
            color: var(--ct-text-muted) !important;
            font-size: 0.83rem;
        }}

        .feedback-card {{
            background: var(--ct-bg-card-sub) !important;
            border: 1px solid var(--ct-border-sub) !important;
            border-radius: 12px;
            padding: 18px;
            margin-bottom: 12px;
            box-shadow: var(--ct-card-shadow);
        }}

        .roadmap-item {{
            background: var(--ct-bg-card-alt) !important;
            border-left: 3px solid var(--ct-primary) !important;
            padding: 12px 16px;
            border-radius: 8px;
            margin-bottom: 10px;
            font-size: 0.88rem;
            color: var(--ct-text-main) !important;
            box-shadow: var(--ct-card-shadow);
        }}

        .recom-card {{
            background: var(--ct-bg-card) !important;
            border: 1px solid var(--ct-border) !important;
            border-left: 4px solid var(--ct-primary) !important;
            padding: 14px 18px;
            border-radius: 8px;
            margin-bottom: 10px;
            color: var(--ct-text-main) !important;
            box-shadow: var(--ct-card-shadow);
        }}

        /* ─── Skill Chips ──────────────────────────────────────────────────── */
        .skill-chip {{
            background: var(--ct-badge-green-bg) !important;
            color: var(--ct-badge-green-text) !important;
            border: 1px solid var(--ct-badge-green-border) !important;
            padding: 4px 13px;
            border-radius: 20px;
            font-size: 0.78rem;
            margin: 3px;
            display: inline-block;
        }}
        .skill-chip-missing {{
            background: var(--ct-badge-red-bg) !important;
            color: var(--ct-badge-red-text) !important;
            border: 1px solid var(--ct-badge-red-border) !important;
            padding: 4px 13px;
            border-radius: 20px;
            font-size: 0.78rem;
            margin: 3px;
            display: inline-block;
        }}
        .skill-chip-blue {{
            background: var(--ct-badge-blue-bg) !important;
            color: var(--ct-badge-blue-text) !important;
            border: 1px solid var(--ct-badge-blue-border) !important;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8rem;
            margin: 3px;
            display: inline-block;
        }}

        /* Step Progress */
        .step-pill.pending {{
            background: var(--ct-border) !important;
            color: var(--ct-text-sub) !important;
        }}
        .step-sep {{
            color: var(--ct-border-sub) !important;
        }}

        /* Readiness Bar */
        .readiness-bar-wrap {{
            background: var(--ct-progress-track) !important;
            border-radius: 6px;
            height: 8px;
            overflow: hidden;
            margin-top: 6px;
        }}

        /* Role Badge */
        .role-badge {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            background: var(--ct-badge-blue-bg) !important;
            border: 1px solid var(--ct-badge-blue-border) !important;
            color: var(--ct-badge-blue-text) !important;
            padding: 10px 22px;
            border-radius: 30px;
            font-size: 1.05rem;
            font-weight: 700;
        }}
        .role-badge-sm {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: var(--ct-badge-blue-bg) !important;
            border: 1px solid var(--ct-badge-blue-border) !important;
            color: var(--ct-badge-blue-text) !important;
            padding: 5px 14px;
            border-radius: 20px;
            font-size: 0.82rem;
            font-weight: 600;
        }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


def render_theme_toggle() -> None:
    """Render a clean, persistent Light/Dark toggle in the sidebar."""
    theme = get_current_theme()

    st.sidebar.markdown(
        """
        <div style="
            font-size: 0.72rem;
            text-transform: uppercase;
            letter-spacing: 1.2px;
            font-weight: 700;
            color: var(--ct-text-muted);
            margin-bottom: 6px;
        ">
            Appearance
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button(
            "🌙 Dark",
            key="_theme_toggle_dark",
            use_container_width=True,
            type="primary" if theme == "dark" else "secondary",
        ):
            if theme != "dark":
                set_theme("dark")
                st.rerun()

    with col2:
        if st.button(
            "☀️ Light",
            key="_theme_toggle_light",
            use_container_width=True,
            type="primary" if theme == "light" else "secondary",
        ):
            if theme != "light":
                set_theme("light")
                st.rerun()

    st.sidebar.markdown("<div style='margin-bottom: 14px;'></div>", unsafe_allow_html=True)
