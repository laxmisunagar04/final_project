"""
question_bank.py — Role-based, skill-aware interview question bank.

Structure:
  QUESTION_BANK[normalized_role][difficulty] = [ {question, topic, follow_up}, ... ]

Difficulty levels: "easy" | "medium" | "hard"

Role keys are lowercase-normalized versions of what predict_role() returns.
The engine uses fuzzy role matching so partial matches work too.
"""

from __future__ import annotations
import re
from typing import Optional

# ─── Master question bank ────────────────────────────────────────────────────

QUESTION_BANK: dict[str, dict[str, list[dict]]] = {

    # ── Software Engineer ────────────────────────────────────────────────────
    "software engineer": {
        "easy": [
            {"question": "What is the difference between a stack and a queue?",
             "topic": "Data Structures", "follow_up": "Can you name a real-world use case for each?"},
            {"question": "Explain the concept of Object-Oriented Programming and its four pillars.",
             "topic": "OOP", "follow_up": "How does polymorphism differ from inheritance?"},
            {"question": "What is a primary key in a relational database?",
             "topic": "DBMS", "follow_up": "What happens if a primary key column has a NULL value?"},
            {"question": "What is the difference between '==' and '===' in JavaScript?",
             "topic": "Programming", "follow_up": "When would you prefer strict equality?"},
            {"question": "Explain the purpose of version control systems like Git.",
             "topic": "Tools", "follow_up": "What is the difference between 'git merge' and 'git rebase'?"},
        ],
        "medium": [
            {"question": "Explain the time complexity of common sorting algorithms (Merge Sort, Quick Sort, Bubble Sort).",
             "topic": "Algorithms", "follow_up": "When would you choose Merge Sort over Quick Sort?"},
            {"question": "What is normalization in databases? Explain 1NF, 2NF, and 3NF.",
             "topic": "DBMS", "follow_up": "When might you intentionally denormalize a database?"},
            {"question": "Describe the SOLID principles of software design.",
             "topic": "System Design", "follow_up": "Give an example of violating the Single Responsibility Principle."},
            {"question": "What is a REST API? How does it differ from GraphQL?",
             "topic": "APIs", "follow_up": "When would GraphQL be a better choice than REST?"},
            {"question": "Explain the concept of concurrency vs parallelism.",
             "topic": "Systems", "follow_up": "How do mutexes and semaphores prevent race conditions?"},
        ],
        "hard": [
            {"question": "Design a URL shortener system like Bit.ly. Walk me through your architecture.",
             "topic": "System Design", "follow_up": "How would you handle 10 million requests per day?"},
            {"question": "Implement a Least Recently Used (LRU) Cache. What data structures would you use?",
             "topic": "Data Structures", "follow_up": "What is the time complexity of get and put operations?"},
            {"question": "Explain the CAP theorem and how it applies to distributed systems.",
             "topic": "Distributed Systems", "follow_up": "How does eventual consistency differ from strong consistency?"},
            {"question": "How would you design a distributed job scheduler?",
             "topic": "System Design", "follow_up": "How do you handle job failures and retries?"},
        ],
    },

    # ── Data Analyst ─────────────────────────────────────────────────────────
    "data analyst": {
        "easy": [
            {"question": "What is the difference between INNER JOIN and LEFT JOIN in SQL?",
             "topic": "SQL", "follow_up": "When would you use a FULL OUTER JOIN?"},
            {"question": "What is the difference between mean, median, and mode?",
             "topic": "Statistics", "follow_up": "When is the median a better measure of central tendency than the mean?"},
            {"question": "What is a pivot table and when would you use one?",
             "topic": "Excel / BI", "follow_up": "How would you build the same aggregation in SQL?"},
            {"question": "Explain the difference between structured and unstructured data.",
             "topic": "Data Concepts", "follow_up": "Give an example of semi-structured data."},
            {"question": "What does GROUP BY do in SQL? Give an example.",
             "topic": "SQL", "follow_up": "What is the difference between WHERE and HAVING?"},
        ],
        "medium": [
            {"question": "Explain the ETL process. What are the common pitfalls?",
             "topic": "Data Engineering", "follow_up": "How do you handle missing or corrupt data during transformation?"},
            {"question": "What is a window function in SQL? Give an example using RANK().",
             "topic": "SQL", "follow_up": "How does PARTITION BY differ from GROUP BY?"},
            {"question": "How would you detect and handle outliers in a dataset?",
             "topic": "Statistics", "follow_up": "What is the IQR method for outlier detection?"},
            {"question": "Walk me through how you would build a sales performance dashboard.",
             "topic": "Visualization", "follow_up": "Which KPIs would you prioritize and why?"},
            {"question": "What is the difference between correlation and causation?",
             "topic": "Statistics", "follow_up": "How would you design an A/B test to establish causation?"},
        ],
        "hard": [
            {"question": "How would you design a data pipeline for real-time analytics on user events?",
             "topic": "Data Engineering", "follow_up": "What tools would you use — Kafka, Spark, Flink?"},
            {"question": "Explain cohort analysis. How would you track user retention over 6 months?",
             "topic": "Analytics", "follow_up": "How does churn rate factor into your cohort model?"},
            {"question": "How would you forecast next quarter's revenue using historical sales data?",
             "topic": "Forecasting", "follow_up": "What statistical models would you consider — ARIMA, Prophet, regression?"},
        ],
    },

    # ── Machine Learning Engineer ─────────────────────────────────────────────
    "machine learning engineer": {
        "easy": [
            {"question": "What is the difference between supervised and unsupervised learning?",
             "topic": "ML Fundamentals", "follow_up": "Give two examples of each type."},
            {"question": "What is overfitting? How do you detect and prevent it?",
             "topic": "ML Fundamentals", "follow_up": "What role does cross-validation play?"},
            {"question": "Explain the bias-variance tradeoff.",
             "topic": "ML Theory", "follow_up": "How does model complexity affect bias and variance?"},
            {"question": "What is the purpose of a train/validation/test split?",
             "topic": "ML Fundamentals", "follow_up": "What is data leakage and how do you prevent it?"},
            {"question": "What is the difference between precision and recall?",
             "topic": "Evaluation Metrics", "follow_up": "When would you optimize for recall over precision?"},
        ],
        "medium": [
            {"question": "Explain how gradient descent works. What are its variants?",
             "topic": "Optimization", "follow_up": "What is the difference between SGD, Adam, and RMSProp?"},
            {"question": "What is regularization? Explain L1 vs L2.",
             "topic": "ML Fundamentals", "follow_up": "What is ElasticNet and when would you use it?"},
            {"question": "How does a Random Forest differ from a single Decision Tree?",
             "topic": "Ensemble Methods", "follow_up": "What is feature importance in Random Forest?"},
            {"question": "Explain the transformer architecture used in NLP models.",
             "topic": "NLP / Deep Learning", "follow_up": "What is the role of the attention mechanism?"},
            {"question": "How would you handle a heavily imbalanced classification dataset?",
             "topic": "ML Engineering", "follow_up": "When would SMOTE be appropriate vs class weight adjustment?"},
        ],
        "hard": [
            {"question": "Design an end-to-end ML pipeline for a real-time recommendation system.",
             "topic": "ML System Design", "follow_up": "How do you handle model drift in production?"},
            {"question": "Explain how you would deploy a TensorFlow model as a REST API at scale.",
             "topic": "MLOps", "follow_up": "How do you manage versioning and rollbacks for ML models?"},
            {"question": "Compare BERT, GPT, and T5. When would you fine-tune vs use zero-shot?",
             "topic": "NLP", "follow_up": "What are the tradeoffs between fine-tuning a large model vs prompting?"},
            {"question": "How would you build a fraud detection system? Walk through feature engineering.",
             "topic": "Applied ML", "follow_up": "How would you evaluate the model given severe class imbalance?"},
        ],
    },

    # ── Frontend Developer ────────────────────────────────────────────────────
    "frontend developer": {
        "easy": [
            {"question": "What is the difference between CSS Flexbox and CSS Grid?",
             "topic": "CSS", "follow_up": "When would you choose Grid over Flexbox?"},
            {"question": "Explain the concept of the Virtual DOM in React.",
             "topic": "React", "follow_up": "How does React's reconciliation algorithm work?"},
            {"question": "What is the difference between 'let', 'const', and 'var' in JavaScript?",
             "topic": "JavaScript", "follow_up": "Explain hoisting and how it differs for each."},
            {"question": "What is semantic HTML and why does it matter?",
             "topic": "HTML", "follow_up": "How does semantic HTML impact SEO and accessibility?"},
            {"question": "What is the box model in CSS?",
             "topic": "CSS", "follow_up": "What is the difference between 'content-box' and 'border-box'?"},
        ],
        "medium": [
            {"question": "Explain React hooks. What problem did they solve over class components?",
             "topic": "React", "follow_up": "When would you use useReducer over useState?"},
            {"question": "What is code splitting and lazy loading? How do you implement it in React?",
             "topic": "Performance", "follow_up": "How does React.Suspense work?"},
            {"question": "Explain the event loop in JavaScript.",
             "topic": "JavaScript", "follow_up": "What is the difference between a Promise and async/await?"},
            {"question": "What is Cross-Site Scripting (XSS)? How do you prevent it on the frontend?",
             "topic": "Security", "follow_up": "What is Content Security Policy (CSP)?"},
            {"question": "How does browser rendering work? Explain the critical rendering path.",
             "topic": "Performance", "follow_up": "What causes reflows and repaints?"},
        ],
        "hard": [
            {"question": "Design a scalable component library from scratch. What decisions matter most?",
             "topic": "Architecture", "follow_up": "How would you handle theming and design tokens?"},
            {"question": "How would you optimize a React app with 10,000 list items rendering slowly?",
             "topic": "Performance", "follow_up": "Explain virtual scrolling and how to implement it."},
            {"question": "Explain micro-frontend architecture. When would you adopt it?",
             "topic": "Architecture", "follow_up": "What are the challenges with shared state across micro-frontends?"},
        ],
    },

    # ── Backend Developer ─────────────────────────────────────────────────────
    "backend developer": {
        "easy": [
            {"question": "What is the difference between authentication and authorization?",
             "topic": "Security", "follow_up": "How does JWT differ from session-based authentication?"},
            {"question": "Explain the difference between SQL and NoSQL databases.",
             "topic": "Databases", "follow_up": "When would you choose MongoDB over PostgreSQL?"},
            {"question": "What are HTTP status codes? Give examples for 200, 400, 401, 404, 500.",
             "topic": "APIs", "follow_up": "What is the difference between 401 and 403?"},
            {"question": "What is middleware in web frameworks like Express or Django?",
             "topic": "Web Frameworks", "follow_up": "How would you write a custom logging middleware?"},
            {"question": "What is the difference between synchronous and asynchronous programming?",
             "topic": "Programming", "follow_up": "How does Node.js handle async I/O?"},
        ],
        "medium": [
            {"question": "How does database indexing improve query performance?",
             "topic": "Databases", "follow_up": "When can an index actually hurt performance?"},
            {"question": "Explain the difference between horizontal and vertical scaling.",
             "topic": "Scalability", "follow_up": "What are the challenges of stateful vs stateless services in horizontal scaling?"},
            {"question": "What is a message queue? Describe a use case for RabbitMQ or Kafka.",
             "topic": "Architecture", "follow_up": "What is the difference between a queue and a pub/sub system?"},
            {"question": "How would you implement rate limiting on an API?",
             "topic": "APIs", "follow_up": "What are the tradeoffs between token bucket and leaky bucket algorithms?"},
            {"question": "Explain connection pooling in databases. Why is it important?",
             "topic": "Databases", "follow_up": "What happens if your pool size is too small?"},
        ],
        "hard": [
            {"question": "Design a scalable authentication service supporting OAuth2 and SSO.",
             "topic": "System Design", "follow_up": "How do you handle token revocation at scale?"},
            {"question": "How would you design a notification service that handles 1M push notifications per hour?",
             "topic": "System Design", "follow_up": "How do you handle delivery guarantees and retries?"},
            {"question": "Explain CQRS and Event Sourcing. When would you use them together?",
             "topic": "Architecture", "follow_up": "What are the consistency challenges with CQRS?"},
        ],
    },

    # ── Data Scientist ────────────────────────────────────────────────────────
    "data scientist": {
        "easy": [
            {"question": "What is the difference between a parametric and non-parametric statistical test?",
             "topic": "Statistics", "follow_up": "When would you use a Mann-Whitney U test?"},
            {"question": "Explain p-value and statistical significance.",
             "topic": "Statistics", "follow_up": "What are the dangers of p-hacking?"},
            {"question": "What is feature engineering? Give three examples.",
             "topic": "ML Fundamentals", "follow_up": "How does feature scaling affect distance-based algorithms?"},
            {"question": "What is the difference between a bar chart and a histogram?",
             "topic": "Visualization", "follow_up": "When should you use a box plot instead?"},
        ],
        "medium": [
            {"question": "Explain Principal Component Analysis (PCA). When would you use it?",
             "topic": "Dimensionality Reduction", "follow_up": "How do you choose the number of principal components?"},
            {"question": "How would you design an A/B test for a new product feature?",
             "topic": "Experimentation", "follow_up": "How do you calculate the required sample size?"},
            {"question": "What is the difference between Bayesian and frequentist statistics?",
             "topic": "Statistics", "follow_up": "Give an example of a prior in a Bayesian model."},
            {"question": "How do you evaluate a clustering model? What metrics would you use?",
             "topic": "Unsupervised ML", "follow_up": "What is the silhouette score?"},
        ],
        "hard": [
            {"question": "How would you build a churn prediction model for a subscription SaaS product?",
             "topic": "Applied ML", "follow_up": "How would you translate model output into a business action?"},
            {"question": "Design a multi-armed bandit system for A/B testing. Why might it outperform classical A/B?",
             "topic": "Experimentation", "follow_up": "What is the explore-exploit tradeoff?"},
        ],
    },

    # ── DevOps / Cloud ────────────────────────────────────────────────────────
    "devops engineer": {
        "easy": [
            {"question": "What is the difference between Docker and a virtual machine?",
             "topic": "Containers", "follow_up": "What is a Docker layer and how does caching work?"},
            {"question": "What is CI/CD? Walk me through a typical pipeline.",
             "topic": "DevOps", "follow_up": "What is the difference between continuous delivery and continuous deployment?"},
            {"question": "What is Kubernetes and what problems does it solve?",
             "topic": "Orchestration", "follow_up": "What is the difference between a Pod, Deployment, and Service?"},
        ],
        "medium": [
            {"question": "Explain blue-green deployment vs canary release.",
             "topic": "Deployment", "follow_up": "When would you choose a canary release?"},
            {"question": "What is Infrastructure as Code? Compare Terraform and CloudFormation.",
             "topic": "IaC", "follow_up": "What are the advantages of declarative IaC over imperative scripts?"},
            {"question": "How would you monitor a production microservices deployment?",
             "topic": "Observability", "follow_up": "What is the difference between logging, metrics, and tracing?"},
        ],
        "hard": [
            {"question": "Design a disaster recovery strategy for a multi-region cloud application.",
             "topic": "Reliability", "follow_up": "What are RTO and RPO, and how do they drive architecture decisions?"},
        ],
    },
}

# ── Aliases so fuzzy matching works ──────────────────────────────────────────
ROLE_ALIASES: dict[str, str] = {
    "swe": "software engineer",
    "software developer": "software engineer",
    "full stack developer": "software engineer",
    "fullstack developer": "software engineer",
    "full-stack developer": "software engineer",
    "ml engineer": "machine learning engineer",
    "ai engineer": "machine learning engineer",
    "deep learning engineer": "machine learning engineer",
    "nlp engineer": "machine learning engineer",
    "data engineer": "data analyst",          # closest bucket
    "bi analyst": "data analyst",
    "business analyst": "data analyst",
    "react developer": "frontend developer",
    "vue developer": "frontend developer",
    "ui developer": "frontend developer",
    "node developer": "backend developer",
    "django developer": "backend developer",
    "api developer": "backend developer",
    "cloud engineer": "devops engineer",
    "site reliability engineer": "devops engineer",
    "sre": "devops engineer",
}

# Default role used when no match is found
DEFAULT_ROLE = "software engineer"
ALL_ROLES = list(QUESTION_BANK.keys())


def normalize_role(raw_role: str) -> str:
    """Map a raw predict_role() output to a QUESTION_BANK key."""
    cleaned = raw_role.strip().lower()
    cleaned = re.sub(r"[^a-z\s]", "", cleaned)  # strip punctuation

    # Direct match
    if cleaned in QUESTION_BANK:
        return cleaned

    # Alias match
    if cleaned in ROLE_ALIASES:
        return ROLE_ALIASES[cleaned]

    # Partial / substring match
    for key in QUESTION_BANK:
        if key in cleaned or cleaned in key:
            return key

    # Word-level overlap scoring
    cleaned_words = set(cleaned.split())
    best_key, best_score = DEFAULT_ROLE, 0
    for key in QUESTION_BANK:
        overlap = len(cleaned_words & set(key.split()))
        if overlap > best_score:
            best_score, best_key = overlap, key

    return best_key if best_score > 0 else DEFAULT_ROLE


def get_questions(
    role: str,
    difficulty: str = "medium",
    skills: Optional[list[str]] = None,
    count: int = 5,
) -> list[dict]:
    """
    Return `count` questions for a given role and difficulty.

    Skill-aware weighting: if any of the user's skills appear in the question
    topic (case-insensitive), that question floats to the top of the selection.
    """
    norm = normalize_role(role)
    pool = QUESTION_BANK.get(norm, QUESTION_BANK[DEFAULT_ROLE])
    questions = list(pool.get(difficulty, pool.get("medium", [])))

    if not questions:
        # Fallback: collapse all difficulties
        for d in ["easy", "medium", "hard"]:
            questions.extend(pool.get(d, []))

    if skills:
        skill_set = {s.lower() for s in skills}

        def relevance(q: dict) -> int:
            topic_words = set(q["topic"].lower().split())
            question_words = set(q["question"].lower().split())
            return len(skill_set & (topic_words | question_words))

        questions = sorted(questions, key=relevance, reverse=True)

    return questions[:count]


def get_all_difficulties(role: str) -> list[str]:
    norm = normalize_role(role)
    pool = QUESTION_BANK.get(norm, QUESTION_BANK[DEFAULT_ROLE])
    return [d for d in ["easy", "medium", "hard"] if d in pool]