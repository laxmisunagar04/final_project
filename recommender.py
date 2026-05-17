def recommend(missing_skills):

    if not missing_skills:
        return ["✅ You are already well prepared!"]

    resource_map = {

        "python": "Learn Python → Coursera / YouTube",
        "machine learning": "ML Course → Andrew Ng (Coursera)",
        "pandas": "Pandas → Kaggle tutorials",
        "numpy": "NumPy → Official Docs",
        "sql": "SQL → LeetCode + W3Schools",
        "data structures": "DSA → Striver Sheet",
        "algorithms": "Algorithms → GeeksforGeeks",
        "html": "HTML → FreeCodeCamp",
        "css": "CSS → FreeCodeCamp",
        "javascript": "JavaScript → MDN Docs",
        "react": "React → Official Docs",
        "node.js": "Node.js → YouTube",
        "mongodb": "MongoDB → MongoDB University",
        "deep learning": "Deep Learning → Coursera",
        "tensorflow": "TensorFlow → Official Tutorials",
        "pytorch": "PyTorch → Official Docs",
        "docker": "Docker → YouTube",
        "kubernetes": "Kubernetes → KodeKloud",
        "aws": "AWS → AWS Academy",
        "excel": "Excel → YouTube",
        "power bi": "Power BI → Microsoft Learn",
        "tableau": "Tableau → Tableau Public",
    }

    recommendations = []

    for skill in missing_skills:
        if skill in resource_map:
            recommendations.append(resource_map[skill])
        else:
            recommendations.append(f"Learn {skill} from online resources")

    return recommendations