"""Plain dataclasses shared across the core modules. No framework imports here."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SkillEntry:
    name: str
    category: str
    aliases: tuple[str, ...] = ()


@dataclass(frozen=True)
class SkillHit:
    skill: str
    category: str
    matched_text: str
    start_char: int
    end_char: int


@dataclass(frozen=True)
class CheckResult:
    name: str
    points: float
    max_points: float
    suggestion: str | None = None

    @property
    def passed(self) -> bool:
        return self.points >= self.max_points


@dataclass(frozen=True)
class ResumeScore:
    total: int
    checks: tuple[CheckResult, ...]

    @property
    def suggestions(self) -> list[str]:
        return [c.suggestion for c in self.checks if c.suggestion]


@dataclass(frozen=True)
class JobMatch:
    score: float  # 0..1, combined score
    skill_score: float  # 0..1, share of job skills found in resume
    text_score: float  # 0..1, TF-IDF cosine similarity
    matched_skills: tuple[str, ...]
    missing_skills: tuple[str, ...]


@dataclass(frozen=True)
class JobRecommendation:
    job_id: str
    title: str
    company: str
    location: str
    match: JobMatch


@dataclass(frozen=True)
class AnalysisResult:
    filename: str
    text: str
    word_count: int
    sections: dict[str, str]
    skill_hits: tuple[SkillHit, ...]
    score: ResumeScore

    @property
    def skill_names(self) -> set[str]:
        return {hit.skill for hit in self.skill_hits}
