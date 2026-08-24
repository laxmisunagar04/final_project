"""
AI Career Twin - Formal AI Mock Interview
Live WebRTC Camera + Real-Time Face Monitoring
"""

import os
import sys
import threading
import time
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


# ============================================================
# CSS
# ============================================================

st.markdown(
    """
<style>

.question-card {
    background: linear-gradient(
        135deg,
        #0f172a,
        #1e1b4b
    );

    border: 1px solid #312e81;
    border-left: 5px solid #e94560;

    border-radius: 18px;

    padding: 30px;

    margin-bottom: 20px;
}

.question-number {
    color: #e94560;
    font-size: 14px;
    font-weight: 700;
    margin-bottom: 15px;
}

.question-stage {
    display: inline-block;

    background: #312e81;
    color: #c4b5fd;

    padding: 6px 14px;

    border-radius: 20px;

    font-size: 13px;

    margin-bottom: 15px;
}

.question-text {
    color: #f8fafc;

    font-size: 21px;

    font-weight: 600;

    line-height: 1.6;
}

.complete-card {
    background: linear-gradient(
        135deg,
        #052e16,
        #064e3b
    );

    border: 1px solid #166534;

    border-radius: 20px;

    padding: 50px;

    text-align: center;
}

.monitor-box {
    padding: 15px;

    border-radius: 12px;

    margin-top: 10px;
}

</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# REAL-TIME CAMERA PROCESSOR
# ============================================================

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

    def recv(self, frame):

        image = frame.to_ndarray(
            format="bgr24"
        )

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

                self.movement_distance = (
                    round(distance, 2)
                )

                if distance > 35:

                    self.movement = "Moving"

                elif distance > 12:

                    self.movement = (
                        "Slight movement"
                    )

                else:

                    self.movement = "Stable"

            self.previous_center = (
                current_center
            )

        else:

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
# CAMERA COMPONENT
# ============================================================

def render_camera():

    st.markdown(
        "### 📷 Live Camera Monitoring"
    )

    if not WEBRTC_AVAILABLE:

        st.error(
            "streamlit-webrtc is not installed."
        )

        st.code(
            "pip install streamlit-webrtc opencv-python av"
        )

        return

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

    webrtc_streamer(
        key="ai-career-twin-interview",

        mode=WebRtcMode.SENDRECV,

        rtc_configuration=rtc_configuration,

        media_stream_constraints={
            "video": True,
            "audio": False
        },

        video_processor_factory=(
            InterviewVideoProcessor
        ),

        async_processing=True,

    )


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


# ============================================================
# HEADER
# ============================================================

st.title(
    "🎤 AI Mock Interview"
)

st.caption(
    "Formal role-based interview with real-time camera monitoring"
)

st.divider()


# ============================================================
# INTERVIEW SETUP
# ============================================================

if not st.session_state.interview_started:

    st.subheader(
        "🎯 Interview Setup"
    )

    st.info(
        "The interview follows a formal sequence "
        "from introduction to closing."
    )

    col1, col2 = st.columns(
        [2, 1]
    )

    with col1:

        st.markdown(
            "### Selected Role"
        )

        st.markdown(
            f"## 🎯 {default_role}"
        )

    with col2:

        st.markdown(
            "### Interview Structure"
        )

        st.write(
            """
            1. Introduction
            2. Resume
            3. Technical
            4. Problem Solving
            5. Behavioral
            6. HR
            7. Closing
            """
        )

    st.divider()

    st.markdown(
        "### 📋 Interview Rules"
    )

    st.write(
        """
        • Answer each question clearly.

        • Explain your reasoning for technical questions.

        • Use examples from your projects.

        • Keep your face visible to the camera.

        • Only one person should appear in the camera.

        • The camera monitors face presence and approximate movement.
        """
    )

    st.divider()

    camera_enabled = st.checkbox(
        "📷 Enable live camera monitoring",
        value=True
    )

    st.session_state.camera_monitoring = (
        camera_enabled
    )

    if st.button(
        "🚀 Start Formal Interview",
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

        st.success(
            "🎉 Interview Complete"
        )

        results = engine.get_results()

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
            "📝 Interview Answers"
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

            st.session_state.interview_engine = (
                None
            )

            st.session_state.interview_started = (
                False
            )

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


        st.progress(
            percentage / 100
        )

        st.caption(
            f"Question {current_number} "
            f"of {total_questions} "
            f"• {percentage}% complete"
        )

        st.divider()


        # ====================================================
        # CAMERA / QUESTION
        # ====================================================

        camera_col, question_col = (
            st.columns(
                [1, 1.5]
            )
        )


        # ====================================================
        # CAMERA
        # ====================================================

        with camera_col:

            if (
                st.session_state.camera_monitoring
            ):

                render_camera()

            else:

                st.info(
                    "Camera monitoring is disabled."
                )


        # ====================================================
        # QUESTION
        # ====================================================

        with question_col:

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

                # IMPORTANT:
                # Do not use an indented HTML block.
                # Streamlit markdown will render this correctly.

                question_html = (
                    '<div class="question-card">'
                    f'<div class="question-number">'
                    f'QUESTION {current_number}'
                    f' &nbsp; • &nbsp; '
                    f'{difficulty.upper()}'
                    f'</div>'
                    f'<div class="question-stage">'
                    f'{question_type.replace("_", " ").title()}'
                    f'</div>'
                    f'<div class="question-text">'
                    f'{question_data["question"]}'
                    f'</div>'
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


            # =================================================
            # ANSWER
            # =================================================

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


            # =================================================
            # BUTTONS
            # =================================================

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
                    key=f"submit_{current_number}"
                ):

                    if not answer.strip():

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
                    key=f"skip_{current_number}"
                ):

                    engine.skip_question()

                    st.rerun()


        # ====================================================
        # INTERVIEW STAGES
        # ====================================================

        st.divider()

        st.subheader(
            "📌 Formal Interview Progress"
        )

        stages = [
            "Introduction",
            "Resume",
            "Technical",
            "Problem Solving",
            "Behavioral",
            "HR",
            "Closing"
        ]

        stage_cols = st.columns(
            len(stages)
        )

        for col, stage_name in zip(
            stage_cols,
            stages
        ):

            with col:

                if stage_name == stage:

                    st.success(
                        f"● {stage_name}"
                    )

                else:

                    st.caption(
                        stage_name
                    )