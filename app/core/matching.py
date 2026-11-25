"""Job description matching and job recommendations.

score = SKILL_WEIGHT * skill_overlap + TEXT_WEIGHT * tfidf_cosine
skill_overlap = matched job skills / all job skills (0 if the job lists no known skills)
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.core.config import (
    DEFAULT_THRESHOLD,
    DEFAULT_TOP_N,
    JOBS_PATH,
    MAX_TOP_N,
    SKILL_WEIGHT,
    TEXT_WEIGHT,
)
from app.core.models import JobMatch, JobRecommendation
from app.core.skills import skill_names

REQUIRED_JOB_COLUMNS = ("job_id", "title", "company", "location", "description")


def load_jobs(path: Path = JOBS_PATH) -> pd.DataFrame:
    frame = pd.read_csv(path, dtype=str).fillna("")
    missing = [column for column in REQUIRED_JOB_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"Jobs file is missing columns: {', '.join(missing)}")
    return frame


def text_similarity(resume_text: str, documents: Sequence[str]) -> list[float]:
    """TF-IDF cosine similarity between the resume and each document."""
    if not documents:
        return []
    try:
        matrix = TfidfVectorizer(stop_words="english").fit_transform([resume_text, *documents])
    except ValueError:  # empty vocabulary, e.g. blank input
        return [0.0] * len(documents)
    return cosine_similarity(matrix[0], matrix[1:]).ravel().tolist()


def _build_match(resume_skills: set[str], job_skills: set[str], similarity: float) -> JobMatch:
    if job_skills:
        matched = tuple(sorted(job_skills & resume_skills))
        missing = tuple(sorted(job_skills - resume_skills))
        skill_score = len(matched) / len(job_skills)
    else:
        matched, missing, skill_score = (), (), 0.0

    score = SKILL_WEIGHT * skill_score + TEXT_WEIGHT * similarity
    return JobMatch(
        score=round(score, 4),
        skill_score=round(skill_score, 4),
        text_score=round(similarity, 4),
        matched_skills=matched,
        missing_skills=missing,
    )


def match_resume_to_job(resume_text: str, job_text: str) -> JobMatch:
    resume_skills = skill_names(resume_text)
    job_skills = skill_names(job_text)
    similarity = text_similarity(resume_text, [job_text])[0]
    return _build_match(resume_skills, job_skills, similarity)


def recommend_jobs(
    resume_text: str,
    jobs: pd.DataFrame,
    top_n: int = DEFAULT_TOP_N,
    threshold: float = DEFAULT_THRESHOLD,
    location: str | None = None,
    min_score: float | None = None,
) -> list[JobRecommendation]:
    top_n = max(1, min(top_n, MAX_TOP_N))
    if location:
        jobs = jobs[jobs["location"].str.contains(location, case=False, regex=False)]
    if jobs.empty:
        return []

    resume_skills = skill_names(resume_text)
    rows = jobs.to_dict("records")
    documents = [f"{row['title']} {row['description']}" for row in rows]
    similarities = text_similarity(resume_text, documents)
    cutoff = max(threshold, min_score or 0.0)

    results: list[JobRecommendation] = []
    for row, document, similarity in zip(rows, documents, similarities, strict=True):
        match = _build_match(resume_skills, skill_names(document), similarity)
        if match.score >= cutoff:
            results.append(
                JobRecommendation(
                    job_id=str(row["job_id"]),
                    title=row["title"],
                    company=row["company"],
                    location=row["location"],
                    match=match,
                )
            )

    results.sort(key=lambda result: result.match.score, reverse=True)
    return results[:top_n]
