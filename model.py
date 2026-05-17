import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
import joblib

# ============================================
# 1. RESUME CLASSIFICATION MODEL (NLP)
# ============================================
def train_role_model():

    data = pd.read_csv("dataset/roles_dataset.csv")

    X = data["resume"]
    y = data["role"]

    vectorizer = TfidfVectorizer()
    X_vec = vectorizer.fit_transform(X)

    model = LogisticRegression()
    model.fit(X_vec, y)

    joblib.dump(model, "role_model.pkl")
    joblib.dump(vectorizer, "vectorizer.pkl")

    print("✅ Role model trained!")

def predict_role(text):

    text = text.lower()

    role_keywords = {

        "Data Scientist": [
            "machine learning", "data analysis", "pandas",
            "numpy", "statistics", "data science"
        ],

        "Software Engineer": [
            "java", "c++", "data structures",
            "algorithms", "oop"
        ],

        "Web Developer": [
            "html", "css", "javascript",
            "react", "node"
        ],

        "Cloud Engineer": [
            "aws", "azure", "gcp", "cloud"
        ],

        "Cyber Security": [
            "security", "ethical hacking",
            "cryptography", "network security"
        ],

        "Android Developer": [
            "android", "kotlin", "firebase"
        ]
    }

    scores = {}

    for role, keywords in role_keywords.items():
        score = 0
        for word in keywords:
            if word in text:
                score += 1
        scores[role] = score

    # 🔥 pick role with highest score
    best_role = max(scores, key=scores.get)

    # fallback if all scores = 0
    if scores[best_role] == 0:
        return "Software Engineer"

    return best_role


# ============================================
# 2. PLACEMENT PREDICTION MODEL (ML)
# ============================================

def train_placement_model():
    data = pd.read_csv("dataset/placement_ai.csv")

    X = data[['cgpa', 'coding', 'projects', 'internships', 'communication']]
    y = data['placed']

    model = RandomForestClassifier()
    model.fit(X, y)

    joblib.dump(model, "placement_model.pkl")

    print("✅ Placement model trained!")

def predict_placement(cgpa, coding, projects, internships, communication):

    # Normalize inputs
    cgpa_score = cgpa / 10
    coding_score = coding / 100
    project_score = projects / 5
    internship_score = internships / 3
    comm_score = communication / 10

    # Weighted sum
    score = (
        cgpa_score * 0.3 +
        coding_score * 0.3 +
        project_score * 0.15 +
        internship_score * 0.15 +
        comm_score * 0.1
    )

    return score
