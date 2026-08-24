# AI Career Twin - Interview Question Bank

# File: interview_questions.py

"""
Interview question bank for the AI Career Twin mock interview.

The interview follows a formal structure:

1. Introduction
2. Resume / Project Discussion
3. Technical Round
4. Problem Solving
5. Behavioral Round
6. HR Round
7. Closing

Main API:
get_questions(role)

Example:
questions = get_questions("Data Scientist")
"""

from typing import Dict, List

# ============================================================

# COMMON QUESTIONS

# ============================================================

INTRODUCTION_QUESTIONS = [
{
"id": "intro_1",
"question": "Good morning. Please introduce yourself and tell me about your academic background.",
"type": "introduction",
"difficulty": "easy",
},
{
"id": "intro_2",
"question": "Tell me about yourself and briefly walk me through your resume.",
"type": "introduction",
"difficulty": "easy",
},
]

RESUME_QUESTIONS = [
{
"id": "resume_1",
"question": "Can you explain one of the most important projects mentioned in your resume?",
"type": "resume",
"difficulty": "medium",
},
{
"id": "resume_2",
"question": "What was your specific contribution to the project you described?",
"type": "resume",
"difficulty": "medium",
},
{
"id": "resume_3",
"question": "What technical challenges did you face while developing your project, and how did you solve them?",
"type": "resume",
"difficulty": "medium",
},
]

PROBLEM_SOLVING_QUESTIONS = {
"Data Scientist": [
{
"id": "ds_problem_1",
"question": "You receive a dataset containing many missing values and inconsistent records. How would you approach cleaning and preparing the data?",
"type": "problem_solving",
"difficulty": "medium",
},
{
"id": "ds_problem_2",
"question": "Suppose your machine learning model performs very well on training data but poorly on unseen data. How would you investigate and solve the problem?",
"type": "problem_solving",
"difficulty": "hard",
},
],

"Data Analyst": [
    {
        "id": "da_problem_1",
        "question": "You are given a large dataset containing duplicate records and missing values. How would you clean the data before creating a report?",
        "type": "problem_solving",
        "difficulty": "medium",
    },
    {
        "id": "da_problem_2",
        "question": "A business dashboard shows that sales have suddenly decreased. How would you analyze the data to identify the reason?",
        "type": "problem_solving",
        "difficulty": "medium",
    },
],

"Software Engineer": [
    {
        "id": "se_problem_1",
        "question": "You are given a program that works correctly but is very slow for large inputs. How would you identify and improve its performance?",
        "type": "problem_solving",
        "difficulty": "medium",
    },
    {
        "id": "se_problem_2",
        "question": "How would you approach debugging a software application that works on your machine but fails in production?",
        "type": "problem_solving",
        "difficulty": "hard",
    },
],

"Backend Developer": [
    {
        "id": "backend_problem_1",
        "question": "An API becomes very slow when many users access it simultaneously. How would you investigate and improve its performance?",
        "type": "problem_solving",
        "difficulty": "medium",
    },
    {
        "id": "backend_problem_2",
        "question": "How would you design a backend system that can handle a large number of concurrent requests?",
        "type": "problem_solving",
        "difficulty": "hard",
    },
],

"Frontend Developer": [
    {
        "id": "frontend_problem_1",
        "question": "A web page takes several seconds to load. What steps would you take to identify and improve the performance?",
        "type": "problem_solving",
        "difficulty": "medium",
    },
    {
        "id": "frontend_problem_2",
        "question": "How would you make a web application responsive across mobile, tablet, and desktop devices?",
        "type": "problem_solving",
        "difficulty": "medium",
    },
],

"Full Stack Developer": [
    {
        "id": "fullstack_problem_1",
        "question": "A full-stack application works correctly for a small number of users but becomes slow as traffic increases. How would you investigate the issue?",
        "type": "problem_solving",
        "difficulty": "hard",
    },
    {
        "id": "fullstack_problem_2",
        "question": "How would you design a secure login and authentication system for a web application?",
        "type": "problem_solving",
        "difficulty": "hard",
    },
],

"Machine Learning Engineer": [
    {
        "id": "mle_problem_1",
        "question": "Your machine learning model has high training accuracy but low validation accuracy. What could be causing this and how would you fix it?",
        "type": "problem_solving",
        "difficulty": "hard",
    },
    {
        "id": "mle_problem_2",
        "question": "How would you deploy a machine learning model so that an application can make predictions in real time?",
        "type": "problem_solving",
        "difficulty": "hard",
    },
],

"AI Engineer": [
    {
        "id": "ai_problem_1",
        "question": "You need to build an AI system using a limited amount of training data. What techniques could you use to improve the system?",
        "type": "problem_solving",
        "difficulty": "hard",
    },
    {
        "id": "ai_problem_2",
        "question": "How would you evaluate whether an AI model is actually performing well in a real-world application?",
        "type": "problem_solving",
        "difficulty": "hard",
    },
],

"Python Developer": [
    {
        "id": "python_problem_1",
        "question": "A Python application is consuming too much memory. How would you investigate and optimize it?",
        "type": "problem_solving",
        "difficulty": "medium",
    },
    {
        "id": "python_problem_2",
        "question": "How would you structure a large Python application so that it remains maintainable and easy to test?",
        "type": "problem_solving",
        "difficulty": "hard",
    },
],

"Java Developer": [
    {
        "id": "java_problem_1",
        "question": "A Java application becomes slow as the number of users increases. How would you investigate the performance problem?",
        "type": "problem_solving",
        "difficulty": "medium",
    },
    {
        "id": "java_problem_2",
        "question": "How would you design a Java application using object-oriented principles so that it is maintainable and scalable?",
        "type": "problem_solving",
        "difficulty": "hard",
    },
],

"Cloud Engineer": [
    {
        "id": "cloud_problem_1",
        "question": "A cloud application suddenly receives ten times its normal traffic. How would you ensure that the application remains available?",
        "type": "problem_solving",
        "difficulty": "hard",
    },
    {
        "id": "cloud_problem_2",
        "question": "How would you design a reliable and scalable cloud architecture for a web application?",
        "type": "problem_solving",
        "difficulty": "hard",
    },
],

"DevOps Engineer": [
    {
        "id": "devops_problem_1",
        "question": "A deployment pipeline starts failing after a code change. How would you investigate and resolve the problem?",
        "type": "problem_solving",
        "difficulty": "medium",
    },
    {
        "id": "devops_problem_2",
        "question": "How would you design a CI/CD pipeline for a production web application?",
        "type": "problem_solving",
        "difficulty": "hard",
    },
],

"Database Administrator": [
    {
        "id": "dba_problem_1",
        "question": "A database query that previously took milliseconds now takes several seconds. How would you investigate the issue?",
        "type": "problem_solving",
        "difficulty": "medium",
    },
    {
        "id": "dba_problem_2",
        "question": "How would you protect a production database against data loss?",
        "type": "problem_solving",
        "difficulty": "hard",
    },
],

"Cybersecurity Analyst": [
    {
        "id": "cyber_problem_1",
        "question": "You notice unusual network activity in an organization. What steps would you take to investigate the incident?",
        "type": "problem_solving",
        "difficulty": "hard",
    },
    {
        "id": "cyber_problem_2",
        "question": "How would you respond if you discovered that an employee account had been compromised?",
        "type": "problem_solving",
        "difficulty": "hard",
    },
],

"Web Developer": [
    {
        "id": "web_problem_1",
        "question": "A web application is working correctly but has poor performance. What areas would you investigate first?",
        "type": "problem_solving",
        "difficulty": "medium",
    },
    {
        "id": "web_problem_2",
        "question": "How would you protect a web application from common security vulnerabilities?",
        "type": "problem_solving",
        "difficulty": "hard",
    },
],


}

# ============================================================

# TECHNICAL QUESTIONS BY ROLE

# ============================================================

TECHNICAL_QUESTIONS = {

"Data Scientist": [
    {
        "id": "ds_tech_1",
        "question": "What is the difference between supervised and unsupervised learning?",
        "type": "technical",
        "difficulty": "easy",
    },
    {
        "id": "ds_tech_2",
        "question": "What is overfitting in machine learning, and how can you reduce it?",
        "type": "technical",
        "difficulty": "medium",
    },
    {
        "id": "ds_tech_3",
        "question": "How would you handle missing values in a dataset?",
        "type": "technical",
        "difficulty": "medium",
    },
    {
        "id": "ds_tech_4",
        "question": "What is the difference between precision and recall?",
        "type": "technical",
        "difficulty": "medium",
    },
    {
        "id": "ds_tech_5",
        "question": "What are Pandas and NumPy used for?",
        "type": "technical",
        "difficulty": "easy",
    },
],

"Data Analyst": [
    {
        "id": "da_tech_1",
        "question": "What is the difference between INNER JOIN and LEFT JOIN in SQL?",
        "type": "technical",
        "difficulty": "easy",
    },
    {
        "id": "da_tech_2",
        "question": "What is the purpose of GROUP BY in SQL?",
        "type": "technical",
        "difficulty": "easy",
    },
    {
        "id": "da_tech_3",
        "question": "How would you identify and handle missing values in a dataset?",
        "type": "technical",
        "difficulty": "medium",
    },
    {
        "id": "da_tech_4",
        "question": "What is the difference between correlation and causation?",
        "type": "technical",
        "difficulty": "medium",
    },
    {
        "id": "da_tech_5",
        "question": "How can data visualization help in business decision-making?",
        "type": "technical",
        "difficulty": "easy",
    },
],

"Software Engineer": [
    {
        "id": "se_tech_1",
        "question": "What are the four main principles of object-oriented programming?",
        "type": "technical",
        "difficulty": "easy",
    },
    {
        "id": "se_tech_2",
        "question": "What is the difference between an array and a linked list?",
        "type": "technical",
        "difficulty": "medium",
    },
    {
        "id": "se_tech_3",
        "question": "What is the time complexity of binary search?",
        "type": "technical",
        "difficulty": "easy",
    },
    {
        "id": "se_tech_4",
        "question": "What is the difference between a process and a thread?",
        "type": "technical",
        "difficulty": "medium",
    },
    {
        "id": "se_tech_5",
        "question": "Why are databases used in software applications?",
        "type": "technical",
        "difficulty": "easy",
    },
],

"Backend Developer": [
    {
        "id": "backend_tech_1",
        "question": "What is a REST API?",
        "type": "technical",
        "difficulty": "easy",
    },
    {
        "id": "backend_tech_2",
        "question": "What is the difference between GET, POST, PUT, and DELETE?",
        "type": "technical",
        "difficulty": "medium",
    },
    {
        "id": "backend_tech_3",
        "question": "What is database normalization?",
        "type": "technical",
        "difficulty": "medium",
    },
    {
        "id": "backend_tech_4",
        "question": "What is authentication and how is it different from authorization?",
        "type": "technical",
        "difficulty": "medium",
    },
    {
        "id": "backend_tech_5",
        "question": "What are the advantages of using an API-based architecture?",
        "type": "technical",
        "difficulty": "medium",
    },
],

"Frontend Developer": [
    {
        "id": "frontend_tech_1",
        "question": "What is the difference between HTML, CSS, and JavaScript?",
        "type": "technical",
        "difficulty": "easy",
    },
    {
        "id": "frontend_tech_2",
        "question": "What is the DOM?",
        "type": "technical",
        "difficulty": "easy",
    },
    {
        "id": "frontend_tech_3",
        "question": "What is React and why is it commonly used?",
        "type": "technical",
        "difficulty": "easy",
    },
    {
        "id": "frontend_tech_4",
        "question": "What is responsive web design?",
        "type": "technical",
        "difficulty": "easy",
    },
    {
        "id": "frontend_tech_5",
        "question": "How would you improve the performance of a web page?",
        "type": "technical",
        "difficulty": "medium",
    },
],

"Full Stack Developer": [
    {
        "id": "fullstack_tech_1",
        "question": "What is the difference between frontend and backend development?",
        "type": "technical",
        "difficulty": "easy",
    },
    {
        "id": "fullstack_tech_2",
        "question": "How does a frontend application communicate with a backend API?",
        "type": "technical",
        "difficulty": "medium",
    },
    {
        "id": "fullstack_tech_3",
        "question": "What is the purpose of a database in a full-stack application?",
        "type": "technical",
        "difficulty": "easy",
    },
    {
        "id": "fullstack_tech_4",
        "question": "What is authentication in a web application?",
        "type": "technical",
        "difficulty": "medium",
    },
    {
        "id": "fullstack_tech_5",
        "question": "What is the difference between SQL and NoSQL databases?",
        "type": "technical",
        "difficulty": "medium",
    },
],

"Machine Learning Engineer": [
    {
        "id": "mle_tech_1",
        "question": "What is the difference between supervised and unsupervised learning?",
        "type": "technical",
        "difficulty": "easy",
    },
    {
        "id": "mle_tech_2",
        "question": "What is feature engineering?",
        "type": "technical",
        "difficulty": "medium",
    },
    {
        "id": "mle_tech_3",
        "question": "What is cross-validation and why is it useful?",
        "type": "technical",
        "difficulty": "medium",
    },
    {
        "id": "mle_tech_4",
        "question": "What is the difference between classification and regression?",
        "type": "technical",
        "difficulty": "easy",
    },
    {
        "id": "mle_tech_5",
        "question": "How would you deploy a trained machine learning model?",
        "type": "technical",
        "difficulty": "hard",
    },
],

"AI Engineer": [
    {
        "id": "ai_tech_1",
        "question": "What is the difference between artificial intelligence, machine learning, and deep learning?",
        "type": "technical",
        "difficulty": "easy",
    },
    {
        "id": "ai_tech_2",
        "question": "What is a neural network?",
        "type": "technical",
        "difficulty": "easy",
    },
    {
        "id": "ai_tech_3",
        "question": "What is natural language processing?",
        "type": "technical",
        "difficulty": "easy",
    },
    {
        "id": "ai_tech_4",
        "question": "What is computer vision?",
        "type": "technical",
        "difficulty": "easy",
    },
    {
        "id": "ai_tech_5",
        "question": "How would you evaluate an AI model before deploying it?",
        "type": "technical",
        "difficulty": "medium",
    },
],

"Python Developer": [
    {
        "id": "python_tech_1",
        "question": "What are the main features of Python?",
        "type": "technical",
        "difficulty": "easy",
    },
    {
        "id": "python_tech_2",
        "question": "What is the difference between a list, tuple, set, and dictionary in Python?",
        "type": "technical",
        "difficulty": "medium",
    },
    {
        "id": "python_tech_3",
        "question": "What is object-oriented programming in Python?",
        "type": "technical",
        "difficulty": "medium",
    },
    {
        "id": "python_tech_4",
        "question": "What are exceptions and how do you handle them in Python?",
        "type": "technical",
        "difficulty": "easy",
    },
    {
        "id": "python_tech_5",
        "question": "What is the difference between a module and a package in Python?",
        "type": "technical",
        "difficulty": "medium",
    },
],

"Java Developer": [
    {
        "id": "java_tech_1",
        "question": "What are the four main principles of object-oriented programming in Java?",
        "type": "technical",
        "difficulty": "easy",
    },
    {
        "id": "java_tech_2",
        "question": "What is the difference between an interface and an abstract class?",
        "type": "technical",
        "difficulty": "medium",
    },
    {
        "id": "java_tech_3",
        "question": "What is exception handling in Java?",
        "type": "technical",
        "difficulty": "easy",
    },
    {
        "id": "java_tech_4",
        "question": "What is the Java Virtual Machine?",
        "type": "technical",
        "difficulty": "easy",
    },
    {
        "id": "java_tech_5",
        "question": "What is the difference between ArrayList and LinkedList?",
        "type": "technical",
        "difficulty": "medium",
    },
],

"Cloud Engineer": [
    {
        "id": "cloud_tech_1",
        "question": "What is cloud computing?",
        "type": "technical",
        "difficulty": "easy",
    },
    {
        "id": "cloud_tech_2",
        "question": "What is the difference between IaaS, PaaS, and SaaS?",
        "type": "technical",
        "difficulty": "medium",
    },
    {
        "id": "cloud_tech_3",
        "question": "What is Docker and why is it useful?",
        "type": "technical",
        "difficulty": "easy",
    },
    {
        "id": "cloud_tech_4",
        "question": "What is Kubernetes?",
        "type": "technical",
        "difficulty": "medium",
    },
    {
        "id": "cloud_tech_5",
        "question": "What is auto-scaling in cloud computing?",
        "type": "technical",
        "difficulty": "medium",
    },
],

"DevOps Engineer": [
    {
        "id": "devops_tech_1",
        "question": "What is DevOps?",
        "type": "technical",
        "difficulty": "easy",
    },
    {
        "id": "devops_tech_2",
        "question": "What is CI/CD?",
        "type": "technical",
        "difficulty": "easy",
    },
    {
        "id": "devops_tech_3",
        "question": "What is Docker?",
        "type": "technical",
        "difficulty": "easy",
    },
    {
        "id": "devops_tech_4",
        "question": "What is Kubernetes used for?",
        "type": "technical",
        "difficulty": "medium",
    },
    {
        "id": "devops_tech_5",
        "question": "How does version control help a development team?",
        "type": "technical",
        "difficulty": "easy",
    },
],

"Database Administrator": [
    {
        "id": "dba_tech_1",
        "question": "What is database normalization?",
        "type": "technical",
        "difficulty": "easy",
    },
    {
        "id": "dba_tech_2",
        "question": "What is an index and why is it used?",
        "type": "technical",
        "difficulty": "medium",
    },
    {
        "id": "dba_tech_3",
        "question": "What is a primary key?",
        "type": "technical",
        "difficulty": "easy",
    },
    {
        "id": "dba_tech_4",
        "question": "What is a database transaction?",
        "type": "technical",
        "difficulty": "medium",
    },
    {
        "id": "dba_tech_5",
        "question": "What are ACID properties?",
        "type": "technical",
        "difficulty": "medium",
    },
],

"Cybersecurity Analyst": [
    {
        "id": "cyber_tech_1",
        "question": "What is cybersecurity?",
        "type": "technical",
        "difficulty": "easy",
    },
    {
        "id": "cyber_tech_2",
        "question": "What is the difference between authentication and authorization?",
        "type": "technical",
        "difficulty": "easy",
    },
    {
        "id": "cyber_tech_3",
        "question": "What is encryption?",
        "type": "technical",
        "difficulty": "easy",
    },
    {
        "id": "cyber_tech_4",
        "question": "What is phishing?",
        "type": "technical",
        "difficulty": "easy",
    },
    {
        "id": "cyber_tech_5",
        "question": "What is the principle of least privilege?",
        "type": "technical",
        "difficulty": "medium",
    },
],

"Web Developer": [
    {
        "id": "web_tech_1",
        "question": "What is the difference between HTML, CSS, and JavaScript?",
        "type": "technical",
        "difficulty": "easy",
    },
    {
        "id": "web_tech_2",
        "question": "What is responsive web design?",
        "type": "technical",
        "difficulty": "easy",
    },
    {
        "id": "web_tech_3",
        "question": "What is a backend in a web application?",
        "type": "technical",
        "difficulty": "easy",
    },
    {
        "id": "web_tech_4",
        "question": "What is an API?",
        "type": "technical",
        "difficulty": "easy",
    },
    {
        "id": "web_tech_5",
        "question": "What are common ways to improve web application security?",
        "type": "technical",
        "difficulty": "medium",
    },
],


}

# ============================================================

# BEHAVIORAL QUESTIONS

# ============================================================

BEHAVIORAL_QUESTIONS = [
{
"id": "behavior_1",
"question": "Tell me about a challenging project or situation you faced and how you handled it.",
"type": "behavioral",
"difficulty": "medium",
},
{
"id": "behavior_2",
"question": "Tell me about a time when you worked as part of a team.",
"type": "behavioral",
"difficulty": "medium",
},
{
"id": "behavior_3",
"question": "Describe a situation where something did not go according to plan. What did you learn from it?",
"type": "behavioral",
"difficulty": "medium",
},
]

# ============================================================

# HR QUESTIONS

# ============================================================

HR_QUESTIONS = [
{
"id": "hr_1",
"question": "Why are you interested in this role?",
"type": "hr",
"difficulty": "easy",
},
{
"id": "hr_2",
"question": "What are your greatest strengths?",
"type": "hr",
"difficulty": "easy",
},
{
"id": "hr_3",
"question": "What is one area you are currently working to improve?",
"type": "hr",
"difficulty": "easy",
},
{
"id": "hr_4",
"question": "Why should we hire you?",
"type": "hr",
"difficulty": "medium",
},
{
"id": "hr_5",
"question": "Where do you see yourself professionally in the next five years?",
"type": "hr",
"difficulty": "medium",
},
]

# ============================================================

# CLOSING QUESTIONS

# ============================================================

CLOSING_QUESTIONS = [
{
"id": "closing_1",
"question": "Do you have any questions for me about the role, team, or organization?",
"type": "closing",
"difficulty": "easy",
},
{
"id": "closing_2",
"question": "Thank you for your time. Is there anything else you would like to add before we conclude the interview?",
"type": "closing",
"difficulty": "easy",
},
]

# ============================================================

# ROLE ALIASES

# ============================================================

ROLE_ALIASES = {
"data science": "Data Scientist",
"data scientist": "Data Scientist",
"data analyst": "Data Analyst",
"software engineer": "Software Engineer",
"software developer": "Software Engineer",
"backend developer": "Backend Developer",
"back end developer": "Backend Developer",
"frontend developer": "Frontend Developer",
"front end developer": "Frontend Developer",
"full stack developer": "Full Stack Developer",
"fullstack developer": "Full Stack Developer",
"machine learning engineer": "Machine Learning Engineer",
"ml engineer": "Machine Learning Engineer",
"ai engineer": "AI Engineer",
"python developer": "Python Developer",
"java developer": "Java Developer",
"cloud engineer": "Cloud Engineer",
"devops engineer": "DevOps Engineer",
"database administrator": "Database Administrator",
"dba": "Database Administrator",
"cybersecurity analyst": "Cybersecurity Analyst",
"cyber security analyst": "Cybersecurity Analyst",
"web developer": "Web Developer",
}

# ============================================================

# DEFAULT TECHNICAL QUESTIONS

# ============================================================

DEFAULT_TECHNICAL_QUESTIONS = [
{
"id": "general_tech_1",
"question": "What are the most important technical skills required for this role?",
"type": "technical",
"difficulty": "easy",
},
{
"id": "general_tech_2",
"question": "Tell me about a technical problem you solved and how you approached it.",
"type": "technical",
"difficulty": "medium",
},
{
"id": "general_tech_3",
"question": "How do you keep your technical knowledge up to date?",
"type": "technical",
"difficulty": "easy",
},
]

# ============================================================

# ROLE NORMALIZATION

# ============================================================

def normalize_role(role: str) -> str:

    if not role:
        return "Software Engineer"

    role_clean = str(role).strip()

    if role_clean in TECHNICAL_QUESTIONS:
        return role_clean

    role_key = role_clean.lower()

    if role_key in ROLE_ALIASES:
        return ROLE_ALIASES[role_key]

# Partial matching for predicted role strings.
    for alias, canonical_role in ROLE_ALIASES.items():
        if alias in role_key:
            return canonical_role

    return "Software Engineer"

# ============================================================

# MAIN QUESTION GENERATOR

# ============================================================

def get_questions(role: str) -> Dict[str, List[dict]]:
    canonical_role = normalize_role(role)

    technical = TECHNICAL_QUESTIONS.get(
        canonical_role,
        DEFAULT_TECHNICAL_QUESTIONS,
    )

    problem_solving = PROBLEM_SOLVING_QUESTIONS.get(
        canonical_role,
        [
            {
                "id": "general_problem_1",
                "question": "Describe a difficult technical problem you encountered and explain how you solved it.",
                "type": "problem_solving",
                "difficulty": "medium",
            },
            {
                "id": "general_problem_2",
                "question": "How would you approach solving a problem when you do not initially know the solution?",
                "type": "problem_solving",
                "difficulty": "medium",
            },
        ],
    )

    return {
        "role": canonical_role,
        "introduction": INTRODUCTION_QUESTIONS.copy(),
        "resume": RESUME_QUESTIONS.copy(),
        "technical": list(technical),
        "problem_solving": list(problem_solving),
        "behavioral": BEHAVIORAL_QUESTIONS.copy(),
        "hr": HR_QUESTIONS.copy(),
        "closing": CLOSING_QUESTIONS.copy(),
    }

# ============================================================

# FLAT QUESTION LIST

# ============================================================

def get_flat_questions(role: str) -> List[dict]:
    """
    Return all questions for a role as a flat list.
    """
    question_set = get_questions(role)

    ordered_stages = [
        "introduction",
        "resume",
        "technical",
        "problem_solving",
        "behavioral",
        "hr",
        "closing",
    ]

    questions = []

    for stage in ordered_stages:
        for question in question_set.get(stage, []):
            item = question.copy()
            item["stage"] = stage
            questions.append(item)

    return questions

# ============================================================

# QUESTION COUNT

# ============================================================

def get_question_count(role: str) -> int:


    return len(get_flat_questions(role))

# ============================================================

# AVAILABLE ROLES

# ============================================================

def get_available_roles() -> List[str]:

    return list(TECHNICAL_QUESTIONS.keys())

# ============================================================

# SIMPLE TEST

# ============================================================

if __name__ == "__main__":

    role = "Data Scientist"

    print("=" * 60)
    print("AI CAREER TWIN - INTERVIEW QUESTION BANK")
    print("=" * 60)

    print(f"\nRole: {role}")

    questions = get_questions(role)

    for stage, stage_questions in questions.items():

        if stage == "role":
            continue

        print(f"\n--- {stage.upper()} ---")

        for index, question in enumerate(stage_questions, start=1):
            print(f"{index}. {question['question']}")

    print("\nTotal Questions:", get_question_count(role))
