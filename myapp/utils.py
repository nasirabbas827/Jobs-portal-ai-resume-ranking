import re
import fitz  # PyMuPDF
import docx2txt
from sklearn.feature_extraction.text import TfidfVectorizer

def extract_text_from_file(file_path):
    if file_path.endswith(".pdf"):
        text = ""
        with fitz.open(file_path) as doc:
            for page in doc:
                text += page.get_text()
        return text

    elif file_path.endswith(".docx"):
        return docx2txt.process(file_path)

    else:
        return ""


def parse_resume(file_path):
    text = extract_text_from_file(file_path)

    # Extract email & phone
    email = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}", text)
    phone = re.search(r"(\+?\d{1,3}[\s-]?)?\(?\d{2,4}\)?[\s.-]?\d{3,4}[\s.-]?\d{3,4}", text)

    # Extract name (first line heuristic)
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    name = lines[0] if lines else None

    # --- Work Experience Extraction ---
    experience_lines = []
    exp_keywords = ["Experience", "Work History", "Employment", "Professional Experience"]
    job_title_keywords = ["Engineer", "Developer", "Manager", "Consultant", "Analyst", "Intern"]

    for idx, line in enumerate(lines):
        if any(word.lower() in line.lower() for word in exp_keywords + job_title_keywords):
            experience_lines.append(line)

    # Extract years of experience
    years_exp_match = re.findall(r"(\d+)\+?\s*(?:years|yrs)", text, re.IGNORECASE)
    years_of_experience = max([int(y) for y in years_exp_match], default=0) if years_exp_match else None

    # --- Skills Extraction ---
    skills = []
    common_skills = ["Python", "Java", "C++", "SQL", "Django", "Flask", "React", "Node.js", "AWS", "Docker"]
    for skill in common_skills:
        if re.search(rf"\b{re.escape(skill)}\b", text, re.IGNORECASE):
            skills.append(skill)

    # --- Education Extraction ---
    education = []
    edu_keywords = ["Bachelor", "Master", "BS", "MS", "PhD", "B.Sc", "M.Sc", "University", "College"]
    for line in lines:
        if any(word in line for word in edu_keywords):
            education.append(line)

    # --- Keyword Extraction ---
    vectorizer = TfidfVectorizer(stop_words="english", max_features=10)
    tfidf_matrix = vectorizer.fit_transform([text])
    keywords = vectorizer.get_feature_names_out()

    return {
        "full_name": name,
        "email": email.group(0) if email else None,
        "phone": phone.group(0) if phone else None,
        "skills": ", ".join(skills),
        "education": "\n".join(education),
        "keywords": ", ".join(keywords),
        "work_experience": "\n".join(experience_lines),
        "years_of_experience": years_of_experience,
    }
