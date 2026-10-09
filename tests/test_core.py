import database
import interview_engine
import interview_evaluator
import recommender
import skill_gap


def test_password_hash_is_consistent():
    password = "TestPassword123!"
    assert database.hash_password(password) == database.hash_password(password)
    assert database.hash_password(password) != database.hash_password("WrongPassword")


def test_interview_questions_load():
    questions = interview_engine.get_questions("Software Engineer")
    assert questions is not None
    assert len(questions) > 0


def test_flat_questions_load():
    questions = interview_engine.get_flat_questions("Software Engineer")
    assert questions is not None
    assert len(questions) > 0


def test_evaluate_answer_returns_result():
    result = interview_evaluator.evaluate_answer(
        "What is Python?",
        "Python is a programming language used for software development."
    )
    assert result is not None


def test_skill_gap_returns_result():
    result = skill_gap.find_skill_gap(
        ["Python", "SQL"],
        "Software Engineer"
    )
    assert result is not None


def test_recommender_returns_result():
    result = recommender.recommend(["Python", "SQL"])
    assert result is not None
