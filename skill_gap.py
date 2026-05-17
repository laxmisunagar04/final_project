def find_skill_gap(user_skills, role):

    role = role.lower().strip()

    ROLE_SKILLS = {

        "data scientist": [
            "python", "machine learning", "pandas",
            "numpy", "statistics", "sql", "data visualization"
        ],

        "software engineer": [
            "java", "c++", "data structures",
            "algorithms", "oop", "dbms"
        ],

        "web developer": [
            "html", "css", "javascript",
            "react", "node.js", "mongodb"
        ],

        "backend developer": [
            "python", "java", "node.js",
            "api", "sql", "dbms"
        ],

        "frontend developer": [
            "html", "css", "javascript",
            "react", "ui", "ux"
        ],

        "full stack developer": [
            "html", "css", "javascript",
            "react", "node.js", "mongodb"
        ],

        "machine learning engineer": [
            "python", "machine learning",
            "deep learning", "tensorflow",
            "pytorch", "numpy"
        ],

        "data analyst": [
            "sql", "excel", "power bi",
            "tableau", "python", "data visualization"
        ],

        "devops engineer": [
            "docker", "kubernetes", "aws",
            "linux", "ci/cd", "git"
        ],

        "cyber security": [
            "network security", "cryptography",
            "ethical hacking", "linux", "firewalls"
        ],

        "cloud engineer": [
            "aws", "azure", "gcp",
            "docker", "kubernetes"
        ],

        "android developer": [
            "java", "kotlin", "android",
            "firebase", "xml"
        ],

        "ios developer": [
            "swift", "ios", "xcode",
            "ui design"
        ],

        "ai engineer": [
            "python", "deep learning",
            "nlp", "tensorflow", "pytorch"
        ],

        "information technology": [
            "python", "sql", "dbms",
            "data structures", "algorithms"
        ]
    }

    # 🔥 Smart role matching (no exact match issue)
    required = []

    for key in ROLE_SKILLS:
        if key in role:
            required = ROLE_SKILLS[key]
            break

    # fallback
    if not required:
        required = ["python", "sql", "data structures"]

    user_skills = [s.lower().strip() for s in user_skills]

    matched = [skill for skill in required if skill in user_skills]
    missing = [skill for skill in required if skill not in user_skills]

    return missing, matched, required