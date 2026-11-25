"""HTTP routes. Thin layer: validation, error mapping and serialization only."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from functools import lru_cache
from typing import Annotated

import pandas as pd
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.api.schemas import (
    AnalyzeResponse,
    CheckOut,
    JobOut,
    MatchResponse,
    ParseResponse,
    RecommendResponse,
    SkillMentionOut,
)
from app.core.config import DEFAULT_THRESHOLD, DEFAULT_TOP_N, MAX_TOP_N, MAX_UPLOAD_BYTES
from app.core.errors import ResumeError
from app.core.matching import load_jobs, match_resume_to_job, recommend_jobs
from app.core.models import JobRecommendation
from app.core.parsers import parse_resume
from app.core.pipeline import analyze_upload
from app.core.scoring import count_words
from app.core.sections import detect_sections
from app.core.skills import group_by_category
from app.db import connect, save_analysis

router = APIRouter()

STATUS_BY_CODE = {"file_too_large": 413, "too_many_pages": 413}


def _to_http_error(exc: ResumeError) -> HTTPException:
    return HTTPException(
        status_code=STATUS_BY_CODE.get(exc.code, 422),
        detail={"code": exc.code, "message": exc.message},
    )


async def _read_upload(file: UploadFile) -> tuple[str, bytes]:
    # Read one byte past the limit so oversize files are detected without loading them fully.
    content = await file.read(MAX_UPLOAD_BYTES + 1)
    return file.filename or "", content


def get_conn() -> Iterator[sqlite3.Connection]:
    conn = connect()
    try:
        yield conn
    finally:
        conn.close()


@lru_cache(maxsize=1)
def _jobs() -> pd.DataFrame:
    return load_jobs()


def _job_out(rec: JobRecommendation) -> JobOut:
    match = rec.match
    why = (
        f"Matches {len(match.matched_skills)} of "
        f"{len(match.matched_skills) + len(match.missing_skills)} job skills."
    )
    if match.missing_skills:
        why += f" Missing: {', '.join(match.missing_skills)}."
    return JobOut(
        job_id=rec.job_id,
        title=rec.title,
        company=rec.company,
        location=rec.location,
        score_pct=round(match.score * 100, 1),
        matched_skills=list(match.matched_skills),
        missing_skills=list(match.missing_skills),
        why=why,
    )


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/parse", response_model=ParseResponse)
async def parse(file: Annotated[UploadFile, File()]) -> ParseResponse:
    filename, content = await _read_upload(file)
    try:
        text = parse_resume(filename, content)
    except ResumeError as exc:
        raise _to_http_error(exc) from exc
    return ParseResponse(
        filename=filename,
        word_count=count_words(text),
        sections=detect_sections(text),
        text=text,
    )


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(
    file: Annotated[UploadFile, File()],
    conn: Annotated[sqlite3.Connection, Depends(get_conn)],
) -> AnalyzeResponse:
    filename, content = await _read_upload(file)
    try:
        result = analyze_upload(filename, content)
    except ResumeError as exc:
        raise _to_http_error(exc) from exc

    analysis_id = save_analysis(
        conn,
        filename=filename,
        word_count=result.word_count,
        score=result.score.total,
        skills=sorted(result.skill_names),
    )
    return AnalyzeResponse(
        analysis_id=analysis_id,
        filename=filename,
        word_count=result.word_count,
        score=result.score.total,
        checks=[
            CheckOut(
                name=check.name,
                points=round(check.points, 2),
                max_points=check.max_points,
                suggestion=check.suggestion,
            )
            for check in result.score.checks
        ],
        suggestions=result.score.suggestions,
        skills=group_by_category(result.skill_hits),
        mentions=[
            SkillMentionOut(
                skill=hit.skill,
                category=hit.category,
                matched_text=hit.matched_text,
                start_char=hit.start_char,
                end_char=hit.end_char,
            )
            for hit in result.skill_hits
        ],
    )


@router.post("/match", response_model=MatchResponse)
async def match(
    file: Annotated[UploadFile, File()],
    jd_text: Annotated[str, Form()] = "",
) -> MatchResponse:
    if not jd_text.strip():
        raise HTTPException(
            status_code=422,
            detail={"code": "empty_job_description", "message": "Job description is required."},
        )
    filename, content = await _read_upload(file)
    try:
        resume_text = parse_resume(filename, content)
    except ResumeError as exc:
        raise _to_http_error(exc) from exc

    result = match_resume_to_job(resume_text, jd_text)
    return MatchResponse(
        score_pct=round(result.score * 100, 1),
        skill_score_pct=round(result.skill_score * 100, 1),
        text_score_pct=round(result.text_score * 100, 1),
        matched_skills=list(result.matched_skills),
        missing_skills=list(result.missing_skills),
    )


@router.post("/recommend", response_model=RecommendResponse)
async def recommend(
    file: Annotated[UploadFile, File()],
    top_n: Annotated[int, Form(ge=1, le=MAX_TOP_N)] = DEFAULT_TOP_N,
    threshold: Annotated[float, Form(ge=0.0, le=1.0)] = DEFAULT_THRESHOLD,
    location: Annotated[str | None, Form()] = None,
    min_score: Annotated[float | None, Form(ge=0.0, le=1.0)] = None,
) -> RecommendResponse:
    filename, content = await _read_upload(file)
    try:
        resume_text = parse_resume(filename, content)
    except ResumeError as exc:
        raise _to_http_error(exc) from exc

    results = recommend_jobs(
        resume_text,
        _jobs(),
        top_n=top_n,
        threshold=threshold,
        location=location or None,
        min_score=min_score,
    )
    outputs = [_job_out(rec) for rec in results]
    return RecommendResponse(count=len(outputs), results=outputs)
