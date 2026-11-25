"""Detect standard resume sections by header lines.

Text before the first recognized header is returned under the key "header"
(usually name and contact details).
"""

from __future__ import annotations

import re

SECTION_ALIASES: dict[str, tuple[str, ...]] = {
    "summary": (
        "summary",
        "professional summary",
        "profile",
        "objective",
        "career objective",
        "about me",
    ),
    "skills": (
        "skills",
        "technical skills",
        "core skills",
        "core competencies",
        "competencies",
        "key skills",
        "technologies",
    ),
    "experience": (
        "experience",
        "work experience",
        "professional experience",
        "employment history",
        "employment",
        "work history",
    ),
    "education": ("education", "academic background", "academics", "qualifications"),
    "projects": ("projects", "personal projects", "academic projects", "key projects"),
    "certifications": (
        "certifications",
        "certificates",
        "licenses",
        "licences",
        "certifications and licenses",
    ),
}

_HEADER_TO_SECTION = {
    alias: section for section, aliases in SECTION_ALIASES.items() for alias in aliases
}
_WHITESPACE_RE = re.compile(r"\s+")


def _header_key(line: str) -> str:
    return _WHITESPACE_RE.sub(" ", line.strip().rstrip(":").strip().lower())


def detect_sections(text: str) -> dict[str, str]:
    """Map canonical section name -> section body. Empty sections are omitted."""
    buckets: dict[str, list[str]] = {}
    current = "header"

    for line in text.splitlines():
        key = _header_key(line)
        if key in _HEADER_TO_SECTION:
            current = _HEADER_TO_SECTION[key]
            buckets.setdefault(current, [])
            continue
        buckets.setdefault(current, []).append(line)

    sections = {name: "\n".join(lines).strip() for name, lines in buckets.items()}
    return {name: body for name, body in sections.items() if body}
