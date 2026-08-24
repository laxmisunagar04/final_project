import re


def evaluate_answer(question, answer):

    answer = answer.strip()

    if not answer:
        return {
            "technical": 0,
            "communication": 0,
            "relevance": 0,
            "overall": 0,
            "feedback": "No answer was provided."
        }

    words = answer.split()

    word_count = len(words)

    # Basic answer-quality calculation
    if word_count < 10:
        communication = 40
    elif word_count < 30:
        communication = 65
    elif word_count < 60:
        communication = 80
    else:
        communication = 90

    # Question keyword matching
    question_words = set(
        re.findall(r"[a-zA-Z]+", question.lower())
    )

    answer_words = set(
        re.findall(r"[a-zA-Z]+", answer.lower())
    )

    if question_words:
        relevance_ratio = len(
            question_words.intersection(answer_words)
        ) / len(question_words)
    else:
        relevance_ratio = 0

    relevance = min(
        100,
        int(relevance_ratio * 150)
    )

    if relevance < 30:
        relevance = 45

    technical = int(
        (communication + relevance) / 2
    )

    overall = int(
        technical * 0.5 +
        communication * 0.25 +
        relevance * 0.25
    )

    if overall >= 80:
        feedback = "Excellent answer. Your response was clear and relevant."

    elif overall >= 60:
        feedback = "Good answer. Try to provide more specific examples."

    else:
        feedback = "Your answer needs improvement. Give a clearer and more structured response."

    return {
        "technical": technical,
        "communication": communication,
        "relevance": relevance,
        "overall": overall,
        "feedback": feedback
    }