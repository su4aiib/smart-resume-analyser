"""FastAPI application entry point.

Run locally:  python -m uvicorn app.api.main:app --reload
Docs:         http://localhost:8000/docs
"""

from __future__ import annotations

from fastapi import FastAPI

from app.api.routes import router

app = FastAPI(
    title="Smart Resume Analyzer & Job Recommendation API",
    version="0.1.0",
    description="Parse resumes, extract skills, score resumes and recommend jobs.",
)
app.include_router(router)
