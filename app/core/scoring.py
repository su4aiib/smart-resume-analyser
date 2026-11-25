"""Transparent resume rubric. Weights sum to 100.

Check                      Max
contact info (email/phone)  10  (5 + 5)
required sections           20  (5 per section, 4 sections)
skill count                 20  (scaled to TARGET_SKILL_COUNT)
quantified achievements     20  (scaled to TARGET_QUANTIFIED_LINES lines)
action verbs in experience  15  (share of bullets starting with a verb)
length                      15  (full marks within MIN_WORDS..MAX_WORDS)
"""

from __future__ import annotations

import re

from app.core.config import (
    ACTION_VERBS,
    MAX_WORDS,
    MIN_WORDS,
    REQUIRED_SECTIONS,
    TARGET_QUANTIFIED_LINES,
    TARGET_SKILL_COUNT,
)
from app.core.models import CheckResult, ResumeScore

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_CANDIDATE_RE = re.compile(r"\+?\d[\d\s().-]{8,}\d")
NUMBER_RE = re.compile(r"\d|%")
WORD_RE = re.compile(r"\b\w+\b")
BULLET_RE = re.compile(r"^\s*[•\-\*–▪●]\s*")
FIRST_WORD_RE = re.compile(r"[A-Za-z]+")


def count_words(text: str) -> int:
    return len(WORD_RE.findall(text))


def _has_phone(text: str) -> bool:
    for match in PHONE_CANDIDATE_RE.finditer(text):
        if sum(ch.isdigit() for ch in match.group()) >= 10:
            return True
    return False


def check_contact(text: str) -> CheckResult:
    has_email = bool(EMAIL_RE.search(text))
    has_phone = _has_phone(text)
    points = (5.0 if has_email else 0.0) + (5.0 if has_phone else 0.0)
    missing = [label for label, ok in (("email", has_email), ("phone number", has_phone)) if not ok]
    suggestion = (
        f"Add your {' and '.join(missing)} to the header so recruiters can reach you."
        if missing
        else None
    )
    return CheckResult("contact_info", points, 10.0, suggestion)


def check_sections(sections: dict[str, str]) -> CheckResult:
    missing = [name for name in REQUIRED_SECTIONS if name not in sections]
    points = 5.0 * (len(REQUIRED_SECTIONS) - len(missing))
    suggestion = (
        f"Add missing sections: {', '.join(name.title() for name in missing)}." if missing else None
    )
    return CheckResult("required_sections", points, 20.0, suggestion)


def check_skill_count(skill_names: set[str]) -> CheckResult:
    count = len(skill_names)
    points = min(count / TARGET_SKILL_COUNT, 1.0) * 20.0
    suggestion = (
        f"Only {count} skills detected; list at least {TARGET_SKILL_COUNT} relevant skills."
        if points < 20.0
        else None
    )
    return CheckResult("skill_count", points, 20.0, suggestion)


def check_quantified(text: str) -> CheckResult:
    count = sum(1 for line in text.splitlines() if NUMBER_RE.search(line))
    points = min(count / TARGET_QUANTIFIED_LINES, 1.0) * 20.0
    suggestion = (
        f"Only {count} lines contain numbers. Quantify results, e.g. 'reduced latency by 30%'."
        if points < 20.0
        else None
    )
    return CheckResult("quantified_achievements", points, 20.0, suggestion)


def check_action_verbs(experience_text: str) -> CheckResult:
    lines = [line.strip() for line in experience_text.splitlines() if line.strip()]
    bullets = [BULLET_RE.sub("", line) for line in lines if BULLET_RE.match(line)]
    candidates = bullets or lines
    if not candidates:
        return CheckResult(
            "action_verbs", 0.0, 15.0, "Add an Experience section with bullet points."
        )

    verb_starts = 0
    for candidate in candidates:
        match = FIRST_WORD_RE.match(candidate)
        if match and match.group().lower() in ACTION_VERBS:
            verb_starts += 1

    points = verb_starts / len(candidates) * 15.0
    suggestion = (
        f"Only {verb_starts} of {len(candidates)} experience lines start with an action verb "
        "(e.g., Led, Built, Improved)."
        if points < 15.0
        else None
    )
    return CheckResult("action_verbs", points, 15.0, suggestion)


def check_length(text: str) -> CheckResult:
    words = count_words(text)
    if MIN_WORDS <= words <= MAX_WORDS:
        points = 15.0
    elif words < MIN_WORDS:
        points = 15.0 * words / MIN_WORDS
    else:
        points = max(0.0, 15.0 * (1 - (words - MAX_WORDS) / MAX_WORDS))
    suggestion = (
        f"Resume is {words} words; aim for {MIN_WORDS}-{MAX_WORDS}." if points < 15.0 else None
    )
    return CheckResult("length", points, 15.0, suggestion)


def score_resume(text: str, sections: dict[str, str], skill_names: set[str]) -> ResumeScore:
    checks = (
        check_contact(text),
        check_sections(sections),
        check_skill_count(skill_names),
        check_quantified(text),
        check_action_verbs(sections.get("experience", "")),
        check_length(text),
    )
    total = round(sum(check.points for check in checks))
    return ResumeScore(total=total, checks=checks)
