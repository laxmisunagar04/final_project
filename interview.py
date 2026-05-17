import openai

def generate_questions(role):
    prompt = f"Generate 3 interview questions for {role}"

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )

    return response['choices'][0]['message']['content']


def evaluate_answer(answer):
    prompt = f"Evaluate this answer: {answer} and give score out of 10"

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )

    return response['choices'][0]['message']['content']