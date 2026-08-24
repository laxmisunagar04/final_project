# 🚀 AI Career Twin
### Intelligent Digital Twin for Personalized Placement Training

AI Career Twin is an AI-powered web application that creates a digital representation of a student's career profile. The system analyzes resumes using Natural Language Processing (NLP), predicts the most suitable career role, identifies skill gaps, recommends learning resources, and estimates placement readiness using Machine Learning.

This project was developed as a **Final Year Engineering Project** to help students improve their employability through personalized AI-driven career guidance.

---

# 📌 Features

## 📄 Resume Analysis
- Upload Resume (PDF)
- Automatic text extraction
- Technical skill extraction using NLP

## 🎯 Career Role Prediction
Predicts the most suitable career role using:
- TF-IDF Vectorization
- Logistic Regression

Supported Roles:
- Software Engineer
- Data Scientist
- Machine Learning Engineer
- AI Engineer
- Data Analyst
- Web Developer
- Frontend Developer
- Backend Developer
- Full Stack Developer
- Android Developer
- DevOps Engineer
- Cloud Engineer
- Cyber Security Analyst
- Database Administrator
- UI/UX Designer

---

## 📊 Skill Gap Analysis

Compares extracted skills with industry-required skills for the predicted role.

Displays:

- ✅ Matched Skills
- ❌ Missing Skills
- 📈 Skill Match Percentage

---

## 📚 Personalized Recommendations

Provides recommendations for improving missing skills.

Examples:

- Online Courses
- Practice Platforms
- Projects
- Documentation

---

## 📈 Placement Prediction

Predicts placement probability using Machine Learning based on:

- CGPA
- Coding Score
- Number of Projects
- Internships
- Communication Skills

---

## 📊 Interactive Dashboard

Displays:

- Skill Radar Chart
- Placement Probability
- Career Role
- Skill Analysis
- Recommendations

---

# 🏗 Project Architecture

```
                    Resume PDF
                         │
                         ▼
                Resume Text Extraction
                         │
                         ▼
                 NLP Preprocessing
                         │
                         ▼
               TF-IDF Vectorization
                         │
                         ▼
             Logistic Regression Model
                         │
                         ▼
               Predicted Career Role
                         │
         ┌───────────────┴───────────────┐
         ▼                               ▼
 Skill Gap Analysis          Placement Prediction
         ▼                               ▼
 Recommendation Engine        Probability Score
```

---

# 🛠 Technologies Used

## Programming Language

- Python 3.10

---

## Frontend

- Streamlit

---

## Machine Learning

- Scikit-learn
- Logistic Regression
- Random Forest Classifier
- TF-IDF Vectorizer

---

## NLP

- PyMuPDF (fitz)
- PDFPlumber
- TF-IDF
- Text Preprocessing

---

## Libraries

- Pandas
- NumPy
- Joblib
- Matplotlib
- Plotly

---

# 📂 Project Structure

```
AI_Career_Twin/
│
├── app.py
├── model.py
├── train.py
├── resume_parser.py
├── skill_gap.py
├── recommender.py
├── interview.py
├── requirements.txt
│
├── dataset/
│   ├── placement.csv
│   └── roles_dataset.csv
│
├── placement_model.pkl
├── role_model.pkl
├── vectorizer.pkl
│
└── README.md
```

---

# 📊 Dataset

The project uses two datasets.

## 1. Role Prediction Dataset

Contains:

- Resume Text
- Career Role

Used to train:

- TF-IDF
- Logistic Regression

---

## 2. Placement Dataset

Contains:

- CGPA
- Coding Score
- Projects
- Internships
- Communication Skills
- Placement Status

Used to train:

- Random Forest Classifier

---

# ⚙ Installation

Clone the repository

```bash
git clone https://github.com/yourusername/AI_Career_Twin.git
```

Move into project

```bash
cd AI_Career_Twin
```

Create Virtual Environment

Windows

```bash
python -m venv venv
```

Activate

PowerShell

```powershell
.\venv\Scripts\Activate.ps1
```

Command Prompt

```cmd
venv\Scripts\activate
```

Install dependencies

```bash
pip install -r requirements.txt
```

---

# ▶ Train Models

Run

```bash
python train.py
```

Output

```
✅ Role model trained!
✅ Placement model trained!
```

---

# ▶ Run Application

```bash
streamlit run app.py
```

Open

```
http://localhost:8501
```

---

# 🧠 Machine Learning Workflow

```
Resume PDF
      │
      ▼
Text Extraction
      │
      ▼
Text Cleaning
      │
      ▼
TF-IDF Vectorization
      │
      ▼
Logistic Regression
      │
      ▼
Career Role Prediction
```

---

# 📈 Placement Prediction Workflow

```
Student Inputs

CGPA
Coding Score
Projects
Internships
Communication

        │
        ▼

Random Forest Model

        │
        ▼

Placement Probability
```

---

# 📊 Evaluation

### Career Role Prediction

- Accuracy
- Precision
- Recall

### Placement Prediction

- Probability Score
- Prediction Accuracy

### Skill Gap Analysis

- Matched Skills
- Missing Skills
- Skill Match Percentage

---

# 🔒 Future Scope

- AI Mock Interview using LLMs
- Voice-based Interview Evaluation
- GitHub Profile Analysis
- LinkedIn Integration
- Knowledge Graph Skill Mapping
- AI Resume Builder
- Industry Job Recommendation
- Career Trajectory Prediction
- AI Career Mentor Chatbot

---

# 🎓 Academic Contribution

This project demonstrates:

- Natural Language Processing
- Machine Learning
- Resume Intelligence
- Career Analytics
- Personalized Recommendation Systems
- Placement Prediction

making it suitable for:

- Final Year Engineering Project
- AI/ML Mini Project
- Hackathons
- Research Prototype

---

# 👩‍💻 Developed By

** LAXMI SUNAGAR **
** JAYALAKSMI**
** MANASA S NAIK 
** ANUSHA G S **

Final Year Engineering Project

---

# 📄 License

This project is developed for educational and academic purposes.