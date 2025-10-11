from typing import List, Dict, Optional
from sentence_transformers import SentenceTransformer
import numpy as np
import re
from textblob import TextBlob

MODEL_NAME = "all-MiniLM-L6-v2"
_model = SentenceTransformer(MODEL_NAME)


def embed_text(text: str) -> np.ndarray:
    if not text:
        return np.zeros(_model.get_sentence_embedding_dimension(), dtype=float)
    vec = _model.encode([text], show_progress_bar=False)[0]
    norm = np.linalg.norm(vec)
    return vec / (norm + 1e-9)


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    if a is None or b is None or a.size == 0 or b.size == 0:
        return 0.0
    return float(
        np.dot(a, b) /
        (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9)
    )


def normalize_list(items: List[str]) -> List[str]:
    # Enhanced normalization to handle variations
    normalized = []
    for item in items:
        if item and item.strip():
            # Convert to lowercase, remove extra spaces, and handle common variations
            item = re.sub(r"\s+", " ", item.strip().lower())
            # Map variations to standard forms
            item = item.replace("django framework", "django").replace("python 3", "python")
            normalized.append(item)
    return normalized


def extract_skills_from_text(text: str) -> List[str]:
    if not text:
        return []
    text = text.lower()
    # Include common skills to ensure they're caught
    common_skills = [
        "python", "java", "c++", "sql", "django", "flask", "react",
        "node.js", "aws", "docker", "javascript", "html", "css", "git"
    ]
    tokens = re.findall(r"[A-Za-z0-9\.\+\-#]+", text)
    skills = sorted({t for t in tokens if 1 < len(t) < 40})
    # Add common skills if present in text
    skills.extend([skill for skill in common_skills if skill in text])
    return sorted(set(skills))


def soft_skill_score(text: str) -> float:
    if not text:
        return 0.0
    soft_skills = [
        "leadership", "communication", "teamwork", "management",
        "time management", "problem solving", "adaptability",
        "creativity", "collaboration", "critical thinking",
        "problem-solving", "team player", "initiative", "work ethic"
    ]
    text = text.lower()
    blob = TextBlob(text)
    sentiment_score = blob.sentiment.polarity
    matched = sum(1 for skill in soft_skills if skill in text)
    base_score = matched / len(soft_skills)
    sentiment_boost = (sentiment_score + 1) / 2
    return base_score * (1 + 0.2 * sentiment_boost)


def rank_resume_for_job(job: dict, parsed_resume: dict) -> Dict:
    weights = {
        "semantic": 0.5,
        "technical_skill_overlap": 0.25,
        "soft_skill": 0.1,
        "experience": 0.1,
        "keyword_relevance": 0.05
    }

    job_text = " ".join(filter(None, [
        job.get("title", ""),
        job.get("description", ""),
        job.get("requirements", "")
    ]))

    resume_text = " ".join(filter(None, [
        parsed_resume.get("full_name", ""),
        parsed_resume.get("skills", ""),
        parsed_resume.get("work_experience", ""),
        parsed_resume.get("education", ""),
        parsed_resume.get("keywords", "")
    ]))

    job_vec = embed_text(job_text)
    resume_vec = embed_text(resume_text)
    semantic_sim = cosine(job_vec, resume_vec)

    # Job skills extraction with fallback to description
    job_skills = []
    if job.get("skills"):
        if isinstance(job["skills"], list):
            job_skills = normalize_list(job["skills"])
        else:
            raw = re.split(r"[,\n;]", str(job["skills"]))
            job_skills = normalize_list(raw)
    if not job_skills:  # Fallback to description
        job_skills = extract_skills_from_text(job.get("description", ""))

    resume_skills = []
    if parsed_resume.get("skills"):
        raw = re.split(r"[,\n;]", parsed_resume["skills"])
        resume_skills = normalize_list(raw)
    else:
        extracted = extract_skills_from_text(
            parsed_resume.get("work_experience", "") +
            " " +
            parsed_resume.get("keywords", "")
        )
        resume_skills = normalize_list(extracted)

    if job_skills:
        overlap = len(set(job_skills) & set(resume_skills))
        technical_skill_overlap_score = overlap / len(job_skills)
    else:
        technical_skill_overlap_score = 0.0

    soft_score = soft_skill_score(
        parsed_resume.get("work_experience", "") +
        " " +
        parsed_resume.get("keywords", "")
    )

    years = parsed_resume.get("years_of_experience") or 0.0
    min_exp = job.get("min_experience")
    if min_exp is None:
        exp_score = 1.0
    else:
        if years >= min_exp:
            exp_score = 1.0
        else:
            exp_score = max(0.0, years / min_exp)

    job_keywords = set(normalize_list(re.split(r"[,\n;]", job.get("requirements", "") + " " + job.get("description", ""))))
    resume_keywords = set(normalize_list(re.split(r"[,\n;]", parsed_resume.get("keywords", ""))))
    if job_keywords:
        keyword_overlap = len(job_keywords & resume_keywords)
        keyword_relevance_score = keyword_overlap / len(job_keywords)
    else:
        keyword_relevance_score = 0.0

    final_score = (
        weights["semantic"] * semantic_sim +
        weights["technical_skill_overlap"] * technical_skill_overlap_score +
        weights["soft_skill"] * soft_score +
        weights["experience"] * exp_score +
        weights["keyword_relevance"] * keyword_relevance_score
    )

    final_score_clipped = float(np.clip(final_score, 0.0, 1.0))

    return {
        "resume_id": parsed_resume.get("resume_id"),
        "name": parsed_resume.get("full_name"),
        "semantic_sim": float(semantic_sim),
        "technical_skill_overlap": float(technical_skill_overlap_score),
        "soft_skill": float(soft_score),
        "experience_score": float(exp_score),
        "keyword_relevance": float(keyword_relevance_score),
        "final_score": final_score_clipped,
        "matched_skills": list(set(job_skills) & set(resume_skills)),
        "job_skills": job_skills,
        "resume_skills": resume_skills
    }


def rank_candidates_for_job(job: dict, parsed_resumes: List[dict], top_k=20) -> List[Dict]:
    results = []
    for pr in parsed_resumes:
        score_data = rank_resume_for_job(job, pr)
        results.append(score_data)
    results.sort(key=lambda x: x["final_score"], reverse=True)
    return results[:top_k]