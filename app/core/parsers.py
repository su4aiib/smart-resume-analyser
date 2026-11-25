"""Convert uploaded PDF/DOCX bytes into plain text."""

from __future__ import annotations

import io
import re
from pathlib import Path

import docx
import pdfplumber

from app.core.config import MAX_PDF_PAGES, MAX_UPLOAD_BYTES
from app.core.errors import ResumeError

SUPPORTED_EXTENSIONS = {".pdf", ".docx"}


def parse_resume(filename: str, content: bytes) -> str:
    """Return normalized plain text for a PDF or DOCX upload.

    Raises ResumeError with a machine-readable `code` on any failure.
    """
    if not content:
        raise ResumeError("empty_file", "Uploaded file is empty.")
    if len(content) > MAX_UPLOAD_BYTES:
        limit_mb = MAX_UPLOAD_BYTES // (1024 * 1024)
        raise ResumeError("file_too_large", f"File exceeds the {limit_mb} MB limit.")

    extension = Path(filename or "").suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        raise ResumeError("unsupported_type", "Only PDF and DOCX files are supported.")

    raw_text = _parse_pdf(content) if extension == ".pdf" else _parse_docx(content)
    text = normalize_text(raw_text)
    if not text:
        raise ResumeError(
            "no_text",
            "No extractable text found. Scanned or image-only documents are not supported.",
        )
    return text


def normalize_text(text: str) -> str:
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.splitlines()]
    joined = "\n".join(lines)
    return re.sub(r"\n{3,}", "\n\n", joined).strip()


def _parse_pdf(content: bytes) -> str:
    try:
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            if len(pdf.pages) > MAX_PDF_PAGES:
                raise ResumeError("too_many_pages", f"PDF exceeds the {MAX_PDF_PAGES}-page limit.")
            pages = [page.extract_text() or "" for page in pdf.pages]
    except ResumeError:
        raise
    except Exception as exc:  # pdfplumber raises several unrelated error types
        raise ResumeError("invalid_file", "Could not read the PDF file.") from exc
    return "\n".join(pages)


def _parse_docx(content: bytes) -> str:
    try:
        document = docx.Document(io.BytesIO(content))
    except Exception as exc:
        raise ResumeError("invalid_file", "Could not read the DOCX file.") from exc

    lines = [paragraph.text for paragraph in document.paragraphs]
    for table in document.tables:
        for row in table.rows:
            lines.extend(cell.text for cell in row.cells)
    return "\n".join(lines)
