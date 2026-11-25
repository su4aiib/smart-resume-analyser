"""Skill extraction using a spaCy PhraseMatcher over a JSON taxonomy.

Matching is token-based and case-insensitive, so "Java" does not match
"JavaScript". Each hit records the matched text and character offsets.
"""

from __future__ import annotations

import json
from collections import defaultdict
from collections.abc import Iterable
from functools import lru_cache
from pathlib import Path

import spacy
from spacy.language import Language
from spacy.matcher import PhraseMatcher

from app.core.config import SKILLS_PATH, SPACY_MODEL
from app.core.models import SkillEntry, SkillHit


def load_entries(path: Path = SKILLS_PATH) -> list[SkillEntry]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return [
        SkillEntry(
            name=item["skill"],
            category=item["category"],
            aliases=tuple(item.get("aliases", [])),
        )
        for item in raw
    ]


class Taxonomy:
    """A compiled skill matcher. Build once and reuse; construction is slow."""

    def __init__(self, entries: Iterable[SkillEntry], nlp: Language | None = None) -> None:
        self.nlp = nlp or spacy.load(SPACY_MODEL)
        self.entries = list(entries)
        self._by_name = {entry.name: entry for entry in self.entries}
        self.matcher = PhraseMatcher(self.nlp.vocab, attr="LOWER")
        for entry in self.entries:
            patterns = [self.nlp.make_doc(alias) for alias in {entry.name, *entry.aliases}]
            self.matcher.add(entry.name, patterns)

    def find(self, text: str) -> list[SkillHit]:
        doc = self.nlp.make_doc(text)
        hits: list[SkillHit] = []
        for match_id, start, end in self.matcher(doc):
            entry = self._by_name[self.nlp.vocab.strings[match_id]]
            span = doc[start:end]
            hits.append(
                SkillHit(
                    skill=entry.name,
                    category=entry.category,
                    matched_text=span.text,
                    start_char=span.start_char,
                    end_char=span.end_char,
                )
            )
        return _keep_longest_non_overlapping(hits)


def _keep_longest_non_overlapping(hits: list[SkillHit]) -> list[SkillHit]:
    """When aliases overlap (e.g. "REST" inside "REST APIs"), keep the longest span."""
    ordered = sorted(hits, key=lambda hit: (hit.start_char, -(hit.end_char - hit.start_char)))
    kept: list[SkillHit] = []
    last_end = -1
    for hit in ordered:
        if hit.start_char >= last_end:
            kept.append(hit)
            last_end = hit.end_char
    return kept


@lru_cache(maxsize=1)
def get_taxonomy() -> Taxonomy:
    return Taxonomy(load_entries())


def extract_skills(text: str, taxonomy: Taxonomy | None = None) -> list[SkillHit]:
    return (taxonomy or get_taxonomy()).find(text)


def skill_names(text: str, taxonomy: Taxonomy | None = None) -> set[str]:
    return {hit.skill for hit in extract_skills(text, taxonomy)}


def group_by_category(hits: Iterable[SkillHit]) -> dict[str, list[str]]:
    grouped: dict[str, set[str]] = defaultdict(set)
    for hit in hits:
        grouped[hit.category].add(hit.skill)
    return {category: sorted(skills) for category, skills in sorted(grouped.items())}
