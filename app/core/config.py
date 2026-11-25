"""Central configuration. All tunable constants live here."""

from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
SKILLS_PATH = DATA_DIR / "skills.json"
JOBS_PATH = DATA_DIR / "jobs.csv"
DB_PATH = Path(os.getenv("RESUME_DB_PATH", str(DATA_DIR / "app.db")))
SPACY_MODEL = "en_core_web_sm"

# Upload limits
MAX_UPLOAD_BYTES = 5 * 1024 * 1024
MAX_PDF_PAGES = 10

# Job matching weights (must sum to 1.0)
SKILL_WEIGHT = 0.6
TEXT_WEIGHT = 0.4

# Recommendations
DEFAULT_TOP_N = 10
MAX_TOP_N = 50
DEFAULT_THRESHOLD = 0.2

# Resume scoring
REQUIRED_SECTIONS = ("summary", "skills", "experience", "education")
TARGET_SKILL_COUNT = 8
TARGET_QUANTIFIED_LINES = 5
MIN_WORDS = 300
MAX_WORDS = 800

ACTION_VERBS = frozenset(
    {
        "achieved",
        "administered",
        "analyzed",
        "architected",
        "automated",
        "built",
        "collaborated",
        "computed",
        "configured",
        "coordinated",
        "created",
        "debugged",
        "decreased",
        "delivered",
        "deployed",
        "designed",
        "developed",
        "directed",
        "drove",
        "enabled",
        "engineered",
        "enhanced",
        "established",
        "evaluated",
        "executed",
        "expanded",
        "facilitated",
        "generated",
        "grew",
        "implemented",
        "improved",
        "increased",
        "initiated",
        "integrated",
        "launched",
        "led",
        "maintained",
        "managed",
        "mentored",
        "migrated",
        "modeled",
        "monitored",
        "negotiated",
        "optimized",
        "orchestrated",
        "organized",
        "owned",
        "partnered",
        "performed",
        "planned",
        "presented",
        "produced",
        "programmed",
        "proposed",
        "reduced",
        "refactored",
        "resolved",
        "researched",
        "reviewed",
        "scaled",
        "streamlined",
        "supervised",
        "taught",
        "tested",
        "trained",
        "transformed",
        "upgraded",
    }
)
