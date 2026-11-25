import pytest

from app.core.config import MAX_UPLOAD_BYTES
from app.core.errors import ResumeError
from app.core.parsers import normalize_text, parse_resume


def test_docx_is_parsed(strong_docx_bytes):
    text = parse_resume("strong_resume.docx", strong_docx_bytes)
    assert "Jane Doe" in text
    assert "Experience" in text


def test_pdf_is_parsed(strong_pdf_bytes):
    text = parse_resume("strong_resume.pdf", strong_pdf_bytes)
    assert "jane.doe@example.com" in text
    assert "Kubernetes" in text


def test_unsupported_extension_is_rejected(strong_docx_bytes):
    with pytest.raises(ResumeError) as exc:
        parse_resume("resume.txt", strong_docx_bytes)
    assert exc.value.code == "unsupported_type"


def test_empty_file_is_rejected():
    with pytest.raises(ResumeError) as exc:
        parse_resume("resume.pdf", b"")
    assert exc.value.code == "empty_file"


def test_oversize_file_is_rejected():
    with pytest.raises(ResumeError) as exc:
        parse_resume("resume.pdf", b"0" * (MAX_UPLOAD_BYTES + 1))
    assert exc.value.code == "file_too_large"


def test_blank_pdf_reports_no_text(fixtures):
    with pytest.raises(ResumeError) as exc:
        parse_resume("blank_scanned.pdf", (fixtures / "blank_scanned.pdf").read_bytes())
    assert exc.value.code == "no_text"


def test_corrupt_docx_is_invalid_file():
    with pytest.raises(ResumeError) as exc:
        parse_resume("resume.docx", b"not a real docx")
    assert exc.value.code == "invalid_file"


def test_normalize_text_collapses_whitespace():
    assert normalize_text("  a   b \r\n\n\n\nc  ") == "a b\n\nc"
