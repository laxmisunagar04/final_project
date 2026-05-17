"""
database.py — SQLite setup and user management for AI Career Twin
"""

import sqlite3
import hashlib
import os

DB_PATH = "career_twin.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    c = conn.cursor()

    # Students table
    c.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL,
            email       TEXT UNIQUE NOT NULL,
            password    TEXT NOT NULL,
            college     TEXT,
            branch      TEXT,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Companies table
    c.execute("""
        CREATE TABLE IF NOT EXISTS companies (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL,
            email       TEXT UNIQUE NOT NULL,
            password    TEXT NOT NULL,
            industry    TEXT,
            website     TEXT,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Student profiles (stores latest resume analysis results)
    c.execute("""
        CREATE TABLE IF NOT EXISTS student_profiles (
            student_id      INTEGER PRIMARY KEY,
            skills          TEXT,
            predicted_role  TEXT,
            placement_prob  REAL,
            cgpa            REAL,
            coding_score    INTEGER,
            projects        INTEGER,
            internships     INTEGER,
            communication   INTEGER,
            updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students(id)
        )
    """)

    conn.commit()
    conn.close()


# ─── Password hashing ───────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


# ─── Student auth ────────────────────────────────────────────────────────────

def register_student(name, email, password, college="", branch=""):
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO students (name, email, password, college, branch) VALUES (?, ?, ?, ?, ?)",
            (name, email, hash_password(password), college, branch)
        )
        conn.commit()
        return True, "Account created successfully!"
    except sqlite3.IntegrityError:
        return False, "Email already registered."
    finally:
        conn.close()


def login_student(email, password):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM students WHERE email=? AND password=?",
        (email, hash_password(password))
    ).fetchone()
    conn.close()
    return dict(row) if row else None


# ─── Company auth ────────────────────────────────────────────────────────────

def register_company(name, email, password, industry="", website=""):
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO companies (name, email, password, industry, website) VALUES (?, ?, ?, ?, ?)",
            (name, email, hash_password(password), industry, website)
        )
        conn.commit()
        return True, "Company registered successfully!"
    except sqlite3.IntegrityError:
        return False, "Email already registered."
    finally:
        conn.close()


def login_company(email, password):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM companies WHERE email=? AND password=?",
        (email, hash_password(password))
    ).fetchone()
    conn.close()
    return dict(row) if row else None


# ─── Student profile ─────────────────────────────────────────────────────────

def save_student_profile(student_id, skills, predicted_role, placement_prob,
                          cgpa, coding_score, projects, internships, communication):
    conn = get_connection()
    conn.execute("""
        INSERT INTO student_profiles
            (student_id, skills, predicted_role, placement_prob,
             cgpa, coding_score, projects, internships, communication)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(student_id) DO UPDATE SET
            skills=excluded.skills,
            predicted_role=excluded.predicted_role,
            placement_prob=excluded.placement_prob,
            cgpa=excluded.cgpa,
            coding_score=excluded.coding_score,
            projects=excluded.projects,
            internships=excluded.internships,
            communication=excluded.communication,
            updated_at=CURRENT_TIMESTAMP
    """, (student_id, ",".join(skills), predicted_role, placement_prob,
          cgpa, coding_score, projects, internships, communication))
    conn.commit()
    conn.close()


def get_student_profile(student_id):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM student_profiles WHERE student_id=?", (student_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


# ─── Company: browse all student profiles ────────────────────────────────────

def get_all_student_profiles():
    conn = get_connection()
    rows = conn.execute("""
        SELECT s.name, s.email, s.college, s.branch,
               p.skills, p.predicted_role, p.placement_prob,
               p.cgpa, p.coding_score, p.projects, p.internships, p.communication
        FROM students s
        JOIN student_profiles p ON s.id = p.student_id
        ORDER BY p.placement_prob DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]
