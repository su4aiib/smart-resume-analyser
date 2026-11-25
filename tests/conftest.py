from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

# Isolate the SQLite database for the whole test run (must be set before app imports).
os.environ["RESUME_DB_PATH"] = str(Path(tempfile.mkdtemp()) / "test.db")

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session")
def fixtures() -> Path:
    return FIXTURES


@pytest.fixture(scope="session")
def strong_docx_bytes() -> bytes:
    return (FIXTURES / "strong_resume.docx").read_bytes()


@pytest.fixture(scope="session")
def strong_pdf_bytes() -> bytes:
    return (FIXTURES / "strong_resume.pdf").read_bytes()


@pytest.fixture(scope="session")
def strong_text(strong_docx_bytes: bytes) -> str:
    from app.core.parsers import parse_resume

    return parse_resume("strong_resume.docx", strong_docx_bytes)


@pytest.fixture(scope="session")
def job_description() -> str:
    return (FIXTURES / "sample_job_description.txt").read_text(encoding="utf-8")
