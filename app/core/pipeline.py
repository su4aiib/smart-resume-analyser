"""End-to-end resume analysis: parse -> sections -> skills -> score."""

from __future__ import annotations

from app.core.models import AnalysisResult
from app.core.parsers import parse_resume
from app.core.scoring import count_words, score_resume
from app.core.sections import detect_sections
from app.core.skills import Taxonomy, extract_skills


def analyze_text(filename: str, text: str, taxonomy: Taxonomy | None = None) -> AnalysisResult:
    sections = detect_sections(text)
    hits = tuple(extract_skills(text, taxonomy))
    score = score_resume(text, sections, {hit.skill for hit in hits})
    return AnalysisResult(
        filename=filename,
        text=text,
        word_count=count_words(text),
        sections=sections,
        skill_hits=hits,
        score=score,
    )


def analyze_upload(
    filename: str, content: bytes, taxonomy: Taxonomy | None = None
) -> AnalysisResult:
    text = parse_resume(filename, content)
    return analyze_text(filename, text, taxonomy)
