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
import queue
import numpy as np
import cv2
import streamlit as st


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

# New: onboarding stage machine, run once before the exam itself.
# "camera_check" -> "mic_check" -> "ready" (exam unlocked)
if "onboard_stage" not in st.session_state:
    st.session_state.onboard_stage = "camera_check"

if "camera_check_passed" not in st.session_state:
    st.session_state.camera_check_passed = False

if "mic_check_passed" not in st.session_state:
    st.session_state.mic_check_passed = False

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

/* expander (answer log) */
details {
    background: var(--panel) !important;
    border: 1px solid var(--hairline) !important;
    border-radius: 8px !important;
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

    def __init__(self):

        self.face_count = 0
        self.face_detected = False

        self.frames = 0

        self.movement = "Stable"

        self.previous_center = None

        self.movement_distance = 0

        self.running = True

        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades
            + "haarcascade_frontalface_default.xml"
        )

    # --------------------------------------------------------
    # THREAD-SAFE STATE ACCESSOR
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

    def recv(self, frame):

        image = frame.to_ndarray(
            format="bgr24"
        )

        with camera_lock:
            self.frames += 1

        # ----------------------------------------------------
        # Resize for faster processing
        # ----------------------------------------------------

        height, width = image.shape[:2]

        processing_width = 640

        if width > processing_width:

            scale = (
                processing_width / width
            )

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

        # ----------------------------------------------------
        # Grayscale
        # ----------------------------------------------------

        gray = cv2.cvtColor(
            small_image,
            cv2.COLOR_BGR2GRAY
        )

        gray = cv2.equalizeHist(
            gray
        )

        # ----------------------------------------------------
        # Face detection
        # ----------------------------------------------------

        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(50, 50),
        )

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

        # ----------------------------------------------------
        # Scaling coordinates back
        # ----------------------------------------------------

        if width > processing_width:

            inverse_scale = (
                width / processing_width
            )

        else:

            inverse_scale = 1.0

        # ----------------------------------------------------
        # Face processing
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
        # Movement calculation
        # ----------------------------------------------------

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

            self.previous_center = (
                current_center
            )

        else:

            with camera_lock:

                self.movement = "No face"

                self.movement_distance = 0

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

    def recv(self, frame):

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

        return frame


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
    )

    if audio_enabled:

        kwargs["audio_processor_factory"] = (
            InterviewAudioProcessor
        )

    ctx = webrtc_streamer(**kwargs)

    return ctx


def get_live_face_state(ctx):
    """
    Safely pull the latest face-monitoring state from the
    running video processor via ctx.video_processor.get_state().
    Returns a sane default (no face) if the camera isn't
    running yet, so callers never have to special-case None.
    """

    if ctx is not None and ctx.video_processor is not None:

        return ctx.video_processor.get_state()

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

        css_class, label = "ok", "FACE VERIFIED"

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
    Small 4-step progress strip shown above every onboarding
    screen (camera / mic / ready), reusing the same
    visual stepper component as the exam section roadmap.
    """

    stage_labels = {
        "camera_check": "Camera Check",
        "mic_check": "Mic & Noise Check",
        "ready": "Begin Exam",
    }

    stages = list(stage_labels.values())

    keys_in_order = list(stage_labels.keys())

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
# ONBOARDING GATE
# (camera check -> mic/noise check -> ready)
# Runs before the original interview setup / exam screens.
# ============================================================

def render_onboarding_gate():

    stage = st.session_state.onboard_stage

    render_onboarding_roadmap(stage)

    st.markdown('<div class="gate-wrap">', unsafe_allow_html=True)


    # ========================================================
    # STAGE 1 - CAMERA CHECK (first thing the candidate sees)
    # ========================================================

    if stage == "camera_check":

        st.markdown(
            '<div class="gate-card" style="text-align:left;">'
            '<div class="gate-eyebrow" style="text-align:center;">Step 1 of 2</div>'
            '<div class="gate-title" style="text-align:center;">Camera Check</div>'
            '<div class="gate-body" style="text-align:center;margin-bottom:4px;">'
            'Position yourself so your full face is clearly visible. '
            'We need to see exactly one face, held steady, before '
            'you can continue.'
            '</div>'
            '</div>',
            unsafe_allow_html=True,
        )

        st.markdown("####")

        @_fragment(run_every=1)
        def render_camera_check_block():

            # The container itself is centered and capped at a
            # small/medium width via the .st-key-camera-check-box
            # CSS rule, so everything drawn inside it - including
            # the camera video - is genuinely constrained to that
            # size (see _sized_container's docstring for why this
            # works where a raw markdown div did not).
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

                live_state = get_live_face_state(ctx)

                face_ok = render_face_status(live_state)

            # Require the single-face condition to hold for
            # a short continuous window (not just one lucky
            # frame) before unlocking Next, so a quick flash
            # of "1 face" while adjusting position doesn't
            # immediately pass the check.
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
                        "✅ Face verified and steady. "
                        "You can continue."
                    )

                else:

                    st.session_state.camera_check_passed = False

                    st.info(
                        f"Hold still… verifying "
                        f"({remaining:.1f}s remaining)"
                    )

            else:

                st.session_state.camera_stable_since = None

                st.session_state.camera_check_passed = False

            next_col1, next_col2, next_col3 = st.columns(
                [1, 1.2, 1]
            )

            with next_col2:

                if st.button(
                    "Next: Mic & Noise Check ➜",
                    type="primary",
                    use_container_width=True,
                    disabled=not st.session_state.camera_check_passed,
                    key="camera_check_next",
                ):

                    st.session_state.onboard_stage = "mic_check"

                    st.rerun()

        render_camera_check_block()


    # ========================================================
    # STAGE 2 - MIC / NOISE CHECK
    # ========================================================

    elif stage == "mic_check":

        if st.session_state.mic_prompt_phrase is None:

            phrases = [
                "Hello, my name is ready for this interview.",
                "The quick brown fox jumps over the lazy dog.",
                "I am testing my microphone before the interview.",
                "Please confirm that my voice is being heard clearly.",
            ]

            st.session_state.mic_prompt_phrase = random.choice(
                phrases
            )

        st.markdown(
            '<div class="gate-card" style="text-align:left;">'
            '<div class="gate-eyebrow" style="text-align:center;">Step 2 of 2</div>'
            '<div class="gate-title" style="text-align:center;">Microphone &amp; Noise Check</div>'
            '<div class="gate-body" style="text-align:center;margin-bottom:4px;">'
            'We need to confirm your microphone works and your '
            'surroundings are reasonably quiet. Please read the '
            'sentence below out loud, clearly.'
            '</div>'
            '</div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div class="mic-phrase-box">'
            '<div class="phrase-label">Read this out loud</div>'
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

                # Simple heuristic thresholds on the 0-1 RMS
                # scale. These are intentionally conservative
                # (mic hardware / gain varies a lot) - the goal
                # is to catch "mic is muted / not working" and
                # "room is far too loud", not to be a precise
                # audio-engineering measurement.
                voice_detected = peak_level > 0.06

                ambient_ok = floor_level < 0.05

                if voice_detected:

                    st.session_state.mic_voice_detected = True

                st.session_state.mic_ambient_ok = ambient_ok

                # ---- live level meter ----

                meter_pct = min(
                    100, int(current_level * 100 / 0.3 * 100) / 100
                )

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

                    st.warning(
                        "🎙️ Waiting to hear you speak…"
                    )

            with status_col2:

                if ambient_ok:

                    st.success("🔇 Background noise OK")

                else:

                    st.warning(
                        "🔊 It's noisy — find a quieter spot"
                    )

            mic_ready = (
                st.session_state.mic_voice_detected
                and st.session_state.mic_ambient_ok
            )

            retry_col1, retry_col2 = st.columns(2)

            with retry_col1:

                if st.button(
                    "🔄 Re-test",
                    use_container_width=True,
                    key="mic_retest",
                ):

                    st.session_state.mic_voice_detected = False

                    if ctx is not None and ctx.audio_processor is not None:

                        ctx.audio_processor.reset()

                    st.rerun()

            with retry_col2:

                if st.button(
                    "🚀 Start Test",
                    type="primary",
                    use_container_width=True,
                    disabled=not mic_ready,
                    key="mic_check_start",
                ):

                    st.session_state.mic_check_passed = True

                    st.session_state.onboard_stage = "ready"

                    st.rerun()

        render_mic_check_block()

        back_col1, back_col2, back_col3 = st.columns(
            [1, 1.2, 1]
        )

        with back_col2:

            if st.button(
                "← Back",
                use_container_width=True,
                key="mic_check_back",
            ):

                st.session_state.onboard_stage = "camera_check"

                st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)


onboarding_complete = (
    st.session_state.onboard_stage == "ready"
)

if not onboarding_complete:

    render_onboarding_gate()

    st.stop()


# ============================================================
# INTERVIEW SETUP
# (unchanged from here down, except: only reachable once the
# camera check and mic check have both passed)
# ============================================================

if not st.session_state.interview_started:

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

        st.markdown("####")

        st.success(
            "✅ Camera and microphone checks completed."
        )

        camera_enabled = st.checkbox(
            "📷 Enable live proctoring (camera monitoring)",
            value=True
        )

        st.session_state.camera_monitoring = (
            camera_enabled
        )

        if st.button(
            "🚀 Begin Examination",
            type="primary",
            use_container_width=True
        ):

            engine = InterviewEngine(
                role=default_role,
                resume_text=""
            )

            engine.start_interview()

            st.session_state.interview_engine = (
                engine
            )

            st.session_state.interview_started = (
                True
            )

            st.session_state.session_code = (
                f"AX-{random.randint(1000, 9999)}"
            )

            st.rerun()


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

        st.markdown(
            '<div class="result-card">'
            '<div class="seal">✓ Assessment Complete</div>'
            '<div class="headline">Formal Interview Results</div>'
            '</div>',
            unsafe_allow_html=True,
        )

        st.markdown("####")

        st.metric(
            "Overall Score",
            f'{results["overall_score"]}%'
        )

        col1, col2, col3 = st.columns(3)

        with col1:

            st.metric(
                "Questions",
                results["total_questions"]
            )

        with col2:

            st.metric(
                "Answered",
                results["answered_questions"]
            )

        with col3:

            st.metric(
                "Duration",
                f'{results["duration_seconds"] // 60} min'
            )

        st.divider()

        st.subheader(
            "📝 Candidate Answer Log"
        )

        for answer in results[
            "answers"
        ]:

            with st.expander(
                f'Q{answer["question_number"]} · '
                f'{answer["stage"]}'
            ):

                st.write(
                    "**Question:**",
                    answer["question"]
                )

                st.write(
                    "**Answer:**",
                    answer["answer"]
                )

        if st.button(
            "🔄 Start New Interview",
            type="primary",
            use_container_width=True
        ):

            st.session_state.interview_engine = None
            st.session_state.interview_started = False
            st.session_state.session_code = None

            # Reset onboarding too, so a new attempt re-runs the
            # camera / mic checks from scratch.
            st.session_state.onboard_stage = "camera_check"
            st.session_state.camera_check_passed = False
            st.session_state.mic_check_passed = False
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
        # QUESTION (live-refreshing fragment)
        # ====================================================
        # The camera is no longer laid out beside the question
        # in a column - it's now a small, bordered inline box
        # rendered just above the Submit/Skip buttons (see
        # .st-key-pip-cam-box CSS + the block right after this
        # one), so the question column now gets the full width.
        # ====================================================

        @_fragment(run_every=1)
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

            answer = st.text_area(
                "✍️ Your Answer",
                height=220,
                placeholder=(
                    "Type your answer here..."
                ),
                key=f"answer_{current_number}"
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

                    live_state = get_live_face_state(
                        webrtc_ctx
                    )

                    badge_html = _proctor_badge_html(
                        live_state,
                        st.session_state.camera_monitoring,
                    )

                    st.markdown(
                        f'<div style="margin-top:6px;">{badge_html}</div>',
                        unsafe_allow_html=True,
                    )

                face_ok = is_single_face(live_state)

            else:

                st.info(
                    "Camera monitoring is disabled."
                )

                # When monitoring is disabled the student
                # explicitly opted out during setup, so the
                # face requirement does not apply.
                live_state = None

                face_ok = True


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
                    disabled=not face_ok,
                ):

                    # Re-validate against the *latest*
                    # processor state here too, instead of
                    # trusting only the disabled attribute
                    # computed above. This protects against
                    # a face state change that happens
                    # between render and click.
                    if st.session_state.camera_monitoring:

                        fresh_state = get_live_face_state(
                            webrtc_ctx
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
                            "continuing."
                        )

                    elif not answer.strip():

                        st.warning(
                            "Please enter your answer."
                        )

                    else:

                        engine.save_answer(
                            answer.strip()
                        )

                        engine.next_question()

                        st.rerun()


            with col_skip:

                if st.button(
                    "⏭️ Skip",
                    use_container_width=True,
                    key=f"skip_{current_number}",
                    disabled=not face_ok,
                ):

                    # Skip must not bypass the face
                    # requirement either - re-check the
                    # latest processor state here as well.
                    if st.session_state.camera_monitoring:

                        fresh_state = get_live_face_state(
                            webrtc_ctx
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