from datetime import datetime

from interview_questions import get_questions, get_flat_questions

class InterviewEngine:

    def __init__(self, role, resume_text=""):

        self.role = role
        self.resume_text = resume_text or ""

        self.stages = [
            "Introduction",
            "Resume",
            "Technical",
            "Problem Solving",
            "Behavioral",
            "HR",
            "Closing",
        ]

        self.stage = "Introduction"

        self.question_number = 0

        self.questions = []
        self.current_question = None

        self.answers = []

        self.technical_score = []
        self.communication_score = []
        self.relevance_score = []
        self.completeness_score = []
        self.problem_solving_score = []

        self.started = False
        self.completed = False

        self.start_time = None
        self.end_time = None

        self.question_bank = get_questions(self.role)
        self.all_questions = get_flat_questions(self.role)

        self.total_questions = len(self.all_questions)

    def start_interview(self):

        self.started = True
        self.completed = False

        self.start_time = datetime.now()

        self.stage = "Introduction"
        self.question_number = 0

        self.answers = []

        self.technical_score = []
        self.communication_score = []
        self.relevance_score = []
        self.completeness_score = []
        self.problem_solving_score = []

        if self.all_questions:
            self.current_question = self.all_questions[0]
            return self.current_question["question"]

        return "No interview questions are available."

    def get_current_question(self):

        if not self.started:
            return (
                "Welcome to AI Career Twin. "
                "Please click Start Interview to begin."
            )

        if self.completed:
            return (
                "Thank you for attending the interview. "
                "This concludes the interview."
            )

        if not self.all_questions:
            return "No interview questions are available."

        if self.question_number >= len(self.all_questions):
            self.completed = True
            self.stage = "Completed"
            self.end_time = datetime.now()

            return (
                "Thank you for attending the interview. "
                "This concludes the interview."
            )

        self.current_question = self.all_questions[
            self.question_number
        ]

        return self.current_question["question"]

    def get_current_question_data(self):

        if not self.started or self.completed:
            return None

        if self.question_number >= len(self.all_questions):
            return None

        self.current_question = self.all_questions[
            self.question_number
        ]

        return self.current_question

    def get_current_stage(self):

        if self.completed:
            return "Completed"

        return self.stage

    def save_answer(self, answer):

        if not self.started or self.completed:
            return False

        question_data = self.get_current_question_data()

        if question_data is None:
            return False

        answer = answer or ""

        answer_record = {
            "question_number": self.question_number + 1,
            "stage": self.stage,
            "question_id": question_data.get("id"),
            "question": question_data.get("question"),
            "question_type": question_data.get("type"),
            "difficulty": question_data.get("difficulty"),
            "answer": answer,
            "timestamp": datetime.now().isoformat(),
        }

        self.answers.append(answer_record)

        return True

    def save_evaluation(self, evaluation):

        if not evaluation:
            return

        if "technical_score" in evaluation:
            self.technical_score.append(
                self._safe_score(evaluation["technical_score"])
            )

        if "communication_score" in evaluation:
            self.communication_score.append(
                self._safe_score(evaluation["communication_score"])
            )

        if "relevance_score" in evaluation:
            self.relevance_score.append(
                self._safe_score(evaluation["relevance_score"])
            )

        if "completeness_score" in evaluation:
            self.completeness_score.append(
                self._safe_score(evaluation["completeness_score"])
            )

        if "problem_solving_score" in evaluation:
            self.problem_solving_score.append(
                self._safe_score(
                    evaluation["problem_solving_score"]
                )
            )

    @staticmethod
    def _safe_score(value):

        try:
            score = float(value)
            return max(0.0, min(100.0, score))

        except (ValueError, TypeError):
            return 0.0

    def next_question(self):

        if not self.started:
            return self.start_interview()

        if self.completed:
            return (
                "Thank you for attending the interview. "
                "This concludes the interview."
            )

        self.question_number += 1

        if self.question_number >= len(self.all_questions):

            self.completed = True
            self.stage = "Completed"
            self.end_time = datetime.now()
            self.current_question = None

            return (
                "Thank you for attending the interview. "
                "This concludes the interview."
            )

        self.current_question = self.all_questions[
            self.question_number
        ]

        self.stage = self._convert_stage_name(
            self.current_question.get("stage", "")
        )

        return self.current_question["question"]

    @staticmethod
    def _convert_stage_name(stage):

        stage_map = {
            "introduction": "Introduction",
            "resume": "Resume",
            "technical": "Technical",
            "problem_solving": "Problem Solving",
            "behavioral": "Behavioral",
            "hr": "HR",
            "closing": "Closing",
        }

        return stage_map.get(
            str(stage).lower(),
            "Technical"
        )

    def skip_question(self):

        if not self.started or self.completed:
            return None

        question_data = self.get_current_question_data()

        if question_data:

            self.answers.append({
                "question_number": self.question_number + 1,
                "stage": self.stage,
                "question_id": question_data.get("id"),
                "question": question_data.get("question"),
                "question_type": question_data.get("type"),
                "difficulty": question_data.get("difficulty"),
                "answer": "",
                "skipped": True,
                "timestamp": datetime.now().isoformat(),
            })

        return self.next_question()

    def is_complete(self):

        return self.completed

    def get_question_number(self):

        if self.completed:
            return self.total_questions

        return self.question_number + 1

    def get_total_questions(self):

        return self.total_questions

    def get_progress(self):

        if self.completed:
            return 100

        if self.total_questions == 0:
            return 0

        progress = (
            self.question_number
            / self.total_questions
        ) * 100

        return round(progress)

    def get_progress_data(self):

        return {
            "current": self.get_question_number(),
            "total": self.total_questions,
            "percentage": self.get_progress(),
            "stage": self.stage,
        }

    def get_duration_seconds(self):

        if not self.start_time:
            return 0

        end_time = self.end_time or datetime.now()

        duration = (
            end_time - self.start_time
        ).total_seconds()

        return round(duration)

    @staticmethod
    def _average(scores):

        if not scores:
            return 0

        return round(
            sum(scores) / len(scores),
            2
        )

    def get_results(self):

        technical = self._average(
            self.technical_score
        )

        communication = self._average(
            self.communication_score
        )

        relevance = self._average(
            self.relevance_score
        )

        completeness = self._average(
            self.completeness_score
        )

        problem_solving = self._average(
            self.problem_solving_score
        )

        available_scores = [
            score
            for score in [
                technical,
                communication,
                relevance,
                completeness,
                problem_solving,
            ]
            if score > 0
        ]

        if available_scores:

            overall = round(
                sum(available_scores)
                / len(available_scores),
                2
            )

        else:
            overall = 0

        return {
            "role": self.role,
            "stage": self.stage,
            "completed": self.completed,
            "total_questions": self.total_questions,
            "answered_questions": len(self.answers),
            "duration_seconds": self.get_duration_seconds(),
            "technical_score": technical,
            "communication_score": communication,
            "relevance_score": relevance,
            "completeness_score": completeness,
            "problem_solving_score": problem_solving,
            "overall_score": overall,
            "answers": self.answers,
        }

    def reset(self):

        self.stage = "Introduction"
        self.question_number = 0

        self.questions = []
        self.current_question = None

        self.answers = []

        self.technical_score = []
        self.communication_score = []
        self.relevance_score = []
        self.completeness_score = []
        self.problem_solving_score = []

        self.started = False
        self.completed = False

        self.start_time = None
        self.end_time = None

        self.question_bank = get_questions(self.role)
        self.all_questions = get_flat_questions(self.role)

        self.total_questions = len(self.all_questions)

# ============================================================
# DIRECT TEST
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("AI CAREER TWIN - INTERVIEW ENGINE TEST")
    print("=" * 60)

    engine = InterviewEngine("Data Scientist")

    print()
    print("Role:", engine.role)

    print(
        "Total Questions:",
        engine.get_total_questions()
    )

    print()
    print("Starting interview...")

    first_question = engine.start_interview()

    print()
    print("Question 1:")
    print(first_question)

    print()
    print("Progress:")
    print(engine.get_progress_data())

    engine.save_answer(
        "I am an Information Science student with experience "
        "in Python, machine learning and databases."
    )

    next_question = engine.next_question()

    print()
    print("Question 2:")
    print(next_question)

    print()
    print("Current Stage:")
    print(engine.get_current_stage())

    print()
    print("Progress:")
    print(engine.get_progress_data())

    print()
    print("Interview Engine imported and tested successfully.")