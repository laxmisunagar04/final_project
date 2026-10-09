"""
interview.py — AI interview question generator, answer evaluator, and Career Advisor assistant.
Uses the official Google GenAI Python SDK (google-genai) with secure key resolution and graceful fallbacks.
"""

import os
import time
import streamlit as st

try:
    from google import genai
    from google.genai import types
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False


def get_gemini_api_key() -> str | None:
    """
    Retrieve Gemini API key securely from:
    1. In-session manual override (st.session_state["custom_gemini_api_key"])
    2. Streamlit secrets (st.secrets["GEMINI_API_KEY"], st.secrets["GOOGLE_API_KEY"], or nested [gemini] section)
    3. Environment variable (GEMINI_API_KEY or GOOGLE_API_KEY)
    Returns None if no key is configured.
    NEVER hardcodes or exposes the key.
    """
    # 1. Session state manual entry
    if "custom_gemini_api_key" in st.session_state and st.session_state["custom_gemini_api_key"]:
        key = str(st.session_state["custom_gemini_api_key"]).strip().strip('"\'')
        if key:
            return key

    # 2. Streamlit secrets
    try:
        if hasattr(st, "secrets"):
            for k in ("GEMINI_API_KEY", "GOOGLE_API_KEY", "gemini_api_key", "google_api_key"):
                if k in st.secrets and st.secrets[k]:
                    key = str(st.secrets[k]).strip().strip('"\'')
                    if key:
                        return key
            # Check nested table, e.g. [gemini] api_key = "..."
            if "gemini" in st.secrets:
                gemini_sec = st.secrets["gemini"]
                if isinstance(gemini_sec, dict) and "api_key" in gemini_sec and gemini_sec["api_key"]:
                    key = str(gemini_sec["api_key"]).strip().strip('"\'')
                    if key:
                        return key
    except Exception:
        pass

    # 3. Environment variables
    for env_var in ("GEMINI_API_KEY", "GOOGLE_API_KEY"):
        val = os.environ.get(env_var, "").strip().strip('"\'')
        if val:
            return val

    return None


def is_api_key_configured() -> bool:
    """Return True if a Gemini API key is detected."""
    return get_gemini_api_key() is not None


# Aliases for backward compatibility & consistency
is_gemini_api_key_configured = is_api_key_configured
get_api_key = get_gemini_api_key
get_openai_api_key = get_gemini_api_key

__all__ = [
    "get_gemini_api_key",
    "get_api_key",
    "get_openai_api_key",
    "is_api_key_configured",
    "is_gemini_api_key_configured",
    "get_gemini_client",
    "chat_career_advisor",
    "generate_questions",
    "evaluate_answer",
    "CAREER_ADVISOR_SYSTEM_PROMPT",
]


def get_gemini_client() -> "genai.Client | None":
    """Return an authenticated Google GenAI client or None if key is missing or SDK unavailable."""
    if not HAS_GEMINI:
        return None
    api_key = get_gemini_api_key()
    if not api_key:
        return None
    try:
        return genai.Client(
            api_key=api_key.strip().strip('"\''),
            vertexai=False,
        )
    except Exception:
        return None


CAREER_ADVISOR_SYSTEM_PROMPT = """You are "TwinAdvisor", the intelligent AI Career Twin Assistant embedded inside the AI Career Twin platform.
You assist students, job seekers, company recruiters, and platform visitors with end-to-end career, hiring, and platform workflows.

Your core capabilities:
1. **Platform Guidance**: Help users discover and navigate all platform features:
   - 📄 Resume Analysis (skill parsing & gap detection)
   - 🎯 Placement Predictor (probability modeling based on CGPA, projects & skills)
   - 📚 Smart Recommendations (custom learning roadmaps & certifications)
   - 🎤 AI Mock Interview (role-based technical and behavioral questions)
   - 🏢 Company Talent Pool (ranked candidate discovery and filtering)
2. **Career Guidance & Strategy**: Technical roadmaps, role transitions (Software Engineering, Data Science, AI/ML, Cloud/DevOps, Full Stack), and industry career milestones.
3. **Resume & Profile Optimization**: Action verbs, quantifiable achievements (STAR & Google X-Y-Z frameworks), ATS keyword alignment, and project highlights.
4. **Skills & Recommendations**: Closing skill gaps with prioritized frameworks, tools, and hands-on portfolio projects.
5. **Interview & Placement Prep**: Technical concepts, coding fundamentals, behavioral coaching, and practical strategies to maximize placement chances.
6. **Company & Talent Pool**: Assisting hiring teams with role criteria, candidate evaluation metrics, skill benchmarking, and interview question design.

Formatting guidelines:
- Use clean Markdown with clear headings, bullet points, and bold text for readability.
- Keep answers structured, actionable, and professional.
- If user context (role, detected skills, college, or company) is provided, tailor your responses directly to their situation.
"""


def _generate_offline_career_response(user_query: str, user_context: dict | None = None) -> str:
    """
    Generate a comprehensive, structured response when no Gemini API key is set.
    Ensures users always receive helpful, high-value guidance across the platform.
    """
    query_lower = user_query.lower()
    role_type = (user_context or {}).get("role", "guest")
    target_role = (user_context or {}).get("target_role") or (user_context or {}).get("role") or "Tech Professional"
    if target_role in ("student", "company", "guest"):
        target_role = "Software Engineer"
    skills = (user_context or {}).get("skills", [])
    skills_str = ", ".join(skills[:5]) if skills else "Python, SQL, Web Dev"

    # 1. Platform / Navigation questions
    if any(k in query_lower for k in ["platform", "feature", "navigate", "tool", "how does", "what can", "where do"]):
        return """### 🚀 AI Career Twin Platform Overview

Here is a guide to everything you can do on **AI Career Twin**:

1. **📄 Resume Analysis**: Upload your PDF resume to extract detected skills, identify skill gaps, and view matching roles.
2. **🎯 Placement Predictor**: Estimate your placement probability using CGPA, project count, internships, and core competencies.
3. **📚 Smart Recommendations**: Get tailored course and certification roadmaps specifically curated to close your missing skills.
4. **🎤 AI Mock Interview**: Practice interactive role-specific technical and behavioral interviews with automatic scoring.
5. **🏢 Talent Pool (Company Portal)**: Companies can browse, filter, and discover ranked student talent by tech stack and readiness.

💡 *Use the sidebar navigation on the left to jump straight into any feature!*"""

    # 2. Company / Hiring / Talent Pool questions
    elif any(k in query_lower for k in ["talent pool", "company", "hire", "recruiter", "filter candidate", "shortlist"]):
        return """### 🏢 Company & Talent Pool Guide

Welcome to the AI Career Twin hiring ecosystem:

1. **Ranked Candidate Search**:
   - Access the **Talent Pool** page in the sidebar to review verified student profiles.
   - Filter by primary role (Software Engineer, Data Scientist, ML Engineer), skills, and minimum placement readiness.
2. **Objective Skill Verification**:
   - Every candidate profile includes validated skill tags extracted via NLP from actual resumes.
   - Placement probability scores provide an objective benchmark for candidate readiness.
3. **Recruiter Best Practices**:
   - Combine core technical requirements with project evidence and communication indicators when reviewing finalists.

💡 *Connect a Gemini API key in `.streamlit/secrets.toml` to generate custom candidate assessment rubrics in real-time!*"""

    # 3. Resume questions
    elif any(k in query_lower for k in ["resume", "cv", "bullet", "ats"]):
        return f"""### 📄 Resume Optimization Strategies for {target_role}

Here are the highest-impact ways to optimize your resume right now:

1. **Use the Google "X-Y-Z" Formula**:
   - Instead of *"Built recommendation feature"*, write:
   - *"Engineered an item-based recommender in Python, boosting engagement by 18% across 5,000 active test sessions."*
2. **Prioritize Relevant Skills**:
   - Align your detected skills (**{skills_str}**) with the top 5 requirements on target job descriptions.
   - Group skills into clean categories: *Languages*, *Frameworks*, *Databases & Tools*.
3. **Pass the ATS (Applicant Tracking System)**:
   - Use clean, single-column formatting without nested tables or graphic skill meters.
   - Match industry standard keywords exactly as they appear in candidate postings.

💡 *Head to the **Resume Analysis** page to test your resume with our NLP extractor!*"""

    # 4. Interview questions
    elif any(k in query_lower for k in ["interview", "mock", "question", "prepare", "behavioral"]):
        return f"""### 🎤 Interview Preparation Framework

To stand out in technical and behavioral interviews for **{target_role}**:

1. **Master the STAR Method for Behavioral Questions**:
   - **Situation**: Context of a project challenge or team conflict.
   - **Task**: What your specific responsibility was.
   - **Action**: The technical decision or initiative you took.
   - **Result**: Quantifiable outcome or lesson learned.
2. **Core Technical Competencies**:
   - Review data structures, algorithms, system design fundamentals, and your primary stack (**{skills_str}**).
   - Be prepared to explain architectural tradeoffs in your top 2 portfolio projects.
3. **Questions to Ask the Interviewer**:
   - *"What does success look like in the first 90 days for this position?"*
   - *"How does your engineering team approach continuous code reviews and architecture decisions?"*

💡 *Try our built-in **AI Mock Interview** in the sidebar for interactive question sessions!*"""

    # 5. Skills / Recommendations
    elif any(k in query_lower for k in ["skill", "gap", "learn", "course", "certif"]):
        return f"""### 🎯 Skill Development & Roadmap for {target_role}

Based on current industry benchmarks:

1. **Core Foundations**: Ensure mastery of algorithmic problem solving, version control (Git), and REST API design.
2. **Specialized Tools**: Deepen your hands-on expertise in **{skills_str}**.
3. **Proof of Competence**: Build 2 end-to-end full-stack or ML deployment projects with live demonstrations and GitHub documentation.
4. **Targeted Certifications**: Earn recognized credentials (e.g. AWS Certified Cloud Practitioner, DeepLearning.AI, Meta).

💡 *Check out the **Recommendations** page in the sidebar for personalized course roadmaps!*"""

    # 6. General Platform Welcome / Overview
    else:
        return f"""### 💡 TwinAdvisor — Platform Assistant

Hello! I am **TwinAdvisor**, your intelligent assistant across the **AI Career Twin** platform.

Here are ways I can help you today:
- 🚀 **Platform Guidance**: Discover how our Resume Analyzer, Placement Predictor, and Talent Pool work together.
- 📄 **Resume Review**: Structure bullet points with quantifiable results and pass ATS screeners.
- 🎯 **Skill Roadmaps**: Identify and close skill gaps for **{target_role}** roles.
- 🎤 **Interview Coaching**: Practice technical and behavioral questions using the STAR framework.
- 🏢 **Hiring & Talent Pool**: Find out how recruiters filter and evaluate ranked candidates.

*Note: You are currently viewing built-in advisory mode. To unlock live generative responses with Google Gemini models (like Gemini 3.6 Flash), configure `GEMINI_API_KEY` in `.streamlit/secrets.toml` or the sidebar input.*"""


def chat_career_advisor(
    messages: list[dict],
    student_context: dict | None = None,
    model: str = "gemini-3.6-flash",
) -> tuple[bool, str]:
    """
    Send conversation history to Google Gemini generate_content.
    Returns (success: bool, response_text: str).
    Gracefully handles missing keys, quota issues, and network errors.
    """
    client = get_gemini_client()

    # If no API key configured, return helpful built-in response
    if client is None:
        latest_user_msg = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                latest_user_msg = m.get("content", "")
                break
        return True, _generate_offline_career_response(latest_user_msg, student_context)

    # Build prompt with rich user/role context
    system_prompt = CAREER_ADVISOR_SYSTEM_PROMPT
    if student_context:
        ctx_parts = []
        role_type = student_context.get("role", "")
        if role_type == "student":
            ctx_parts.append("User Type: Student")
            if student_context.get("name"):
                ctx_parts.append(f"Student Name: {student_context['name']}")
            if student_context.get("target_role"):
                ctx_parts.append(f"Target Role: {student_context['target_role']}")
            elif student_context.get("role") and student_context["role"] != "student":
                ctx_parts.append(f"Target Role: {student_context['role']}")
            if student_context.get("skills"):
                ctx_parts.append(f"Detected Skills: {', '.join(student_context['skills'])}")
            if student_context.get("college"):
                ctx_parts.append(f"College: {student_context['college']}")
            if student_context.get("branch"):
                ctx_parts.append(f"Branch: {student_context['branch']}")
            if student_context.get("placement_prob") is not None:
                ctx_parts.append(f"Placement Probability: {round(student_context['placement_prob'] * 100, 1)}%")
            if student_context.get("cgpa"):
                ctx_parts.append(f"CGPA: {student_context['cgpa']}")
        elif role_type == "company":
            ctx_parts.append("User Type: Company Recruiter / Hiring Partner")
            if student_context.get("company_name") or student_context.get("name"):
                ctx_parts.append(f"Company: {student_context.get('company_name') or student_context.get('name')}")
            if student_context.get("industry"):
                ctx_parts.append(f"Industry: {student_context['industry']}")
            if student_context.get("website"):
                ctx_parts.append(f"Website: {student_context['website']}")
        else:
            ctx_parts.append("User Type: Guest Visitor (exploring platform)")

        if ctx_parts:
            system_prompt += "\n\nActive User Profile Context:\n" + "\n".join(f"- {p}" for p in ctx_parts)

    try:
        # Build contents list
        contents = []
        for m in messages:
            role = "user" if m.get("role") == "user" else "model"
            text_content = m.get("content", "").strip()
            if text_content:
                contents.append(
                    types.Content(
                        role=role,
                        parts=[types.Part.from_text(text=text_content)]
                    )
                )

        if not contents:
            return False, "⚠️ No message content to send."

        primary_model = model or "gemini-3.6-flash"
        fallback_model = "gemini-2.5-flash" if primary_model != "gemini-2.5-flash" else "gemini-2.0-flash"
        gen_config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.7,
        )

        def _is_transient_error(error: Exception) -> bool:
            err_str = str(error).upper()
            return any(
                token in err_str
                for token in (
                    "503",
                    "UNAVAILABLE",
                    "429",
                    "RESOURCE_EXHAUSTED",
                    "HIGH DEMAND",
                    "SERVER BUSY",
                    "RATE LIMIT",
                    "QUOTA",
                    "DEADLINE_EXCEEDED",
                    "TIMEOUT",
                    "500",
                    "502",
                    "504",
                    "INTERNAL",
                )
            )

        # 1. Primary model with up to 2 retries on transient errors (exponential backoff: 1s, 2s)
        last_error = None
        max_retries = 2
        for attempt in range(max_retries + 1):
            try:
                response = client.models.generate_content(
                    model=primary_model,
                    contents=contents,
                    config=gen_config,
                )
                reply = response.text or ""
                return True, reply.strip()
            except Exception as e:
                last_error = e
                if attempt < max_retries and _is_transient_error(e):
                    time.sleep(1.0 * (2 ** attempt))
                    continue
                break

        # 2. If primary model still fails with a temporary error, try ONE fallback model
        if last_error and _is_transient_error(last_error):
            try:
                response = client.models.generate_content(
                    model=fallback_model,
                    contents=contents,
                    config=gen_config,
                )
                reply = response.text or ""
                return True, reply.strip()
            except Exception as e:
                last_error = e

        if last_error:
            raise last_error

    except Exception as e:
        err_msg = str(e)
        if "API key not valid" in err_msg or "INVALID_ARGUMENT" in err_msg or "API_KEY_INVALID" in err_msg:
            return False, "❌ **Gemini Authentication Error**: The configured Gemini API key is invalid. Please check your `GEMINI_API_KEY`."
        elif "UNAUTHENTICATED" in err_msg or "401" in err_msg or "ACCESS_TOKEN_TYPE_UNSUPPORTED" in err_msg:
            return False, "❌ **Gemini Authentication Error**: 401 UNAUTHENTICATED. Please verify your `GEMINI_API_KEY` in `.streamlit/secrets.toml`."
        elif "RESOURCE_EXHAUSTED" in err_msg or "Quota" in err_msg or "rate limit" in err_msg.lower():
            return False, "⚠️ **Gemini Rate Limit / Quota Exceeded**: Your Gemini API request limit has been reached. Please try again shortly."
        elif "503" in err_msg or "UNAVAILABLE" in err_msg or "high demand" in err_msg.lower():
            return False, "⚠️ **Gemini Server Busy (503)**: Google Gemini is currently experiencing high demand. Please try sending your message again in a moment."
        elif "BLOCKED" in err_msg:
            return False, "⚠️ **Gemini Safety Filter**: The response was filtered by content safety settings."
        else:
            return False, f"⚠️ **Gemini API Notice**: {err_msg}"


def generate_questions(role: str, count: int = 3) -> str:
    """Generate interview questions for a given role using Google Gemini API with fallback."""
    client = get_gemini_client()
    if client is None:
        return (
            f"1. Explain the fundamental principles of {role} and walk me through your recent project.\n"
            f"2. How do you approach debugging complex issues in a production environment?\n"
            f"3. Describe a time you had to learn a new framework or technology under a tight deadline."
        )

    try:
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=f"Generate {count} technical and behavioral interview questions for {role}.",
            config=types.GenerateContentConfig(temperature=0.7),
        )
        return response.text or "No questions generated."
    except Exception as e:
        return f"Could not generate questions via Gemini API ({e}). Defaulting to core {role} questions."


def evaluate_answer(answer: str, question: str = "") -> str:
    """Evaluate an interview answer and give feedback out of 10 using Google Gemini API with fallback."""
    client = get_gemini_client()
    if client is None:
        length = len(answer.split())
        score = 8 if length >= 30 else (6 if length >= 15 else 4)
        return (
            f"**Score**: {score}/10\n\n"
            f"**Feedback**: Your response is clear. To achieve a 10/10, expand with specific technical details, "
            f"tradeoffs considered, and quantifiable results using the STAR framework."
        )

    prompt = f"Evaluate this interview answer: '{answer}'"
    if question:
        prompt += f" for the question: '{question}'"
    prompt += ". Provide a score out of 10, strengths, and actionable improvement tips."

    try:
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0.7),
        )
        return response.text or "No evaluation generated."
    except Exception as e:
        return f"Could not evaluate answer via Gemini API ({e}). Score: 7/10."