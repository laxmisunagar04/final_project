"""
feedback_engine.py — Answer scoring and personalised feedback generation.

Current implementation: deterministic heuristics (no API key required).
Future: drop-in replacement with OpenAI / Claude API call.

Scoring dimensions:
  - length_score      (0-25): penalises one-liners and empty answers
  - keyword_score     (0-40): how many topic keywords the answer contains
  - structure_score   (0-20): presence of explanatory language / structure
  - confidence_score  (0-15): hedging language detector (penalised)

Total raw score is normalised to 0–100.
"""

from __future__ import annotations

import re
from typing import Optional

# ─── Keyword map: topic → expected keywords ───────────────────────────────────
TOPIC_KEYWORDS: dict[str, list[str]] = {
    "Data Structures":    ["stack", "queue", "array", "linked list", "tree", "graph", "hash", "heap"],
    "OOP":                ["encapsulation", "inheritance", "polymorphism", "abstraction", "class", "object", "interface"],
    "DBMS":               ["table", "index", "query", "normalization", "transaction", "acid", "join", "foreign key", "schema"],
    "Algorithms":         ["complexity", "o(n)", "sort", "search", "recursion", "dynamic programming", "greedy", "divide"],
    "System Design":      ["scalability", "load balancer", "database", "cache", "microservices", "api", "availability", "latency"],
    "Distributed Systems":["consistency", "availability", "partition", "cap theorem", "replication", "sharding", "consensus"],
    "SQL":                ["select", "join", "group by", "where", "having", "index", "subquery", "aggregate", "window"],
    "Statistics":         ["mean", "median", "variance", "standard deviation", "distribution", "hypothesis", "p-value", "confidence"],
    "ML Fundamentals":    ["training", "validation", "test", "overfitting", "underfitting", "loss", "gradient", "feature", "label"],
    "Optimization":       ["gradient descent", "learning rate", "convergence", "batch", "momentum", "adam", "sgd"],
    "Evaluation Metrics": ["accuracy", "precision", "recall", "f1", "roc", "auc", "confusion matrix", "mse", "rmse"],
    "NLP":                ["token", "embedding", "transformer", "attention", "bert", "gpt", "sentiment", "sequence"],
    "Deep Learning":      ["neural network", "layer", "activation", "backpropagation", "cnn", "rnn", "lstm", "dropout"],
    "CSS":                ["flexbox", "grid", "margin", "padding", "selector", "specificity", "responsive", "media query"],
    "JavaScript":         ["closure", "prototype", "promise", "async", "event loop", "hoisting", "scope", "callback"],
    "React":              ["component", "state", "props", "hook", "useeffect", "usestate", "virtual dom", "context", "redux"],
    "APIs":               ["rest", "http", "endpoint", "request", "response", "authentication", "json", "graphql", "status code"],
    "Security":           ["encryption", "hash", "jwt", "oauth", "xss", "csrf", "ssl", "tls", "authentication", "authorization"],
    "Databases":          ["sql", "nosql", "index", "transaction", "schema", "replication", "sharding", "acid"],
    "Scalability":        ["horizontal", "vertical", "load balancer", "cache", "cdn", "queue", "microservice", "stateless"],
    "Containers":         ["docker", "image", "container", "volume", "network", "compose", "registry", "layer"],
    "Observability":      ["logging", "metrics", "tracing", "monitoring", "alerting", "dashboard", "sli", "slo"],
    "Performance":        ["cache", "lazy loading", "bundle", "minify", "cdn", "reflow", "repaint", "virtual scroll"],
    "Architecture":       ["modular", "separation of concerns", "design pattern", "solid", "microservice", "monolith", "coupling"],
    "Analytics":          ["kpi", "metric", "dashboard", "cohort", "funnel", "retention", "segment", "visualization"],
    "Data Engineering":   ["pipeline", "etl", "batch", "streaming", "kafka", "spark", "airflow", "schema", "warehouse"],
    "ML Engineering":     ["pipeline", "feature store", "model serving", "drift", "monitoring", "versioning", "mlops"],
    "Tools":              ["git", "docker", "ci/cd", "github", "jira", "terminal", "ide", "vscode"],
    "Programming":        ["function", "variable", "loop", "condition", "class", "module", "import", "exception"],
    "Web Frameworks":     ["route", "middleware", "controller", "model", "view", "request", "response", "orm"],
    "IaC":                ["terraform", "cloudformation", "ansible", "declarative", "state", "resource", "module"],
    "Deployment":         ["blue-green", "canary", "rolling", "rollback", "zero-downtime", "feature flag"],
    "Reliability":        ["rto", "rpo", "disaster recovery", "failover", "redundancy", "backup", "region"],
    "Dimensionality Reduction": ["pca", "variance", "components", "eigenvalue", "t-sne", "umap"],
    "Experimentation":    ["hypothesis", "control", "treatment", "sample size", "statistical significance", "p-value"],
    "Unsupervised ML":    ["cluster", "centroid", "k-means", "silhouette", "dbscan", "hierarchical"],
    "Applied ML":         ["feature engineering", "pipeline", "baseline", "evaluation", "production", "inference"],
    "Ensemble Methods":   ["random forest", "boosting", "bagging", "xgboost", "feature importance", "weak learner"],
    "Visualization":      ["chart", "graph", "bar", "line", "scatter", "histogram", "heatmap", "tableau", "power bi"],
    "MLOps":              ["docker", "kubernetes", "mlflow", "airflow", "versioning", "registry", "serving", "monitoring"],
    "Forecasting":        ["arima", "prophet", "time series", "trend", "seasonality", "forecast", "regression"],
    "HTML":               ["tag", "element", "attribute", "semantic", "dom", "form", "input", "accessibility"],
    "Excel / BI":         ["pivot", "vlookup", "formula", "filter", "chart", "dashboard", "power bi"],
    "Data Concepts":      ["structured", "unstructured", "schema", "format", "pipeline", "data lake"],
}

HEDGING_PHRASES = [
    r"\bi think\b", r"\bmaybe\b", r"\bi'm not sure\b", r"\bi guess\b",
    r"\bprobably\b", r"\bnot sure\b", r"\bi don't know\b", r"\bkind of\b",
    r"\bsort of\b", r"\bif i recall\b",
]

STRUCTURE_MARKERS = [
    r"\bfirst(ly)?\b", r"\bsecond(ly)?\b", r"\bfinally\b", r"\bfor example\b",
    r"\bfor instance\b", r"\bsuch as\b", r"\bspecifically\b", r"\bin other words\b",
    r"\bto summarize\b", r"\bin conclusion\b", r"\btherefore\b", r"\bbecause\b",
    r"\bthis means\b", r"\bhowever\b", r"\bon the other hand\b",
]


def _length_score(text: str) -> tuple[int, str]:
    words = len(text.split())
    if words == 0:
        return 0, "No answer provided."
    elif words < 15:
        return 8, "Very brief — try to elaborate with examples."
    elif words < 40:
        return 15, "Decent length but could be more detailed."
    elif words < 100:
        return 22, "Good answer length."
    else:
        return 25, "Comprehensive length."


def _keyword_score(text: str, topic: str) -> tuple[int, list[str], list[str]]:
    text_lower = text.lower()
    expected   = TOPIC_KEYWORDS.get(topic, [])
    found      = [kw for kw in expected if kw in text_lower]
    missing    = [kw for kw in expected if kw not in text_lower]
    ratio      = len(found) / max(len(expected), 1)
    score      = round(ratio * 40)
    return score, found, missing[:5]  # cap missing list to 5


def _structure_score(text: str) -> tuple[int, str]:
    text_lower = text.lower()
    hits = sum(1 for pat in STRUCTURE_MARKERS if re.search(pat, text_lower))
    if hits >= 4:
        return 20, "Well-structured with clear explanations."
    elif hits >= 2:
        return 14, "Reasonable structure; add more connecting phrases."
    elif hits == 1:
        return 8, "Lacks structure. Use 'first', 'for example', 'because' etc."
    else:
        return 4, "Answer reads as a raw list of terms without explanation."


def _confidence_score(text: str) -> tuple[int, str]:
    text_lower = text.lower()
    hedges = sum(1 for pat in HEDGING_PHRASES if re.search(pat, text_lower))
    if hedges == 0:
        return 15, "Confident delivery — good."
    elif hedges == 1:
        return 10, "Minor hedging detected. Try to sound more assured."
    elif hedges <= 3:
        return 5, "Multiple hesitations detected. Practice stating answers more directly."
    else:
        return 0, "Significant uncertainty in delivery. Work on framing answers confidently."


def score_answer(answer: str, question: dict) -> dict:
    """
    Score a single answer. Returns a rich dict compatible with feedback_engine
    and scorecard modules.
    """
    topic = question.get("topic", "Programming")

    l_score,  l_note             = _length_score(answer)
    k_score,  found_kw, miss_kw  = _keyword_score(answer, topic)
    st_score, st_note            = _structure_score(answer)
    c_score,  c_note             = _confidence_score(answer)

    raw_total = l_score + k_score + st_score + c_score  # max 100
    pct       = min(raw_total, 100)

    return {
        "total":          pct,
        "length_score":   l_score,
        "keyword_score":  k_score,
        "structure_score":st_score,
        "confidence_score":c_score,
        "found_keywords": found_kw,
        "missing_keywords":miss_kw,
        "notes": {
            "length":     l_note,
            "keywords":   f"Covered: {', '.join(found_kw) or 'none'}. Missing: {', '.join(miss_kw) or 'none'}.",
            "structure":  st_note,
            "confidence": c_note,
        },
    }


def score_all_answers(session_data: dict) -> dict[int, dict]:
    """Score every answered question. Returns {question_idx: score_dict}."""
    scores = {}
    for idx, answer in session_data["answers"].items():
        q = session_data["questions"][idx]
        scores[idx] = score_answer(answer, q)
    return scores


def generate_feedback(session_data: dict, scores: dict[int, dict]) -> dict:
    """
    Build personalised per-question feedback + an overall improvement roadmap.
    """
    skills   = session_data.get("skills", [])
    role     = session_data.get("raw_role", "the target role")
    per_q    = {}

    for idx, s in scores.items():
        q    = session_data["questions"][idx]
        pct  = s["total"]

        if pct >= 80:
            rating  = "Excellent"
            emoji   = "🔥"
            summary = f"Strong answer. You clearly understand {q['topic']}."
        elif pct >= 60:
            rating  = "Good"
            emoji   = "👍"
            summary = f"Solid answer. Expand on {', '.join(s['missing_keywords'][:2]) or 'key concepts'} next time."
        elif pct >= 40:
            rating  = "Needs Work"
            emoji   = "⚠️"
            summary = f"Partially correct. Focus on: {', '.join(s['missing_keywords'][:3]) or 'depth and clarity'}."
        else:
            rating  = "Weak"
            emoji   = "❌"
            summary = f"Answer needs significant improvement. Study {q['topic']} fundamentals."

        per_q[idx] = {
            "rating":  rating,
            "emoji":   emoji,
            "summary": summary,
            "tips":    [
                s["notes"]["length"],
                s["notes"]["keywords"],
                s["notes"]["structure"],
                s["notes"]["confidence"],
            ],
            "follow_up": q.get("follow_up", ""),
        }

    # ── Improvement roadmap ──────────────────────────────────────────────────
    weak_topics = [
        session_data["questions"][i]["topic"]
        for i, s in scores.items()
        if s["total"] < 60
    ]
    weak_topics = list(dict.fromkeys(weak_topics))  # deduplicate, preserve order

    # Skills in resume vs skills mentioned in answers
    answered_text = " ".join(session_data["answers"].values()).lower()
    unused_skills = [sk for sk in skills if sk.lower() not in answered_text]

    roadmap = []
    if weak_topics:
        roadmap.append(f"📚 Deepen your knowledge in: **{', '.join(weak_topics)}**")
    if unused_skills:
        roadmap.append(
            f"🛠️ You listed {', '.join(unused_skills[:4])} on your resume — demonstrate "
            f"these more explicitly in answers."
        )
    roadmap.append(f"🎯 Practice answering with the **STAR method** (Situation, Task, Action, Result).")
    roadmap.append(f"🔁 Do 3 mock interviews per week for {role} to build fluency.")

    # Recommended technologies / resources per weak topic
    tech_map = {
        "Data Structures":   ["LeetCode (Easy → Medium)", "NeetCode.io", "CTCI book"],
        "System Design":     ["Grokking the System Design Interview", "ByteByteGo blog", "System Design Primer (GitHub)"],
        "ML Fundamentals":   ["fast.ai", "Hands-On ML (Aurélien Géron)", "Kaggle Learn"],
        "SQL":               ["Mode Analytics SQL Tutorial", "SQLZoo", "LeetCode Database"],
        "Statistics":        ["StatQuest (YouTube)", "Think Stats (book)", "Khan Academy Statistics"],
        "React":             ["React docs (react.dev)", "Epic React by Kent C. Dodds"],
        "APIs":              ["REST API Design Rulebook", "Postman Learning Center"],
        "Security":          ["OWASP Top 10", "PortSwigger Web Security Academy"],
        "Algorithms":        ["LeetCode", "The Algorithm Design Manual", "Coursera Algorithms"],
        "Deep Learning":     ["fast.ai", "Andrej Karpathy's YouTube", "Deep Learning (Goodfellow)"],
        "NLP":               ["HuggingFace Course", "Stanford CS224N", "spaCy documentation"],
    }

    recommended = []
    for topic in weak_topics[:3]:
        resources = tech_map.get(topic, ["Official documentation", "YouTube tutorials", "Practice problems"])
        recommended.append({"topic": topic, "resources": resources})

    return {
        "per_question": per_q,
        "roadmap":      roadmap,
        "recommended":  recommended,
        "weak_topics":  weak_topics,
        "unused_skills":unused_skills,
    }