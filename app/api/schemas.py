"""Pydantic request/response models for the HTTP API."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ParseResponse(BaseModel):
    filename: str
    word_count: int
    sections: dict[str, str]
    text: str


class SkillMentionOut(BaseModel):
    skill: str
    category: str
    matched_text: str
    start_char: int
    end_char: int


class CheckOut(BaseModel):
    name: str
    points: float
    max_points: float
    suggestion: str | None


class AnalyzeResponse(BaseModel):
    analysis_id: str
    filename: str
    word_count: int
    score: int = Field(ge=0, le=100)
    checks: list[CheckOut]
    suggestions: list[str]
    skills: dict[str, list[str]]
    mentions: list[SkillMentionOut]


class MatchResponse(BaseModel):
    score_pct: float
    skill_score_pct: float
    text_score_pct: float
    matched_skills: list[str]
    missing_skills: list[str]


class JobOut(BaseModel):
    job_id: str
    title: str
    company: str
    location: str
    score_pct: float
    matched_skills: list[str]
    missing_skills: list[str]
    why: str


class RecommendResponse(BaseModel):
    count: int
    results: list[JobOut]
