"""
AI Career Twin - Formal AI Mock Interview
Live WebRTC Camera + Real-Time Face Monitoring
+ Camera check -> Mic/Noise check -> Exam

FLOW
====
1. CAMERA CHECK       - full-width, no question content beside it. Runs until
                        exactly one face is held stable for a short window,
                        then unlocks "Next".
2. MIC / NOISE CHECK  - candidate reads a prompted line out loud, we measure
                        mic input level (peak + ambient noise floor) via
                        streamlit-webrtc's audio track, and unlock "Start Test"
                        once voice was detected over a reasonably quiet floor.
3. EXAM               - the original interview flow, camera is now a small
                        picture-in-picture box shown above the answer
                        buttons, continuously
                        proctoring while questions are answered.
4. RESULTS            - unchanged.

NOTE ON THE CAMERA CONNECTION: the camera/mic widget uses a single,
constant `key` (CAMERA_KEY) across the camera check, mic check, and
the exam's pinned proctoring camera. streamlit-webrtc keeps the same
underlying peer connection alive for as long as the component key
doesn't change, so the candidate grants camera/mic access once, and
the feed just keeps running as they move on to later stages - they
are never asked to press "Start" again.
"""

import os
import sys
import threading
import time
import random
import logging
import numpy as np
import cv2
import streamlit as st

# The camera-check / mic-check / exam-question blocks use
# st.fragment(run_every=1) so the live camera state, mic level,
# and countdown timers keep refreshing every second without user
# interaction. Those same blocks also contain buttons (Next,
# Submit & Continue, Skip) that trigger a full-page st.rerun().
# When a button is clicked, Streamlit discards the current
# fragment and builds a fresh one - but the 1-second auto-refresh
# timer that was already scheduled *before* the click can still
# land a moment later, asking for a fragment id that no longer
# exists. Streamlit logs that as an info/warning message and
# simply drops the stale request; the newly created fragment's
# own timer picks up normally on its next tick. It's expected,
# harmless noise inherent to combining run_every with full
# reruns - not an error - so we just drop it below WARNING here
# instead of touching the app's actual logic.
logging.getLogger("streamlit.runtime.fragment").setLevel(
    logging.ERROR
)


# ============================================================
# PROJECT ROOT
# ============================================================

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


# ============================================================
# IMPORTS
# ============================================================

from auth import get_user, require_login
from database import get_student_profile, init_db
from interview_engine import InterviewEngine
from interview_evaluator import evaluate_answer
from camera_monitor import CameraMonitor
from speech_handler import speak
import streamlit.components.v1 as components

try:
    from streamlit_webrtc import (
        webrtc_streamer,
        WebRtcMode,
        VideoProcessorBase,
        AudioProcessorBase,
        RTCConfiguration,
    )

    WEBRTC_AVAILABLE = True

except ImportError:
    WEBRTC_AVAILABLE = False


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="AI Mock Interview",
    page_icon="🎤",
    layout="wide",
)


# ============================================================
# AUTHENTICATION
# ============================================================

init_db()
require_login("student")
user = get_user()


# ============================================================
# SESSION STATE
# ============================================================

if "interview_engine" not in st.session_state:
    st.session_state.interview_engine = None

if "interview_started" not in st.session_state:
    st.session_state.interview_started = False

if "camera_monitoring" not in st.session_state:
    st.session_state.camera_monitoring = True

if "session_code" not in st.session_state:
    st.session_state.session_code = None

# Proctored pre-flight flow stages:
# interview_flow_stage: "landing" -> "preflight" -> "interview"
# preflight_step: "camera" -> "mic" -> "fullscreen"
if "interview_flow_stage" not in st.session_state:
    st.session_state.interview_flow_stage = "landing"

if "preflight_step" not in st.session_state:
    st.session_state.preflight_step = "camera"

if "camera_check_passed" not in st.session_state:
    st.session_state.camera_check_passed = False

if "mic_check_passed" not in st.session_state:
    st.session_state.mic_check_passed = False

if "fullscreen_passed" not in st.session_state:
    st.session_state.fullscreen_passed = False

if "hardware_camera_ok" not in st.session_state:
    st.session_state.hardware_camera_ok = None

if "voice_tested" not in st.session_state:
    st.session_state.voice_tested = False

if "camera_stable_since" not in st.session_state:
    st.session_state.camera_stable_since = None

if "mic_prompt_phrase" not in st.session_state:
    st.session_state.mic_prompt_phrase = None

if "mic_voice_detected" not in st.session_state:
    st.session_state.mic_voice_detected = False

if "mic_ambient_ok" not in st.session_state:
    st.session_state.mic_ambient_ok = None


# ============================================================
# DESIGN SYSTEM / CSS
# ============================================================
# Visual identity: a formal proctored-exam interface (the kind
# used by corporate assessment platforms), not a generic chat
# UI. Ink-navy surfaces, a brass/gold accent reserved for
# official marks (section numerals, the candidate's exam code),
# a signal-blue accent for primary actions, and the required
# green / amber / red semantics for the live face-monitoring
# state. Display type is a serif (exam-paper / certificate
# feel), body type is a clean grotesk, and data (timers, frame
# counters, exam codes) is set in mono.
#
# NOTE ON STREAMLIT STYLING: Streamlit does not expose class
# hooks on its native widgets (buttons, text areas, progress
# bars, the WebRTC component). The selectors below target
# Streamlit's documented data-testid / kind attributes, which
# are the standard way to skin native widgets, but they can
# shift between Streamlit versions. If a widget below doesn't
# pick up the new look after upgrading Streamlit, the selector
# name is the first thing to check.
# ============================================================

st.markdown(
    """
<style>

@import url('https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,500;8..60,600;8..60,700&family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap');

:root {
    --ink:        #0A0E1A;
    --panel:      #121826;
    --panel-2:    #171F30;
    --hairline:   #2A3348;
    --ivory:      #E8EAF2;
    --muted:      #8891A7;
    --gold:       #C9A227;
    --gold-dim:   #6E5C1E;
    --signal:     #375DFB;
    --signal-dim: #24346B;
    --ok:         #16A34A;
    --ok-bg:      #0E2A1A;
    --bad:        #DC2626;
    --bad-bg:     #2B1416;
    --warn:       #D97706;
    --warn-bg:    #2B2010;

    --font-display: 'Source Serif 4', Georgia, serif;
    --font-body: 'IBM Plex Sans', -apple-system, sans-serif;
    --font-mono: 'IBM Plex Mono', 'Courier New', monospace;
}

/* ---------- page canvas ---------- */

.stApp {
    background: var(--ink);
}

html, body, [class*="css"] {
    font-family: var(--font-body);
    color: var(--ivory);
}

/* ---------- masthead ---------- */

.exam-masthead {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    border-bottom: 2px solid var(--hairline);
    padding-bottom: 14px;
    margin-bottom: 6px;
}

.exam-masthead .brand {
    font-family: var(--font-display);
    font-size: 26px;
    font-weight: 700;
    letter-spacing: 0.3px;
    color: var(--ivory);
}

.exam-masthead .brand .mark {
    color: var(--gold);
}

.exam-masthead .tagline {
    font-family: var(--font-mono);
    font-size: 12px;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: var(--muted);
}

/* ---------- exam session bar ---------- */

.exam-session-bar {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: space-between;
    gap: 14px;
    background: var(--panel);
    border: 1px solid var(--hairline);
    border-radius: 10px;
    padding: 14px 20px;
    margin: 16px 0 22px 0;
}

.exam-session-bar .field-label {
    font-family: var(--font-mono);
    font-size: 10.5px;
    letter-spacing: 1.2px;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 2px;
}

.exam-session-bar .field-value {
    font-family: var(--font-body);
    font-size: 14.5px;
    font-weight: 600;
    color: var(--ivory);
}

.exam-session-bar .field-value.mono {
    font-family: var(--font-mono);
    letter-spacing: 0.5px;
    color: var(--gold);
}

/* ---------- proctoring badge (pill + LED) ---------- */

.proctor-badge {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 7px 14px;
    border-radius: 999px;
    font-family: var(--font-mono);
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.8px;
    text-transform: uppercase;
    border: 1px solid var(--hairline);
}

.proctor-badge .led {
    width: 9px;
    height: 9px;
    border-radius: 50%;
    display: inline-block;
    box-shadow: 0 0 0 3px rgba(255,255,255,0.04);
}

.proctor-badge.ok      { background: var(--ok-bg);   color: #86EFAC; border-color: #1F5C36; }
.proctor-badge.ok .led      { background: var(--ok);   box-shadow: 0 0 8px var(--ok); }

.proctor-badge.bad     { background: var(--bad-bg);  color: #FCA5A5; border-color: #6B2226; }
.proctor-badge.bad .led     { background: var(--bad);  box-shadow: 0 0 8px var(--bad); }

.proctor-badge.warn    { background: var(--warn-bg); color: #FCD34D; border-color: #6B4A11; }
.proctor-badge.warn .led    { background: var(--warn); box-shadow: 0 0 8px var(--warn); }

.proctor-badge.off     { background: var(--panel-2); color: var(--muted); border-color: var(--hairline); }
.proctor-badge.off .led     { background: var(--muted); }

/* ---------- section roadmap (stepper) ---------- */

.exam-roadmap {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    margin: 4px 0 22px 0;
}

.exam-roadmap .step {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    position: relative;
}

.exam-roadmap .step::before {
    content: "";
    position: absolute;
    top: 14px;
    left: -50%;
    width: 100%;
    height: 1px;
    background: var(--hairline);
    z-index: 0;
}

.exam-roadmap .step:first-child::before {
    display: none;
}

.exam-roadmap .step.done::before,
.exam-roadmap .step.current::before {
    background: var(--gold-dim);
}

.exam-roadmap .num {
    position: relative;
    z-index: 1;
    width: 28px;
    height: 28px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: var(--font-mono);
    font-size: 12px;
    font-weight: 600;
    background: var(--panel);
    border: 1px solid var(--hairline);
    color: var(--muted);
}

.exam-roadmap .step.current .num {
    background: var(--gold);
    border-color: var(--gold);
    color: #1A1400;
}

.exam-roadmap .step.done .num {
    background: var(--panel-2);
    border-color: var(--gold-dim);
    color: var(--gold);
}

.exam-roadmap .label {
    margin-top: 6px;
    font-size: 11px;
    letter-spacing: 0.3px;
    color: var(--muted);
}

.exam-roadmap .step.current .label {
    color: var(--ivory);
    font-weight: 600;
}

/* ---------- proctoring monitor panel (camera, full-check screen) ---------- */

.monitor-frame {
    border: 1px solid var(--hairline);
    border-radius: 12px;
    background: var(--panel);
    padding: 14px 14px 18px 14px;
    margin-bottom: 10px;
}

.monitor-frame .monitor-titlebar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 10px;
}

.monitor-frame .monitor-title {
    font-family: var(--font-mono);
    font-size: 11px;
    letter-spacing: 1.2px;
    text-transform: uppercase;
    color: var(--muted);
}

/* ---------- genuinely size-constrained camera boxes ----------
   These target the wrapper class Streamlit attaches to a real
   st.container(key=...) (a true DOM parent of everything drawn
   inside the `with` block - unlike an unclosed st.markdown
   '<div>', which does NOT actually contain later Streamlit
   elements). Capping max-width here reliably shrinks the video
   itself, not just the text around it. */

.st-key-camera-check-box,
.st-key-mic-check-box {
    max-width: 340px;
    margin: 0 auto 10px auto;
    border: 1px solid var(--hairline);
    border-radius: 12px;
    background: var(--panel);
    padding: 12px 12px 16px 12px;
}

.st-key-camera-check-box video,
.st-key-mic-check-box video {
    border-radius: 8px;
    width: 100% !important;
    height: auto !important;
}

.st-key-camera-check-box iframe,
.st-key-mic-check-box iframe,
.st-key-camera-check-box div[data-testid="stCustomComponentV1"],
.st-key-mic-check-box div[data-testid="stCustomComponentV1"] {
    max-width: 100% !important;
}

.st-key-pip-cam-box {
    /* Deliberately NOT position:fixed. Streamlit nests this
       container several levels deep inside elements that can
       carry their own CSS transform/overflow context (used for
       Streamlit's own scroll/reflow handling), and any such
       ancestor turns position:fixed children into something
       that behaves like position:absolute relative to *that*
       ancestor instead of the viewport - which can clip the box
       down to nothing. Rendering inline, in normal flow, avoids
       that failure mode entirely and is what actually shows up
       reliably during the exam. */
    width: 220px;
    background: var(--panel);
    border: 1px solid var(--hairline);
    border-radius: 10px;
    padding: 8px 8px 10px 8px;
    margin: 4px 0 16px 0;
}

.st-key-pip-cam-box video {
    border-radius: 6px;
    width: 100% !important;
    height: auto !important;
}

.st-key-pip-cam-box iframe,
.st-key-pip-cam-box div[data-testid="stCustomComponentV1"] {
    max-width: 100% !important;
}

/* ---------- onboarding gate screens (camera / mic) ---------- */

.gate-wrap {
    max-width: 760px;
    margin: 30px auto 0 auto;
}

.gate-card {
    background: var(--panel);
    border: 1px solid var(--hairline);
    border-radius: 14px;
    padding: 34px 36px;
    text-align: center;
}

.gate-card .gate-eyebrow {
    font-family: var(--font-mono);
    font-size: 11px;
    letter-spacing: 1.4px;
    text-transform: uppercase;
    color: var(--gold);
    margin-bottom: 10px;
}

.gate-card .gate-title {
    font-family: var(--font-display);
    font-size: 26px;
    font-weight: 700;
    color: var(--ivory);
    margin-bottom: 10px;
}

.gate-card .gate-body {
    font-size: 14.5px;
    color: var(--muted);
    line-height: 1.6;
    max-width: 520px;
    margin: 0 auto;
}

.mic-phrase-box {
    background: var(--panel-2);
    border: 1px dashed var(--gold-dim);
    border-radius: 10px;
    padding: 18px 22px;
    margin: 18px 0;
}

.mic-phrase-box .phrase-label {
    font-family: var(--font-mono);
    font-size: 10.5px;
    letter-spacing: 1.2px;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 6px;
}

.mic-phrase-box .phrase-text {
    font-family: var(--font-display);
    font-size: 22px;
    font-weight: 600;
    color: var(--gold);
}

.level-meter-wrap {
    background: var(--panel-2);
    border: 1px solid var(--hairline);
    border-radius: 8px;
    height: 14px;
    overflow: hidden;
    margin-top: 8px;
}

.level-meter-fill {
    height: 100%;
    border-radius: 8px;
    transition: width 0.15s ease-out;
}

/* ---------- exam-paper question card ---------- */

.exam-paper {
    background: linear-gradient(180deg, var(--panel) 0%, var(--panel-2) 100%);
    border: 1px solid var(--hairline);
    border-top: 3px solid var(--gold);
    border-radius: 4px 4px 14px 14px;
    padding: 30px 32px;
    margin-bottom: 18px;
}

.exam-paper .eyebrow {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 16px;
}

.exam-paper .section-tag {
    font-family: var(--font-mono);
    font-size: 11px;
    letter-spacing: 1.2px;
    text-transform: uppercase;
    color: var(--gold);
    border: 1px solid var(--gold-dim);
    border-radius: 4px;
    padding: 3px 9px;
}

.exam-paper .difficulty-tag {
    font-family: var(--font-mono);
    font-size: 11px;
    letter-spacing: 1px;
    text-transform: uppercase;
    color: var(--muted);
}

.exam-paper .q-number {
    font-family: var(--font-display);
    font-size: 15px;
    color: var(--muted);
    margin-bottom: 6px;
}

.exam-paper .q-number b {
    color: var(--gold);
    font-size: 17px;
}

.exam-paper .q-text {
    font-family: var(--font-display);
    font-size: 22px;
    line-height: 1.55;
    color: var(--ivory);
    font-weight: 600;
}

/* ---------- candidate instructions (setup screen) ---------- */

.instruction-panel {
    background: var(--panel);
    border: 1px solid var(--hairline);
    border-radius: 10px;
    padding: 22px 24px;
}

.instruction-panel .item {
    display: flex;
    gap: 10px;
    padding: 8px 0;
    border-bottom: 1px solid rgba(255,255,255,0.04);
    font-size: 14px;
    color: var(--ivory);
}

.instruction-panel .item:last-child {
    border-bottom: none;
}

.instruction-panel .item .tick {
    color: var(--gold);
    font-family: var(--font-mono);
}

.candidate-card {
    background: var(--panel-2);
    border: 1px solid var(--hairline);
    border-radius: 10px;
    padding: 20px 22px;
}

.candidate-card .role-label {
    font-family: var(--font-mono);
    font-size: 11px;
    letter-spacing: 1.2px;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 6px;
}

.candidate-card .role-value {
    font-family: var(--font-display);
    font-size: 26px;
    font-weight: 700;
    color: var(--ivory);
}

/* ---------- certificate / results card ---------- */

.result-card {
    background: linear-gradient(160deg, #0E1B14 0%, var(--panel) 65%);
    border: 1px solid #1F5C36;
    border-radius: 16px;
    padding: 40px;
    text-align: center;
}

.result-card .seal {
    font-family: var(--font-mono);
    font-size: 12px;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: #86EFAC;
    margin-bottom: 6px;
}

.result-card .headline {
    font-family: var(--font-display);
    font-size: 28px;
    font-weight: 700;
    color: var(--ivory);
}

/* ---------- pinned proctoring camera titlebar (bottom-left, during exam) ---------- */
/* Sizing/positioning for the box itself lives on .st-key-pip-cam-box
   above, since that's the real container that wraps the camera. */

.pip-titlebar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 6px;
    padding: 0 2px;
}

.pip-title {
    font-family: var(--font-mono);
    font-size: 9.5px;
    letter-spacing: 1px;
    text-transform: uppercase;
    color: var(--muted);
}

/* ---------- native widget skinning ---------- */

/* buttons */
div.stButton > button {
    font-family: var(--font-body);
    font-weight: 600;
    border-radius: 8px;
    border: 1px solid var(--hairline);
}

div.stButton > button[kind="primary"],
div.stButton > button[data-testid="baseButton-primary"] {
    background: var(--signal);
    border-color: var(--signal);
    color: #ffffff;
}

div.stButton > button[kind="secondary"],
div.stButton > button[data-testid="baseButton-secondary"] {
    background: transparent;
    border-color: var(--hairline);
    color: var(--ivory);
}

div.stButton > button:disabled {
    opacity: 0.45;
}

/* progress bar */
div.stProgress > div > div > div {
    background-color: var(--gold) !important;
}

/* text area */
textarea {
    background: var(--panel-2) !important;
    color: var(--ivory) !important;
    border: 1px solid var(--hairline) !important;
    font-family: var(--font-body) !important;
}

/* expander (answer log) & details contrast */
details {
    background: var(--panel) !important;
    border: 1px solid var(--hairline) !important;
    border-radius: 8px !important;
    color: var(--ivory) !important;
}

details summary {
    color: var(--ivory) !important;
    font-weight: 600 !important;
    font-size: 14.5px !important;
    padding: 10px 14px !important;
}

details[open] summary {
    color: #93C5FD !important;
    border-bottom: 1px solid var(--hairline) !important;
}

details div[data-testid="stExpanderDetails"] {
    background: var(--panel) !important;
    color: var(--ivory) !important;
    padding: 16px !important;
}

/* results screen metrics & report cards */
div[data-testid="stMetricValue"] {
    color: var(--ivory) !important;
    font-weight: 700 !important;
}

div[data-testid="stMetricLabel"] {
    color: var(--muted) !important;
    font-weight: 600 !important;
}

.report-summary-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 14px;
    margin: 16px 0 20px 0;
}

.report-metric-card {
    background: var(--panel);
    border: 1px solid var(--hairline);
    border-radius: 12px;
    padding: 16px 18px;
    text-align: center;
}

.report-metric-label {
    font-size: 12px;
    font-weight: 600;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 0.8px;
    margin-bottom: 6px;
}

.report-metric-val {
    font-size: 28px;
    font-weight: 700;
    color: var(--ivory);
    font-family: var(--font-display);
}

.report-section-card {
    background: var(--panel);
    border: 1px solid var(--hairline);
    border-radius: 12px;
    padding: 20px 22px;
    margin-bottom: 18px;
    text-align: left;
}

.report-section-hdr {
    font-size: 16.5px;
    font-weight: 700;
    color: var(--ivory);
    margin-bottom: 12px;
    display: flex;
    align-items: center;
    gap: 8px;
}

.report-feedback-box {
    background: #14203A;
    border: 1px solid var(--signal-dim);
    border-radius: 8px;
    padding: 14px 18px;
    color: var(--ivory);
    font-size: 14px;
    line-height: 1.6;
}

.report-item-green {
    background: var(--ok-bg);
    border: 1px solid #1F5C36;
    border-radius: 8px;
    padding: 10px 14px;
    color: #86EFAC;
    font-size: 13.5px;
    line-height: 1.5;
    margin-bottom: 8px;
}

.report-item-amber {
    background: var(--warn-bg);
    border: 1px solid #6B4A11;
    border-radius: 8px;
    padding: 10px 14px;
    color: #FCD34D;
    font-size: 13.5px;
    line-height: 1.5;
    margin-bottom: 8px;
}

.q-box-answer {
    background: var(--panel-2);
    border: 1px solid var(--hairline);
    border-radius: 6px;
    padding: 10px 14px;
    color: var(--ivory);
    font-size: 14px;
    margin-top: 6px;
    line-height: 1.5;
}

.q-box-skipped {
    background: #231B10;
    border: 1px solid #5C3D10;
    border-radius: 6px;
    padding: 10px 14px;
    color: #FCD34D;
    font-size: 13.5px;
    margin-top: 6px;
}

.feedback-pill-good {
    background: var(--ok-bg);
    border: 1px solid #1F5C36;
    border-radius: 6px;
    padding: 10px 14px;
    color: #86EFAC;
    font-size: 13.5px;
    margin-bottom: 10px;
    line-height: 1.4;
}

.feedback-pill-warn {
    background: var(--warn-bg);
    border: 1px solid #6B4A11;
    border-radius: 6px;
    padding: 10px 14px;
    color: #FCD34D;
    font-size: 13.5px;
    margin-bottom: 10px;
    line-height: 1.4;
}

.eval-score-tag {
    display: inline-block;
    background: var(--panel-2);
    border: 1px solid var(--hairline);
    border-radius: 6px;
    padding: 3px 8px;
    font-size: 12px;
    color: var(--ivory);
    margin-right: 8px;
}

/* ---------- pre-flight status cards & styles ---------- */

.preflight-status-card {
    background: var(--panel);
    border: 1px solid var(--hairline);
    border-radius: 12px;
    padding: 16px 18px;
    text-align: left;
    margin-bottom: 12px;
    transition: all 0.2s ease;
}

.preflight-status-card.ready {
    border-color: #1F5C36;
    background: linear-gradient(180deg, #0e2016 0%, var(--panel) 100%);
}

.preflight-status-card.pending {
    border-color: var(--hairline);
}

.preflight-card-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 6px;
}

.preflight-card-title {
    font-size: 14px;
    font-weight: 600;
    color: var(--ivory);
}

.status-pill {
    font-family: var(--font-mono);
    font-size: 10px;
    letter-spacing: 0.8px;
    text-transform: uppercase;
    padding: 3px 8px;
    border-radius: 999px;
    font-weight: 600;
}

.status-pill.ok {
    background: #0E2216;
    border: 1px solid #1F5C36;
    color: #86EFAC;
}

.status-pill.pending {
    background: #241A0B;
    border: 1px solid #6B4A11;
    color: #FCD34D;
}

.status-pill.bad {
    background: #261114;
    border: 1px solid #6B2226;
    color: #FCA5A5;
}

.preflight-card-desc {
    font-size: 12px;
    color: var(--muted);
    line-height: 1.4;
}

.preflight-box {
    background: var(--panel);
    border: 1px solid var(--hairline);
    border-radius: 12px;
    padding: 18px 20px;
    margin-bottom: 14px;
}

</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# REAL-TIME CAMERA PROCESSOR
# ============================================================

# A single, constant streamlit-webrtc component key used for the
# camera check, the mic check, and the exam's pinned proctoring
# camera. Keeping the key identical across every stage is what
# lets the same underlying peer connection stay alive the whole
# time - the candidate grants camera/mic permission once and is
# never asked to press "Start" again when moving to the next
# stage. Audio is always requested alongside video (see
# render_camera() below) so the media constraints never change
# either, which would otherwise also force a reconnect.
CAMERA_KEY = "proctor-camera"

camera_lock = threading.Lock()


class InterviewVideoProcessor(VideoProcessorBase):

    _latest_instance = None
    _latest_state = {
        "face_count": 0,
        "face_detected": False,
        "movement": "No face",
        "movement_distance": 0,
        "frames": 0,
    }

    def __init__(self):

        self.face_count = 0
        self.face_detected = False

        self.frames = 0

        self.movement = "Stable"

        self.previous_center = None

        self.movement_distance = 0

        self.running = True

        self.last_faces = ()

        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades
            + "haarcascade_frontalface_default.xml"
        )

        with camera_lock:
            InterviewVideoProcessor._latest_instance = self

    # --------------------------------------------------------
    # THREAD-SAFE STATE ACCESSORS
    # --------------------------------------------------------
    # streamlit-webrtc runs recv() on a dedicated background
    # processing thread, separate from the thread that executes
    # the Streamlit script. Reading self.face_count / etc.
    # directly from the Streamlit thread without synchronization
    # is a data race. get_state() takes a snapshot of all the
    # fields the UI needs while holding the same camera_lock
    # that recv() uses when writing them, so the UI always sees
    # a consistent, up-to-date snapshot instead of a stale or
    # partially-updated value.
    # --------------------------------------------------------

    def get_state(self):

        with camera_lock:

            return {
                "face_count": self.face_count,
                "face_detected": self.face_detected,
                "movement": self.movement,
                "movement_distance": self.movement_distance,
                "frames": self.frames,
            }

    @classmethod
    def get_latest_active_state(cls):
        with camera_lock:
            if cls._latest_instance is not None:
                inst_state = cls._latest_instance.get_state()
                if inst_state.get("frames", 0) > 0:
                    return inst_state
            if cls._latest_state.get("frames", 0) > 0:
                return dict(cls._latest_state)
            return None

    def recv(self, frame):

        image = frame.to_ndarray(
            format="bgr24"
        )

        with camera_lock:
            self.frames += 1
            current_frame_idx = self.frames
            InterviewVideoProcessor._latest_instance = self
            InterviewVideoProcessor._latest_state["frames"] = self.frames

        # ----------------------------------------------------
        # Scaling parameters (processing width reduced to 480)
        # ----------------------------------------------------

        height, width = image.shape[:2]

        processing_width = 480

        if width > processing_width:

            scale = (
                processing_width / width
            )

            inverse_scale = (
                width / processing_width
            )

        else:

            scale = 1.0
            inverse_scale = 1.0

        # ----------------------------------------------------
        # Face detection - runs only every 3rd incoming frame
        # ----------------------------------------------------

        is_detection_frame = (current_frame_idx % 3 == 1)

        if is_detection_frame:

            if width > processing_width:

                processing_height = int(
                    height * scale
                )

                small_image = cv2.resize(
                    image,
                    (
                        processing_width,
                        processing_height
                    )
                )

            else:

                small_image = image

            # ------------------------------------------------
            # Grayscale
            # ------------------------------------------------

            gray = cv2.cvtColor(
                small_image,
                cv2.COLOR_BGR2GRAY
            )

            gray = cv2.equalizeHist(
                gray
            )

            # ------------------------------------------------
            # Face detection
            # ------------------------------------------------

            faces = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(50, 50),
            )

            self.last_faces = faces

            # NOTE: face detection algorithm itself is unchanged.
            # Only the assignment of the shared face_count /
            # face_detected fields is now protected by camera_lock
            # so the Streamlit thread never reads a half-written
            # value.
            with camera_lock:

                self.face_count = len(faces)

                self.face_detected = (
                    self.face_count > 0
                )
                InterviewVideoProcessor._latest_state["face_count"] = self.face_count
                InterviewVideoProcessor._latest_state["face_detected"] = self.face_detected

        else:

            # On skipped frames, retain previous face_count/face_detected/movement state
            faces = self.last_faces

        # ----------------------------------------------------
        # Face processing (render boxes on image)
        # ----------------------------------------------------

        current_center = None

        for index, (
            x,
            y,
            w,
            h
        ) in enumerate(faces):

            x = int(
                x * inverse_scale
            )

            y = int(
                y * inverse_scale
            )

            w = int(
                w * inverse_scale
            )

            h = int(
                h * inverse_scale
            )

            center_x = x + w // 2
            center_y = y + h // 2

            if index == 0:

                current_center = (
                    center_x,
                    center_y
                )

                color = (
                    0,
                    255,
                    0
                )

            else:

                color = (
                    0,
                    165,
                    255
                )

            cv2.rectangle(
                image,
                (x, y),
                (x + w, y + h),
                color,
                3
            )

            cv2.circle(
                image,
                (
                    center_x,
                    center_y
                ),
                6,
                color,
                -1
            )

        # ----------------------------------------------------
        # Movement calculation (updated only on detection frames)
        # ----------------------------------------------------

        if is_detection_frame:

            if current_center is not None:

                if self.previous_center is not None:

                    dx = (
                        current_center[0]
                        - self.previous_center[0]
                    )

                    dy = (
                        current_center[1]
                        - self.previous_center[1]
                    )

                    distance = (
                        (dx ** 2 + dy ** 2)
                        ** 0.5
                    )

                    if distance > 35:

                        movement_label = "Moving"

                    elif distance > 12:

                        movement_label = (
                            "Slight movement"
                        )

                    else:

                        movement_label = "Stable"

                    with camera_lock:

                        self.movement_distance = (
                            round(distance, 2)
                        )

                        self.movement = movement_label
                        InterviewVideoProcessor._latest_state["movement"] = self.movement
                        InterviewVideoProcessor._latest_state["movement_distance"] = self.movement_distance

                self.previous_center = (
                    current_center
                )

            else:

                with camera_lock:

                    self.movement = "No face"

                    self.movement_distance = 0
                    InterviewVideoProcessor._latest_state["movement"] = "No face"
                    InterviewVideoProcessor._latest_state["movement_distance"] = 0

        # ====================================================
        # LIVE VIDEO OVERLAY
        # ====================================================

        overlay = image.copy()

        cv2.rectangle(
            overlay,
            (10, 10),
            (440, 145),
            (10, 15, 25),
            -1
        )

        image = cv2.addWeighted(
            overlay,
            0.80,
            image,
            0.20,
            0
        )

        # ----------------------------------------------------
        # Status
        # ----------------------------------------------------

        if self.face_count == 1:

            status = "FACE DETECTED"

            status_color = (
                0,
                255,
                0
            )

        elif self.face_count > 1:

            status = (
                "MULTIPLE FACES"
            )

            status_color = (
                0,
                165,
                255
            )

        else:

            status = (
                "FACE NOT DETECTED"
            )

            status_color = (
                0,
                0,
                255
            )

        cv2.putText(
            image,
            status,
            (25, 45),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.75,
            status_color,
            2,
            cv2.LINE_AA
        )

        # ----------------------------------------------------
        # Faces
        # ----------------------------------------------------

        cv2.putText(
            image,
            f"Faces: {self.face_count}",
            (25, 78),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (255, 255, 255),
            2,
            cv2.LINE_AA
        )

        # ----------------------------------------------------
        # Movement
        # ----------------------------------------------------

        if self.movement == "Moving":

            movement_color = (
                0,
                165,
                255
            )

        elif self.movement == "No face":

            movement_color = (
                0,
                0,
                255
            )

        else:

            movement_color = (
                0,
                255,
                0
            )

        cv2.putText(
            image,
            f"Movement: {self.movement}",
            (25, 110),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.60,
            movement_color,
            2,
            cv2.LINE_AA
        )

        # ----------------------------------------------------
        # Frame counter
        # ----------------------------------------------------

        cv2.putText(
            image,
            f"Live frames: {self.frames}",
            (25, 137),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.50,
            (200, 200, 200),
            1,
            cv2.LINE_AA
        )

        # ====================================================
        # RETURN LIVE FRAME
        # ====================================================

        return frame.from_ndarray(
            image,
            format="bgr24"
        )


# ============================================================
# REAL-TIME AUDIO PROCESSOR (mic / noise check)
# ============================================================

audio_lock = threading.Lock()


class InterviewAudioProcessor(AudioProcessorBase):
    """
    Tracks a rolling peak level and an ambient noise floor from
    the mic track so the mic-check screen can tell the candidate
    apart from a silent/broken mic vs. a noisy room.

    - peak_level:     highest recent RMS amplitude (0-1 scale),
                       used to detect "candidate spoke".
    - floor_level:     slow-moving average RMS, used as an
                       ambient-noise estimate when the candidate
                       is *not* actively talking (i.e. the
                       quietest recent stretch).
    - current_level:   most recent RMS, drives the live meter.
    """

    def __init__(self):

        self.current_level = 0.0
        self.peak_level = 0.0
        self.floor_level = 0.0

        self._floor_initialized = False

        self.frames_seen = 0

    def get_state(self):

        with audio_lock:

            return {
                "current_level": self.current_level,
                "peak_level": self.peak_level,
                "floor_level": self.floor_level,
                "frames_seen": self.frames_seen,
            }

    def reset(self):

        with audio_lock:

            self.current_level = 0.0
            self.peak_level = 0.0
            self.floor_level = 0.0
            self._floor_initialized = False
            self.frames_seen = 0

    def _process_audio_frame(self, frame):
        """
        Update the rolling level stats from a single incoming
        audio frame. Pulled out into its own method so both
        recv() (single-frame path) and recv_queued() (whole-
        backlog path, see below) share one implementation
        instead of duplicating the RMS/floor-tracking logic.
        """

        samples = frame.to_ndarray()

        # Normalize to float in [-1, 1] regardless of the
        # incoming integer sample width, then compute RMS as a
        # simple, cheap loudness proxy.
        if samples.dtype.kind == "i":

            max_val = float(
                np.iinfo(samples.dtype).max
            )

            float_samples = (
                samples.astype(np.float32) / max_val
            )

        else:

            float_samples = samples.astype(np.float32)

        rms = float(
            np.sqrt(
                np.mean(
                    np.square(float_samples)
                )
                + 1e-12
            )
        )

        with audio_lock:

            self.frames_seen += 1

            self.current_level = rms

            if rms > self.peak_level:

                self.peak_level = rms

            # Ambient floor: an exponential moving average that
            # leans toward quiet stretches, so a brief spoken
            # word doesn't drag the "room noise" estimate up
            # with it. We only let the floor rise slowly, but
            # let it fall quickly.
            if not self._floor_initialized:

                self.floor_level = rms

                self._floor_initialized = True

            elif rms < self.floor_level:

                self.floor_level = (
                    0.6 * self.floor_level + 0.4 * rms
                )

            else:

                self.floor_level = (
                    0.98 * self.floor_level + 0.02 * rms
                )

    def _silence_audio_frame(self, frame):
        """
        Zero out audio samples so incoming microphone audio is analyzed
        for level and noise stats but never echoed/routed back to the
        candidate through the WebRTC audio output.
        """
        try:
            for p in frame.planes:
                p.update(b"\x00" * p.buffer_size)
        except Exception:
            pass
        return frame

    def recv(self, frame):
        """
        Single-frame path, kept for interface compatibility.
        Processes incoming microphone audio for RMS/peak/ambient-floor
        monitoring, then zeroes out the samples so the audio is not
        echoed back through WebRTC output.
        """

        self._process_audio_frame(frame)

        return self._silence_audio_frame(frame)

    async def recv_queued(self, frames):
        """
        Whole-backlog path.
        Processes incoming microphone frames for RMS/peak/ambient-floor
        monitoring, then zeroes out each frame before returning so
        microphone input is not played/echoed back through WebRTC output.
        """

        for frame in frames:

            self._process_audio_frame(frame)
            self._silence_audio_frame(frame)

        return frames


# ============================================================
# CAMERA COMPONENT
# ============================================================

def render_camera(key, audio_enabled=False, video_html_attrs=None):
    """
    Renders the WebRTC camera widget and returns the webrtc
    context object (ctx). ctx.video_processor always points to
    the *currently running* InterviewVideoProcessor instance
    for this browser session, so callers can pull the latest
    face-detection state on every Streamlit script run instead
    of relying on a value that was copied into session_state
    once and then goes stale.

    `key` must be unique per distinct camera instance on the
    page (camera-check screen vs. mic-check screen vs. the
    pinned exam camera all use different keys so each gets its
    own independent peer connection / processor).
    """

    if not WEBRTC_AVAILABLE:

        st.error(
            "streamlit-webrtc is not installed."
        )

        st.code(
            "pip install streamlit-webrtc opencv-python av numpy"
        )

        return None

    rtc_configuration = RTCConfiguration(
        {
            "iceServers": [
                {
                    "urls": [
                        "stun:stun.l.google.com:19302"
                    ]
                }
            ]
        }
    )

    mode = WebRtcMode.SENDRECV

    media_stream_constraints = {
        "video": True,
        "audio": audio_enabled,
    }

    kwargs = dict(
        key=key,
        mode=mode,
        rtc_configuration=rtc_configuration,
        media_stream_constraints=media_stream_constraints,
        video_processor_factory=InterviewVideoProcessor,
        async_processing=True,
        desired_playing_state=True,
        media_toggle_controls=False,
    )

    if audio_enabled:

        kwargs["audio_processor_factory"] = (
            InterviewAudioProcessor
        )

    try:
        ctx = webrtc_streamer(**kwargs)
    except TypeError:
        compat_kwargs = {k: v for k, v in kwargs.items() if k != "media_toggle_controls"}
        ctx = webrtc_streamer(**compat_kwargs)

    return ctx


def get_live_face_state(ctx=None):
    """
    Safely pull the latest face-monitoring state from the
    running video processor via ctx.video_processor.get_state(),
    with thread-safe fallback to the active synchronized processor state.
    Returns a sane default (no face) if the camera isn't
    running yet, so callers never have to special-case None.
    """

    if ctx is not None and getattr(ctx, "video_processor", None) is not None:
        state = ctx.video_processor.get_state()
        if state and state.get("frames", 0) > 0:
            return state

    if CAMERA_KEY in st.session_state:
        ss_ctx = st.session_state.get(CAMERA_KEY)
        if ss_ctx is not None and getattr(ss_ctx, "video_processor", None) is not None:
            state = ss_ctx.video_processor.get_state()
            if state and state.get("frames", 0) > 0:
                return state

    latest = InterviewVideoProcessor.get_latest_active_state()
    if latest is not None:
        return latest

    return {
        "face_count": 0,
        "face_detected": False,
        "movement": "No face",
        "movement_distance": 0,
        "frames": 0,
    }


def get_live_audio_state(ctx):
    """
    Safely pull the latest mic level state from the running
    audio processor. Returns a sane "silence" default if audio
    isn't running yet.
    """

    if ctx is not None and ctx.audio_processor is not None:

        return ctx.audio_processor.get_state()

    return {
        "current_level": 0.0,
        "peak_level": 0.0,
        "floor_level": 0.0,
        "frames_seen": 0,
    }


def is_single_face(state):
    """Single source of truth for the 'exactly one face' rule."""

    return state is not None and state["face_count"] == 1


def _proctor_badge_html(state, monitoring_enabled, size="normal"):
    """
    Builds the HTML for the live proctoring badge/pill used both
    in the exam session bar and next to the monitor panel. Same
    underlying face-count logic as render_face_status(), just a
    compact visual form.
    """

    if not monitoring_enabled:

        return (
            '<span class="proctor-badge off">'
            '<span class="led"></span>MONITORING OFF</span>'
        )

    face_count = state["face_count"]

    if face_count == 1:

        css_class, label = "ok", "FACE DETECTED"

    elif face_count == 0:

        css_class, label = "bad", "FACE NOT DETECTED"

    else:

        css_class, label = "warn", "MULTIPLE FACES"

    return (
        f'<span class="proctor-badge {css_class}">'
        f'<span class="led"></span>{label}</span>'
    )


def render_face_status(state):
    """
    Renders one of the three required face-state messages based
    on the latest processor snapshot, in the exam-alert visual
    style. Returns True only when exactly one face is present
    (used to enable/disable the Submit & Skip buttons, and the
    camera-check "Next" button).
    """

    face_count = state["face_count"]

    if face_count == 1:

        css_class = "ok"

        title = "🟢 Face detected"

        body = "Your face is visible. You may continue."

        face_ok = True

    elif face_count == 0:

        css_class = "bad"

        title = "🔴 Face not detected"

        body = "Please position yourself in front of the camera."

        face_ok = False

    else:

        css_class = "warn"

        title = "🟠 Multiple faces detected"

        body = "Only one person should be visible in the camera."

        face_ok = False

    bg = {"ok": "var(--ok-bg)", "bad": "var(--bad-bg)", "warn": "var(--warn-bg)"}[css_class]

    border = {"ok": "#1F5C36", "bad": "#6B2226", "warn": "#6B4A11"}[css_class]

    text = {"ok": "#86EFAC", "bad": "#FCA5A5", "warn": "#FCD34D"}[css_class]

    st.markdown(
        f'<div style="background:{bg};border:1px solid {border};'
        f'border-radius:8px;padding:12px 16px;margin-top:10px;">'
        f'<div style="color:{text};font-weight:700;font-size:14px;">{title}</div>'
        f'<div style="color:{text};font-size:12.5px;opacity:0.9;margin-top:2px;">{body}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    return face_ok


def _sized_container(key):
    """
    Wraps content in a real st.container(key=...). Unlike an
    unclosed st.markdown('<div>...') (which does NOT actually
    become a DOM parent of later Streamlit elements - each
    Streamlit element is its own sibling block), a keyed
    container genuinely nests everything drawn inside the
    `with` block under one wrapper element carrying the CSS
    class `st-key-<key>`. That's what lets the CSS above
    actually shrink the camera video instead of just resizing
    text around it.

    Falls back to a plain, unsized container on Streamlit
    versions older than the one that added the `key` argument,
    so the app still runs (just without the size cap) instead
    of crashing.
    """

    try:

        return st.container(key=key)

    except TypeError:

        return st.container()


def _fragment(run_every=None):
    """
    Small compatibility shim around st.fragment. Newer Streamlit
    versions support st.fragment(run_every=...), which is what
    lets camera/mic/status blocks auto-refresh on a timer so the
    UI keeps picking up the latest processor state even when the
    user isn't clicking anything. If st.fragment isn't available
    in the installed Streamlit version, we fall back to a no-op
    decorator so the app still runs (state will still update on
    every normal rerun, just not on a timer).
    """

    if callable(run_every):
        func = run_every
        if hasattr(st, "fragment"):
            return st.fragment(func)
        return func

    if hasattr(st, "fragment"):

        try:

            return st.fragment(run_every=run_every)

        except TypeError:

            return st.fragment()

    def _noop_decorator(func):

        return func

    return _noop_decorator


# ============================================================
# SMALL DISPLAY HELPERS
# ============================================================

def _safe_get(mapping, keys, default):
    """Best-effort lookup across possible field names for the
    logged-in user record, without assuming an exact schema."""

    for key in keys:

        try:

            value = mapping[key]

            if value:

                return value

        except (KeyError, TypeError):

            continue

    return default


def render_masthead():

    st.markdown(
        '<div class="exam-masthead">'
        '<div>'
        '<div class="brand">AI CAREER TWIN <span class="mark">/</span> FORMAL ASSESSMENT</div>'
        '<div class="tagline">Proctored Mock Interview &nbsp;·&nbsp; Role-Based Evaluation</div>'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )


def render_section_roadmap(stages, current_stage):

    try:

        current_index = stages.index(current_stage)

    except ValueError:

        current_index = 0

    cells = []

    for index, stage_name in enumerate(stages):

        if index < current_index:

            state_class = "done"

        elif index == current_index:

            state_class = "current"

        else:

            state_class = "upcoming"

        cells.append(
            f'<div class="step {state_class}">'
            f'<div class="num">{index + 1}</div>'
            f'<div class="label">{stage_name}</div>'
            f'</div>'
        )

    st.markdown(
        f'<div class="exam-roadmap">{"".join(cells)}</div>',
        unsafe_allow_html=True,
    )


def render_onboarding_roadmap(current_key):
    """
    3-step progress strip shown across the pre-flight onboarding flow:
    Overview -> Pre-Flight Checks -> Live Examination.
    """

    stage_labels = {
        "landing": "Assessment Overview",
        "preflight": "Pre-Flight Checks",
        "interview": "Live Examination",
    }

    stages = list(stage_labels.values())

    current_label = stage_labels.get(
        current_key, stages[0]
    )

    render_section_roadmap(stages, current_label)


# ============================================================
# STUDENT ROLE
# ============================================================

profile = get_student_profile(
    user["id"]
)

if profile and profile.get(
    "predicted_role"
):

    default_role = profile[
        "predicted_role"
    ]

else:

    default_role = "Software Engineer"

candidate_name = _safe_get(
    user,
    ["name", "full_name", "username", "email"],
    "Candidate",
)


# ============================================================
# MASTHEAD
# ============================================================

render_masthead()


# ============================================================
# ============================================================
# FULLSCREEN HTML/JS COMPONENT
# ============================================================

def render_fullscreen_box():
    """
    Renders browser fullscreen request via the HTML/JS Fullscreen API.
    Must be triggered by an explicit user button click due to browser
    security requirements for the requestFullscreen API.
    """
    fs_html = """
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="utf-8">
    <style>
      body {
        margin: 0;
        padding: 0;
        background: transparent;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      }
      .fs-panel {
        background: #171F30;
        border: 1px solid #2A3348;
        border-radius: 10px;
        padding: 14px 18px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 12px;
      }
      .fs-text-wrap {
        text-align: left;
      }
      .fs-head {
        font-size: 13.5px;
        font-weight: 600;
        color: #F8FAFC;
        margin-bottom: 2px;
      }
      .fs-sub {
        font-size: 12px;
        color: #94A3B8;
      }
      .fs-trigger-btn {
        background: #375DFB;
        color: #FFFFFF;
        border: none;
        border-radius: 6px;
        padding: 9px 18px;
        font-size: 13px;
        font-weight: 600;
        cursor: pointer;
        white-space: nowrap;
        transition: all 0.2s ease;
        box-shadow: 0 2px 8px rgba(55, 93, 251, 0.35);
      }
      .fs-trigger-btn:hover {
        background: #2347E2;
      }
    </style>
    </head>
    <body>
      <div class="fs-panel">
        <div class="fs-text-wrap">
          <div class="fs-head">⛶ Browser Fullscreen Mode</div>
          <div id="fs-dyn-msg" class="fs-sub">Click button to request browser fullscreen.</div>
        </div>
        <button type="button" class="fs-trigger-btn" id="fs-btn-act" onclick="triggerFullscreen()">
          ⛶ Request Fullscreen
        </button>
      </div>
      <script>
        function checkFsState() {
          var pDoc = window.parent ? window.parent.document : document;
          return !!(pDoc.fullscreenElement || pDoc.webkitFullscreenElement || pDoc.mozFullScreenElement || pDoc.msFullscreenElement);
        }
        function triggerFullscreen() {
          try {
            var pDoc = window.parent ? window.parent.document : document;
            var elem = pDoc.documentElement;
            if (!checkFsState()) {
              if (elem.requestFullscreen) {
                elem.requestFullscreen().then(function() {
                  var m = document.getElementById('fs-dyn-msg');
                  if (m) m.innerHTML = '<span style="color:#86EFAC;font-weight:600;">✓ Fullscreen active! Click Confirm below.</span>';
                }).catch(function(err) {
                  var m = document.getElementById('fs-dyn-msg');
                  if (m) m.innerHTML = '<span style="color:#FCD34D;">Browser security requires pressing <b>F11</b>.</span>';
                });
              } else if (elem.webkitRequestFullscreen) {
                elem.webkitRequestFullscreen();
                var m = document.getElementById('fs-dyn-msg');
                if (m) m.innerHTML = '<span style="color:#86EFAC;font-weight:600;">✓ Fullscreen active!</span>';
              } else if (elem.msRequestFullscreen) {
                elem.msRequestFullscreen();
                var m = document.getElementById('fs-dyn-msg');
                if (m) m.innerHTML = '<span style="color:#86EFAC;font-weight:600;">✓ Fullscreen active!</span>';
              }
            } else {
              if (pDoc.exitFullscreen) {
                pDoc.exitFullscreen();
              }
            }
          } catch(e) {
            var m = document.getElementById('fs-dyn-msg');
            if (m) m.innerHTML = '<span style="color:#FCD34D;">Please press <b>F11</b> on your keyboard to enter fullscreen.</span>';
          }
        }
      </script>
    </body>
    </html>
    """
    components.html(fs_html, height=75)


# ============================================================
# STAGE 1: MOCK INTERVIEW LANDING
# ============================================================

if not st.session_state.interview_started and st.session_state.interview_flow_stage == "landing":

    render_onboarding_roadmap("landing")

    st.markdown("####")

    setup_col1, setup_col2 = st.columns([1.3, 1])

    with setup_col1:

        st.markdown(
            '<div class="instruction-panel">'
            '<div class="role-label" style="font-family:var(--font-mono);'
            'font-size:11px;letter-spacing:1.2px;text-transform:uppercase;'
            'color:var(--muted);margin-bottom:14px;">Candidate Instructions</div>'
            '<div class="item"><span class="tick">✓</span> Answer each question clearly and completely.</div>'
            '<div class="item"><span class="tick">✓</span> Explain your reasoning for technical questions.</div>'
            '<div class="item"><span class="tick">✓</span> Use concrete examples from your own projects.</div>'
            '<div class="item"><span class="tick">✓</span> Keep your face visible to the camera at all times.</div>'
            '<div class="item"><span class="tick">✓</span> Only one person may appear in the camera frame.</div>'
            '<div class="item"><span class="tick">✓</span> The proctoring system checks face presence and movement continuously.</div>'
            '</div>',
            unsafe_allow_html=True,
        )

        st.markdown("####")

        st.markdown(
            '<div class="field-label" style="font-family:var(--font-mono);'
            'font-size:11px;letter-spacing:1.2px;text-transform:uppercase;'
            'color:var(--muted);margin-bottom:10px;">Exam Structure</div>',
            unsafe_allow_html=True,
        )

        render_section_roadmap(
            [
                "Introduction",
                "Resume",
                "Technical",
                "Problem Solving",
                "Behavioral",
                "HR",
                "Closing",
            ],
            "Introduction",
        )

    with setup_col2:

        st.markdown(
            '<div class="candidate-card">'
            '<div class="role-label">Candidate</div>'
            f'<div class="field-value" style="font-size:16px;margin-bottom:16px;">{candidate_name}</div>'
            '<div class="role-label">Assessed Role</div>'
            f'<div class="role-value">{default_role}</div>'
            '</div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div style="background:var(--panel-2);border:1px solid var(--hairline);'
            'border-radius:10px;padding:16px 18px;margin-top:16px;">'
            '<div style="font-family:var(--font-mono);font-size:11px;letter-spacing:1.2px;'
            'text-transform:uppercase;color:var(--gold);margin-bottom:6px;">🔒 Proctoring Pre-Flight Required</div>'
            '<div style="font-size:13px;color:var(--muted);line-height:1.5;">'
            'This formal assessment enforces automated real-time proctoring. '
            'Before entering the test, you must pass a 3-point pre-flight check:'
            '<ul style="margin:8px 0 0 18px;padding:0;">'
            '<li>📷 <b>Camera Test</b>: Webcam access &amp; face verification</li>'
            '<li>🎙️ <b>Mic &amp; Voice Test</b>: Audio output &amp; microphone detection</li>'
            '<li>⛶ <b>Fullscreen Request</b>: Browser environment lock</li>'
            '</ul>'
            '</div>'
            '</div>',
            unsafe_allow_html=True,
        )

        st.markdown("####")

        if st.button(
            "🚀 Start Proctored Assessment",
            type="primary",
            use_container_width=True,
            key="start_proctored_assessment_btn",
        ):
            st.session_state.interview_flow_stage = "preflight"
            st.session_state.preflight_step = "camera"
            st.rerun()

    st.stop()


# ============================================================
# STAGE 2: PRE-FLIGHT CHECK SCREEN
# ============================================================

elif not st.session_state.interview_started and st.session_state.interview_flow_stage == "preflight":

    render_onboarding_roadmap("preflight")

    st.markdown("####")

    # Status Board for all 3 checks
    stat_c1, stat_c2, stat_c3 = st.columns(3)

    with stat_c1:
        cam_ok = st.session_state.camera_check_passed
        badge_cls = "ok" if cam_ok else "pending"
        badge_lbl = "VERIFIED" if cam_ok else "PENDING"
        card_cls = "ready" if cam_ok else "pending"
        st.markdown(
            f'<div class="preflight-status-card {card_cls}">'
            '<div class="preflight-card-head">'
            '<div class="preflight-card-title">📷 1. Camera Check</div>'
            f'<span class="status-pill {badge_cls}">{badge_lbl}</span>'
            '</div>'
            '<div class="preflight-card-desc">Hardware probe &amp; face framing</div>'
            '</div>',
            unsafe_allow_html=True,
        )

    with stat_c2:
        mic_ok = st.session_state.mic_check_passed
        badge_cls = "ok" if mic_ok else "pending"
        badge_lbl = "VERIFIED" if mic_ok else "PENDING"
        card_cls = "ready" if mic_ok else "pending"
        st.markdown(
            f'<div class="preflight-status-card {card_cls}">'
            '<div class="preflight-card-head">'
            '<div class="preflight-card-title">🎙️ 2. Mic &amp; Voice</div>'
            f'<span class="status-pill {badge_cls}">{badge_lbl}</span>'
            '</div>'
            '<div class="preflight-card-desc">Voice synthesizer &amp; mic stream</div>'
            '</div>',
            unsafe_allow_html=True,
        )

    with stat_c3:
        fs_ok = st.session_state.fullscreen_passed
        badge_cls = "ok" if fs_ok else "bad"
        badge_lbl = "FULLSCREEN READY" if fs_ok else "FULLSCREEN REQUIRED"
        card_cls = "ready" if fs_ok else "pending"
        st.markdown(
            f'<div class="preflight-status-card {card_cls}">'
            '<div class="preflight-card-head">'
            '<div class="preflight-card-title">⛶ 3. Fullscreen</div>'
            f'<span class="status-pill {badge_cls}">{badge_lbl}</span>'
            '</div>'
            '<div class="preflight-card-desc">Browser lockdown &amp; anti-cheat</div>'
            '</div>',
            unsafe_allow_html=True,
        )

    st.markdown("####")

    # Step selector buttons
    step_c1, step_c2, step_c3 = st.columns(3)
    with step_c1:
        cam_mark = "✅" if st.session_state.camera_check_passed else "1."
        is_cam = st.session_state.preflight_step == "camera"
        if st.button(
            f"{cam_mark} Camera Test",
            key="step_btn_cam",
            type="primary" if is_cam else "secondary",
            use_container_width=True,
        ):
            st.session_state.preflight_step = "camera"
            st.rerun()

    with step_c2:
        mic_mark = "✅" if st.session_state.mic_check_passed else "2."
        is_mic = st.session_state.preflight_step == "mic"
        if st.button(
            f"{mic_mark} Mic & Voice",
            key="step_btn_mic",
            type="primary" if is_mic else "secondary",
            use_container_width=True,
        ):
            st.session_state.preflight_step = "mic"
            st.rerun()

    with step_c3:
        fs_mark = "✅" if st.session_state.fullscreen_passed else "3."
        is_fs = st.session_state.preflight_step == "fullscreen"
        if st.button(
            f"{fs_mark} Fullscreen",
            key="step_btn_fs",
            type="primary" if is_fs else "secondary",
            use_container_width=True,
        ):
            st.session_state.preflight_step = "fullscreen"
            st.rerun()

    st.markdown("####")

    # --------------------------------------------------------
    # STEP 1: CAMERA PERMISSION & TEST (camera_monitor.py)
    # --------------------------------------------------------
    if st.session_state.preflight_step == "camera":

        st.markdown(
            '<div class="gate-card" style="text-align:left;">'
            '<div class="gate-eyebrow" style="text-align:center;">Check 1 of 3</div>'
            '<div class="gate-title" style="text-align:center;">Camera Permission &amp; Face Alignment</div>'
            '<div class="gate-body" style="text-align:center;margin-bottom:8px;">'
            'Position yourself so your full face is clearly visible. '
            'We verify hardware availability via camera_monitor.py and hold steady for 2 seconds.'
            '</div>'
            '</div>',
            unsafe_allow_html=True,
        )

        st.markdown("####")

        hw_box_c1, hw_box_c2 = st.columns([1.3, 1])
        with hw_box_c1:
            st.markdown(
                '<div style="font-size:13.5px;color:var(--ivory);font-weight:600;padding-top:6px;">'
                '📷 Hardware Camera Probe (camera_monitor.py)'
                '</div>',
                unsafe_allow_html=True,
            )
            st.caption("Validates local video capture device initialization.")
        with hw_box_c2:
            if st.button("🔍 Test Camera Hardware", key="btn_test_cam_hw", use_container_width=True):
                cam = CameraMonitor()
                if cam.start():
                    frame = cam.read_frame()
                    cam.stop()
                    if frame is not None:
                        st.session_state.hardware_camera_ok = True
                        st.session_state.camera_check_passed = True
                        st.success("✅ Camera hardware initialized successfully!")
                    else:
                        st.session_state.hardware_camera_ok = False
                        st.error("Camera opened but could not read frame.")
                else:
                    st.session_state.hardware_camera_ok = False
                    st.error("Could not open camera device. Please ensure webcam is connected.")

        st.markdown("####")

        @_fragment()
        def render_camera_check_block():

            with _sized_container("camera-check-box"):

                st.markdown(
                    '<div class="monitor-titlebar">'
                    '<span class="monitor-title">Camera Preview</span>'
                    '</div>',
                    unsafe_allow_html=True,
                )

                ctx = render_camera(
                    key=CAMERA_KEY,
                    audio_enabled=True,
                )

            return ctx

        cam_ctx = render_camera_check_block()

        @_fragment(run_every=1)
        def render_camera_status_block(ctx=cam_ctx):

            ctx_active = ctx or st.session_state.get(CAMERA_KEY)
            live_state = get_live_face_state(ctx_active)

            face_ok = render_face_status(live_state)

            now = time.time()

            if face_ok:

                if st.session_state.camera_stable_since is None:
                    st.session_state.camera_stable_since = now

                stable_for = (
                    now - st.session_state.camera_stable_since
                )

                required_seconds = 2.0

                remaining = max(
                    0.0, required_seconds - stable_for
                )

                if stable_for >= required_seconds:
                    st.session_state.camera_check_passed = True
                    st.success(
                        "✅ Face verified and steady. Camera check passed!"
                    )
                else:
                    st.info(
                        f"Hold still… verifying "
                        f"({remaining:.1f}s remaining)"
                    )

            else:
                st.session_state.camera_stable_since = None

            c_btn1, c_btn2 = st.columns(2)
            with c_btn1:
                if not st.session_state.camera_check_passed:
                    if st.button("✅ Confirm Camera Ready", key="cam_manual_confirm", use_container_width=True):
                        st.session_state.camera_check_passed = True
                        st.session_state.preflight_step = "mic"
                        st.rerun()
            with c_btn2:
                if st.button(
                    "Next: Mic & Voice Test ➜",
                    type="primary",
                    use_container_width=True,
                    disabled=not st.session_state.camera_check_passed,
                    key="cam_next_btn",
                ):
                    st.session_state.preflight_step = "mic"
                    st.rerun()

        render_camera_status_block()

    # --------------------------------------------------------
    # STEP 2: MICROPHONE & VOICE TEST (speech_handler.py)
    # --------------------------------------------------------
    elif st.session_state.preflight_step == "mic":

        if st.session_state.mic_prompt_phrase is None:
            phrases = [
                "Hello, I am ready for this proctored interview.",
                "Testing my microphone and voice before the assessment.",
                "Please confirm that my voice is being heard clearly.",
            ]
            st.session_state.mic_prompt_phrase = random.choice(phrases)

        st.markdown(
            '<div class="gate-card" style="text-align:left;">'
            '<div class="gate-eyebrow" style="text-align:center;">Check 2 of 3</div>'
            '<div class="gate-title" style="text-align:center;">Microphone &amp; Voice Test</div>'
            '<div class="gate-body" style="text-align:center;margin-bottom:8px;">'
            'We confirm your voice output functions via speech_handler.py and your '
            'microphone detects audible speech over ambient room noise.'
            '</div>'
            '</div>',
            unsafe_allow_html=True,
        )

        st.markdown("####")

        # Proctor audio output test using speech_handler.py
        voice_box_c1, voice_box_c2 = st.columns([1.3, 1])
        with voice_box_c1:
            st.markdown(
                '<div style="font-size:13.5px;color:var(--ivory);font-weight:600;padding-top:6px;">'
                '🔊 Proctor Audio Synthesizer (speech_handler.py)'
                '</div>',
                unsafe_allow_html=True,
            )
            st.caption("Plays an automated proctor spoken audio prompt through system sound.")
        with voice_box_c2:
            if st.button("🔊 Test Voice Output", key="btn_test_voice_output", use_container_width=True):
                with st.spinner("Playing proctor audio prompt..."):
                    ok = speak("Pre-flight audio check. Please verify you can hear this proctor prompt clearly.")
                if ok:
                    st.session_state.voice_tested = True
                    st.success("✅ Proctor voice test completed successfully via speech_handler.py!")
                else:
                    st.warning("Voice output test completed.")

        st.markdown("####")

        st.markdown(
            '<div class="mic-phrase-box">'
            '<div class="phrase-label">Read this out loud into your microphone</div>'
            f'<div class="phrase-text">"{st.session_state.mic_prompt_phrase}"</div>'
            '</div>',
            unsafe_allow_html=True,
        )

        @_fragment(run_every=1)
        def render_mic_check_block():

            with _sized_container("mic-check-box"):

                st.markdown(
                    '<div class="monitor-titlebar">'
                    '<span class="monitor-title">Camera &amp; Microphone Preview</span>'
                    '</div>',
                    unsafe_allow_html=True,
                )

                ctx = render_camera(
                    key=CAMERA_KEY,
                    audio_enabled=True,
                )

                audio_state = get_live_audio_state(ctx)

                current_level = audio_state["current_level"]
                peak_level = audio_state["peak_level"]
                floor_level = audio_state["floor_level"]

                voice_detected = peak_level > 0.06
                ambient_ok = floor_level < 0.05

                if voice_detected:
                    st.session_state.mic_voice_detected = True

                st.session_state.mic_ambient_ok = ambient_ok

                meter_pct = max(0, min(100, current_level / 0.3 * 100))

                if current_level > 0.15:
                    meter_color = "#DC2626"
                elif current_level > 0.04:
                    meter_color = "#16A34A"
                else:
                    meter_color = "#375DFB"

                st.markdown(
                    '<div class="field-label" style="margin-top:10px;">'
                    'Live mic level</div>'
                    '<div class="level-meter-wrap">'
                    f'<div class="level-meter-fill" style="width:{meter_pct:.0f}%;'
                    f'background:{meter_color};"></div>'
                    '</div>',
                    unsafe_allow_html=True,
                )

            status_col1, status_col2 = st.columns(2)

            with status_col1:
                if st.session_state.mic_voice_detected:
                    st.success("🎙️ Voice detected")
                else:
                    st.warning("🎙️ Waiting to hear you speak…")

            with status_col2:
                if ambient_ok:
                    st.success("🔇 Background noise OK")
                else:
                    st.warning("🔊 It's noisy — find a quieter spot")

            mic_ready = (
                st.session_state.mic_voice_detected
                and st.session_state.mic_ambient_ok
            )
            if mic_ready:
                st.session_state.mic_check_passed = True

            retry_col1, retry_col2, retry_col3 = st.columns(3)

            with retry_col1:
                if st.button("🔄 Re-test", use_container_width=True, key="mic_retest"):
                    st.session_state.mic_voice_detected = False
                    st.session_state.mic_check_passed = False
                    if ctx is not None and ctx.audio_processor is not None:
                        ctx.audio_processor.reset()
                    st.rerun()

            with retry_col2:
                if not st.session_state.mic_check_passed:
                    if st.button("✅ Confirm Mic", use_container_width=True, key="btn_confirm_mic_step"):
                        st.session_state.mic_check_passed = True
                        st.session_state.preflight_step = "fullscreen"
                        st.rerun()

            with retry_col3:
                if st.button(
                    "Next: Fullscreen ➜",
                    type="primary",
                    use_container_width=True,
                    disabled=not st.session_state.mic_check_passed,
                    key="mic_check_next_to_fs",
                ):
                    st.session_state.preflight_step = "fullscreen"
                    st.rerun()

        render_mic_check_block()

    # --------------------------------------------------------
    # STEP 3: FULLSCREEN REQUEST (Browser Fullscreen API)
    # --------------------------------------------------------
    elif st.session_state.preflight_step == "fullscreen":

        st.markdown(
            '<div class="gate-card" style="text-align:left;">'
            '<div class="gate-eyebrow" style="text-align:center;">Check 3 of 3</div>'
            '<div class="gate-title" style="text-align:center;">Browser Fullscreen Lockdown</div>'
            '<div class="gate-body" style="text-align:center;margin-bottom:8px;">'
            'Online proctoring requires full-screen mode to ensure an uninterrupted, '
            'secure assessment environment without tab or window switching.'
            '</div>'
            '</div>',
            unsafe_allow_html=True,
        )

        st.markdown("####")

        render_fullscreen_box()

        st.markdown("####")

        fs_st_col1, fs_st_col2 = st.columns([1.2, 1])

        with fs_st_col1:
            if st.session_state.fullscreen_passed:
                st.success("⛶ Status: Fullscreen Ready")
            else:
                st.warning("⚠️ Status: Fullscreen Required")

        with fs_st_col2:
            if not st.session_state.fullscreen_passed:
                if st.button("✅ Confirm Fullscreen Ready", key="btn_confirm_fs_pass", use_container_width=True):
                    st.session_state.fullscreen_passed = True
                    st.rerun()
            else:
                if st.button("🔄 Reset Fullscreen", key="btn_reset_fs_pass", use_container_width=True):
                    st.session_state.fullscreen_passed = False
                    st.rerun()

        st.info(
            "💡 **If Fullscreen cannot be enabled via the button:**\n\n"
            "Certain browsers restrict iframe fullscreen calls due to security policies. "
            "Simply press **F11** (Windows/Linux) or **Fn + F11** / **Control + Command + F** (macOS) "
            "on your keyboard to enter full screen, then click **'Confirm Fullscreen Ready'**."
        )

    # --------------------------------------------------------
    # BOTTOM ACTION BAR (Start Interview Gate)
    # --------------------------------------------------------
    st.divider()

    all_checks_passed = (
        st.session_state.camera_check_passed
        and st.session_state.mic_check_passed
        and st.session_state.fullscreen_passed
    )

    if not all_checks_passed:
        missing = []
        if not st.session_state.camera_check_passed:
            missing.append("Camera verification")
        if not st.session_state.mic_check_passed:
            missing.append("Microphone & voice test")
        if not st.session_state.fullscreen_passed:
            missing.append("Fullscreen mode")
        st.warning(f"⚠️ Pre-flight incomplete. Please complete: {', '.join(missing)} before starting the interview.")
    else:
        st.success("🎯 All pre-flight checks verified! You are ready to enter the proctored interview.")

    act_col1, act_col2 = st.columns([1, 1.3])

    with act_col1:
        if st.button("← Back to Assessment Overview", key="btn_preflight_to_landing", use_container_width=True):
            st.session_state.interview_flow_stage = "landing"
            st.rerun()

    with act_col2:
        if st.button(
            "🚀 Start Interview",
            type="primary",
            disabled=not all_checks_passed,
            use_container_width=True,
            key="btn_preflight_start_exam",
        ):
            engine = InterviewEngine(
                role=default_role,
                resume_text=""
            )
            engine.start_interview()
            st.session_state.interview_engine = engine
            st.session_state.interview_started = True
            st.session_state.session_code = f"AX-{random.randint(1000, 9999)}"
            st.session_state.interview_flow_stage = "interview"
            st.rerun()

    st.stop()


# ============================================================
# ACTIVE INTERVIEW
# ============================================================

else:

    engine = (
        st.session_state.interview_engine
    )

    if engine is None:

        st.session_state.interview_started = (
            False
        )

        st.rerun()


    # ========================================================
    # COMPLETED
    # ========================================================

    if engine.is_complete():

        results = engine.get_results()
        all_records = results.get("answers", [])
        total_questions = results.get("total_questions", len(all_records))
        overall_score = results.get("overall_score", 0)
        duration_min = results.get("duration_seconds", 0) // 60

        # Evaluate answered questions with interview_evaluator
        answered_records = []
        for a in all_records:
            is_ans = not a.get("skipped", False) and bool(a.get("answer", "").strip())
            if is_ans:
                ev = evaluate_answer(a.get("question", ""), a.get("answer", ""))
                a["evaluation"] = ev
                answered_records.append(a)
            else:
                a["evaluation"] = None

        answered_count = len(answered_records)
        skipped_count = max(0, total_questions - answered_count)

        st.markdown(
            '<div class="result-card">'
            '<div class="seal">✓ Assessment Complete</div>'
            '<div class="headline">Formal Interview Results &amp; Assessment Report</div>'
            '</div>',
            unsafe_allow_html=True,
        )

        # ----------------------------------------------------
        # 1. ASSESSMENT SUMMARY
        # ----------------------------------------------------
        summary_html = f'''
        <div class="report-summary-grid">
            <div class="report-metric-card">
                <div class="report-metric-label">Overall Score</div>
                <div class="report-metric-val" style="color:#86EFAC;">{overall_score}%</div>
            </div>
            <div class="report-metric-card">
                <div class="report-metric-label">Total Questions</div>
                <div class="report-metric-val">{total_questions}</div>
            </div>
            <div class="report-metric-card">
                <div class="report-metric-label">Answered Questions</div>
                <div class="report-metric-val" style="color:#93C5FD;">{answered_count}</div>
            </div>
            <div class="report-metric-card">
                <div class="report-metric-label">Skipped Questions</div>
                <div class="report-metric-val" style="color:#FCD34D;">{skipped_count}</div>
            </div>
        </div>
        '''
        st.markdown(summary_html, unsafe_allow_html=True)
        st.caption(f"⏱️ Assessment Duration: {duration_min} min &nbsp;·&nbsp; Session: {st.session_state.session_code or '—'} &nbsp;·&nbsp; Role: {engine.role}")

        st.markdown("####")

        # ----------------------------------------------------
        # 2. OVERALL FEEDBACK (Based strictly on evaluator data)
        # ----------------------------------------------------
        if answered_count > 0:
            avg_tech = sum(a["evaluation"]["technical"] for a in answered_records) / answered_count
            avg_comm = sum(a["evaluation"]["communication"] for a in answered_records) / answered_count
            avg_rel = sum(a["evaluation"]["relevance"] for a in answered_records) / answered_count
            avg_eval = sum(a["evaluation"]["overall"] for a in answered_records) / answered_count

            if avg_eval >= 80:
                summary_narrative = (
                    "Candidate demonstrated strong interview performance on answered questions, "
                    "providing clear, articulate, and highly relevant responses across assessed topics."
                )
            elif avg_eval >= 60:
                summary_narrative = (
                    "Candidate demonstrated satisfactory performance on answered questions with solid foundational concepts, "
                    "though responses would benefit from more specific examples and technical depth."
                )
            else:
                summary_narrative = (
                    "Candidate responses on answered questions require improvement. "
                    "Answers need greater clarity, more structured delivery, and stronger topic coverage."
                )

            completion_note = f"Candidate completed {answered_count} of {total_questions} questions ({skipped_count} skipped)."
        else:
            avg_tech = avg_comm = avg_rel = avg_eval = 0
            summary_narrative = "No questions were answered during this assessment session (all questions were skipped)."
            completion_note = f"0 of {total_questions} questions were answered; {skipped_count} questions were skipped."

        overall_fb_html = f'''
        <div class="report-section-card">
            <div class="report-section-hdr">🎯 Overall Feedback</div>
            <div class="report-feedback-box">
                <div style="font-weight:600;margin-bottom:6px;">{summary_narrative}</div>
                <div style="color:var(--muted);font-size:13.5px;">{completion_note}</div>
            </div>
        </div>
        '''
        st.markdown(overall_fb_html, unsafe_allow_html=True)

        # ----------------------------------------------------
        # 3. STRENGTHS & AREAS FOR IMPROVEMENT
        # ----------------------------------------------------
        strengths = []
        improvements = []

        if answered_count > 0:
            if avg_comm >= 75:
                strengths.append(f"Communication & Depth: Provided thorough explanations with sustained elaboration (Average Communication Score: {avg_comm:.0f}/100).")
            if avg_rel >= 60:
                strengths.append(f"Topic Relevance: Responses directly incorporated core question keywords and subject matter (Average Relevance Score: {avg_rel:.0f}/100).")
            if avg_tech >= 70:
                strengths.append(f"Technical Competency: Maintained balanced technical reasoning across attempted questions (Average Technical Score: {avg_tech:.0f}/100).")

            for a in answered_records:
                if a["evaluation"]["overall"] >= 80:
                    strengths.append(f"Q{a['question_number']} ({a['stage']}): {a['evaluation']['feedback']} (Score: {a['evaluation']['overall']}/100)")

            if not strengths:
                strengths.append(f"Candidate attempted {answered_count} question(s). No specific dimensions exceeded the 60/100 strength threshold under current evaluator criteria.")

            if skipped_count > 0:
                improvements.append(f"Assessment Completion: {skipped_count} of {total_questions} questions were skipped without submission. Attempting all questions ensures a complete evaluation.")
            if avg_comm < 65:
                improvements.append("Answer Elaboration: Responses were brief. Expand explanations with comprehensive details and background.")
            if avg_rel < 60:
                improvements.append("Keyword & Topic Alignment: Focus on directly addressing the specific technical terminology prompted in each question.")

            low_scores = [a for a in answered_records if a["evaluation"]["overall"] < 60]
            if low_scores:
                improvements.append(f"Clarity & Structure: {len(low_scores)} response(s) scored below 60/100 and need more structured delivery.")

            needs_examples = any("more specific examples" in a["evaluation"]["feedback"].lower() for a in answered_records)
            if needs_examples:
                improvements.append("Specific Examples: Support key points with real-world scenarios, metrics, or concrete project examples.")
        else:
            strengths.append("No answers were submitted to evaluate strengths.")
            improvements.append(f"Assessment Completion: All {total_questions} questions were skipped. Provide substantive answers to receive evaluation scores.")

        col_str, col_imp = st.columns(2)

        with col_str:
            str_items = "".join(f'<div class="report-item-green"><b>✓</b> {s}</div>' for s in strengths)
            st.markdown(
                f'<div class="report-section-card">'
                f'<div class="report-section-hdr">💪 Strengths</div>'
                f'{str_items}'
                f'</div>',
                unsafe_allow_html=True,
            )

        with col_imp:
            imp_items = "".join(f'<div class="report-item-amber"><b>▲</b> {imp}</div>' for imp in improvements)
            st.markdown(
                f'<div class="report-section-card">'
                f'<div class="report-section-hdr">📈 Areas for Improvement</div>'
                f'{imp_items}'
                f'</div>',
                unsafe_allow_html=True,
            )

        st.divider()

        # ----------------------------------------------------
        # 4. CANDIDATE ANSWER LOG & PER-QUESTION FEEDBACK
        # ----------------------------------------------------
        st.subheader("📝 Candidate Answer Log & Question Feedback")
        st.caption("Detailed review showing evaluator scores and feedback for answered questions, and recorded status for skipped questions.")

        for answer in all_records:
            q_num = answer.get("question_number", 0)
            stage = answer.get("stage", "Technical")
            q_text = answer.get("question", "")
            ans_text = answer.get("answer", "").strip()
            ev = answer.get("evaluation")

            if ev is not None:
                expander_title = f"Q{q_num} · {stage} — Score: {ev['overall']}%"
                with st.expander(expander_title, expanded=False):
                    st.markdown(f"**Question:**\n{q_text}")
                    st.markdown(
                        f"**Candidate Answer:**\n"
                        f"<div class='q-box-answer'>{ans_text}</div>",
                        unsafe_allow_html=True,
                    )
                    st.markdown("####")
                    badge_cls = "feedback-pill-good" if ev["overall"] >= 60 else "feedback-pill-warn"
                    st.markdown(
                        f"<div class='{badge_cls}'>"
                        f"<b>💡 Evaluator Feedback:</b> {ev['feedback']}"
                        f"</div>",
                        unsafe_allow_html=True,
                    )
                    st.markdown(
                        f"<span class='eval-score-tag'>Technical: {ev['technical']}/100</span>"
                        f"<span class='eval-score-tag'>Communication: {ev['communication']}/100</span>"
                        f"<span class='eval-score-tag'>Relevance: {ev['relevance']}/100</span>"
                        f"<span class='eval-score-tag' style='font-weight:700;border-color:#1F5C36;color:#86EFAC;'>Overall: {ev['overall']}/100</span>",
                        unsafe_allow_html=True,
                    )
            else:
                expander_title = f"Q{q_num} · {stage} — ⏭️ Skipped"
                with st.expander(expander_title, expanded=False):
                    st.markdown(f"**Question:**\n{q_text}")
                    st.markdown(
                        "<div class='q-box-skipped'>"
                        "<b>⏭️ Status:</b> Skipped by candidate — No answer provided."
                        "</div>",
                        unsafe_allow_html=True,
                    )

        if st.button(
            "🔄 Start New Interview",
            type="primary",
            use_container_width=True
        ):

            st.session_state.interview_engine = None
            st.session_state.interview_started = False
            st.session_state.session_code = None

            # Reset pre-flight onboarding so a new attempt re-runs
            # the camera, mic/voice, and fullscreen checks from scratch.
            st.session_state.interview_flow_stage = "landing"
            st.session_state.preflight_step = "camera"
            st.session_state.camera_check_passed = False
            st.session_state.mic_check_passed = False
            st.session_state.fullscreen_passed = False
            st.session_state.hardware_camera_ok = None
            st.session_state.voice_tested = False
            st.session_state.camera_stable_since = None
            st.session_state.mic_prompt_phrase = None
            st.session_state.mic_voice_detected = False
            st.session_state.mic_ambient_ok = None

            st.rerun()


    # ========================================================
    # CURRENT QUESTION
    # ========================================================

    else:

        question_data = (
            engine.get_current_question_data()
        )

        progress = (
            engine.get_progress_data()
        )

        current_number = (
            progress["current"]
        )

        total_questions = (
            progress["total"]
        )

        percentage = (
            progress["percentage"]
        )

        stage = progress["stage"]

        stages = [
            "Introduction",
            "Resume",
            "Technical",
            "Problem Solving",
            "Behavioral",
            "HR",
            "Closing"
        ]

        # ====================================================
        # EXAM SESSION BAR
        # ====================================================

        st.markdown(
            '<div class="exam-session-bar">'
            '<div>'
            '<div class="field-label">Candidate</div>'
            f'<div class="field-value">{candidate_name} &nbsp;·&nbsp; {default_role}</div>'
            '</div>'
            '<div>'
            '<div class="field-label">Session</div>'
            f'<div class="field-value mono">{st.session_state.session_code or "—"}</div>'
            '</div>'
            '<div>'
            '<div class="field-label">Progress</div>'
            f'<div class="field-value">Question {current_number} of {total_questions} &nbsp;·&nbsp; {percentage}%</div>'
            '</div>'
            '</div>',
            unsafe_allow_html=True,
        )

        st.progress(
            percentage / 100
        )

        render_section_roadmap(stages, stage)


        # ====================================================
        # QUESTION
        # ====================================================
        # The camera is no longer laid out beside the question
        # in a column - it's now a small, bordered inline box
        # rendered just above the Submit/Skip buttons (see
        # .st-key-pip-cam-box CSS + the block right after this
        # one), so the question column now gets the full width.
        # ====================================================

        def render_active_question_block(
            engine=engine,
            current_number=current_number,
            total_questions=total_questions,
            question_data=question_data,
        ):

            # ================================================
            # QUESTION / EXAM PAPER (full width)
            # ================================================

            if question_data:

                difficulty = (
                    question_data.get(
                        "difficulty",
                        "medium"
                    )
                )

                question_type = (
                    question_data.get(
                        "type",
                        "interview"
                    )
                )

                question_html = (
                    '<div class="exam-paper">'
                    '<div class="eyebrow">'
                    f'<span class="section-tag">{question_type.replace("_", " ").title()}</span>'
                    f'<span class="difficulty-tag">Difficulty · {difficulty.upper()}</span>'
                    '</div>'
                    '<div class="q-number">Question <b>'
                    f'{current_number}</b> of {total_questions}</div>'
                    f'<div class="q-text">{question_data["question"]}</div>'
                    '</div>'
                )

                st.markdown(
                    question_html,
                    unsafe_allow_html=True
                )

            else:

                st.error(
                    "Unable to load question."
                )


            # ================================================
            # ANSWER
            # ================================================

            ans_key = f"answer_{current_number}"
            if ans_key not in st.session_state:
                existing_ans = ""
                for rec in getattr(engine, "answers", []):
                    if rec.get("question_number") == current_number:
                        existing_ans = rec.get("answer", "")
                        break
                st.session_state[ans_key] = existing_ans

            answer = st.text_area(
                "✍️ Your Answer",
                height=220,
                placeholder=(
                    "Type your answer here..."
                ),
                key=ans_key,
            )


            st.caption(
                "💡 Structure your answer clearly "
                "and support it with examples."
            )


            # ================================================
            # PINNED SMALL PROCTORING CAMERA (bottom-left)
            # ================================================

            webrtc_ctx = None

            if st.session_state.camera_monitoring:

                # .st-key-pip-cam-box (CSS above) renders this as
                # a small, bordered inline box just above the
                # answer buttons - and because this is a real
                # st.container(key=...), the width cap genuinely
                # applies to the camera video drawn inside it, not
                # just the surrounding text.
                with _sized_container("pip-cam-box"):

                    st.markdown(
                        '<div class="pip-titlebar">'
                        '<span class="pip-title">Proctoring · Cam 01</span>'
                        '</div>',
                        unsafe_allow_html=True,
                    )

                    webrtc_ctx = render_camera(
                        key=CAMERA_KEY,
                        audio_enabled=True,
                    )

                def render_pip_proctor_badge():
                    active_ctx = webrtc_ctx or st.session_state.get(CAMERA_KEY)
                    live_state = get_live_face_state(active_ctx)
                    badge_html = _proctor_badge_html(
                        live_state,
                        st.session_state.camera_monitoring,
                    )
                    st.markdown(
                        f'<div style="width:220px;margin:4px 0 12px 0;">{badge_html}</div>',
                        unsafe_allow_html=True,
                    )

                render_pip_proctor_badge()

            else:

                st.info(
                    "Camera monitoring is disabled."
                )


            # ================================================
            # BUTTONS
            # ================================================

            col_submit, col_skip = (
                st.columns(
                    [3, 1]
                )
            )


            with col_submit:

                button_text = (
                    "➡️ Submit & Continue"
                    if current_number
                    < total_questions
                    else
                    "🏁 Submit & Finish"
                )

                if st.button(
                    button_text,
                    type="primary",
                    use_container_width=True,
                    key=f"submit_{current_number}",
                ):

                    # Re-validate against the *latest*
                    # processor state here too. This protects
                    # against a face state change that happens
                    # between render and click.
                    if st.session_state.camera_monitoring:

                        fresh_state = get_live_face_state(
                            webrtc_ctx or st.session_state.get(CAMERA_KEY)
                        )

                    else:

                        fresh_state = None

                    user_answer = (answer or st.session_state.get(ans_key, "")).strip()

                    if (
                        st.session_state.camera_monitoring
                        and not is_single_face(
                            fresh_state
                        )
                    ):

                        st.warning(
                            "Face verification failed. "
                            "Please make sure exactly one "
                            "face is visible before "
                            "continuing."
                        )

                    elif not user_answer:

                        st.warning(
                            "Please enter your answer."
                        )

                    else:

                        engine.save_answer(
                            user_answer
                        )

                        engine.next_question()

                        st.rerun()


            with col_skip:

                if st.button(
                    "⏭️ Skip",
                    use_container_width=True,
                    key=f"skip_{current_number}",
                ):

                    # Skip must not bypass the face
                    # requirement either - re-check the
                    # latest processor state here as well.
                    if st.session_state.camera_monitoring:

                        fresh_state = get_live_face_state(
                            webrtc_ctx or st.session_state.get(CAMERA_KEY)
                        )

                    else:

                        fresh_state = None

                    if (
                        st.session_state.camera_monitoring
                        and not is_single_face(
                            fresh_state
                        )
                    ):

                        st.warning(
                            "Face verification failed. "
                            "Please make sure exactly one "
                            "face is visible before "
                            "skipping."
                        )

                    else:

                        engine.skip_question()

                        st.rerun()


        render_active_question_block()