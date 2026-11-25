"""SQLite helpers. Stores analysis metadata only: no resume text."""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.core.config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS analyses (
    id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    filename TEXT NOT NULL,
    word_count INTEGER NOT NULL,
    score INTEGER NOT NULL,
    skills TEXT NOT NULL
)
"""


def connect(path: Path = DB_PATH) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    # Each request gets its own connection, so sharing across threads is safe here.
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute(SCHEMA)
    conn.commit()
    return conn


def save_analysis(
    conn: sqlite3.Connection,
    filename: str,
    word_count: int,
    score: int,
    skills: list[str],
) -> str:
    analysis_id = uuid.uuid4().hex
    with conn:
        conn.execute(
            "INSERT INTO analyses (id, created_at, filename, word_count, score, skills) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                analysis_id,
                datetime.now(UTC).isoformat(timespec="seconds"),
                filename,
                word_count,
                score,
                json.dumps(skills),
            ),
        )
    return analysis_id


def get_analysis(conn: sqlite3.Connection, analysis_id: str) -> dict[str, Any] | None:
    row = conn.execute("SELECT * FROM analyses WHERE id = ?", (analysis_id,)).fetchone()
    if row is None:
        return None
    record = dict(row)
    record["skills"] = json.loads(record["skills"])
    return record
