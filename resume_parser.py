import fitz
import pytesseract
from PIL import Image
import io

def extract_resume_data(uploaded_file):

    text = ""

    pdf = fitz.open(stream=uploaded_file.read(), filetype="pdf")

    for page in pdf:
        page_text = page.get_text()

        if page_text:
            text += page_text
        else:
            # OCR fallback
            pix = page.get_pixmap()
            img = Image.open(io.BytesIO(pix.tobytes()))
            text += pytesseract.image_to_string(img)

    text = text.lower()

    skill_keywords = [
    "python", "java", "c++", "sql",
    "machine learning", "deep learning",
    "data structures", "algorithms",
    "oop", "dbms",
    "pandas", "numpy", "tensorflow",
    "html", "css", "javascript", "react",
    "node", "aws", "docker", "kubernetes",
    "excel", "power bi", "tableau"
]

    skills = [skill for skill in skill_keywords if skill in text]

    print("Extracted Skills:", skills)

    return list(set(skills)), text