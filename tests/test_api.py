import pytest
from fastapi.testclient import TestClient

from app.api.main import app

client = TestClient(app)


@pytest.fixture
def docx_upload(strong_docx_bytes):
    return {"file": ("strong_resume.docx", strong_docx_bytes, "application/octet-stream")}


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_parse_returns_text_and_sections(docx_upload):
    response = client.post("/parse", files=docx_upload)
    assert response.status_code == 200
    body = response.json()
    assert "experience" in body["sections"]
    assert body["word_count"] > 100


def test_analyze_returns_score_and_saves(docx_upload):
    response = client.post("/analyze", files=docx_upload)
    assert response.status_code == 200
    body = response.json()
    assert 0 <= body["score"] <= 100
    assert len(body["checks"]) == 6
    assert "Python" in body["skills"]["languages"]
    assert body["analysis_id"]
    assert all("start_char" in m for m in body["mentions"])
    # Resume text must not be stored; only metadata lives in the DB.


def test_analyze_rejects_unsupported_type():
    response = client.post("/analyze", files={"file": ("resume.txt", b"hello", "text/plain")})
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "unsupported_type"


def test_analyze_rejects_oversize_upload():
    from app.core.config import MAX_UPLOAD_BYTES

    payload = b"0" * (MAX_UPLOAD_BYTES + 10)
    response = client.post("/analyze", files={"file": ("resume.pdf", payload, "application/pdf")})
    assert response.status_code == 413
    assert response.json()["detail"]["code"] == "file_too_large"


def test_analyze_rejects_scanned_pdf(fixtures):
    data = (fixtures / "blank_scanned.pdf").read_bytes()
    response = client.post("/analyze", files={"file": ("scan.pdf", data, "application/pdf")})
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "no_text"


def test_match_returns_scores(docx_upload, job_description):
    response = client.post("/match", files=docx_upload, data={"jd_text": job_description})
    assert response.status_code == 200
    body = response.json()
    assert body["score_pct"] > 0
    assert "Python" in body["matched_skills"]


def test_match_requires_job_description(docx_upload):
    response = client.post("/match", files=docx_upload, data={"jd_text": "   "})
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "empty_job_description"


def test_recommend_returns_ranked_jobs(docx_upload):
    response = client.post("/recommend", files=docx_upload, data={"top_n": "5", "threshold": "0.0"})
    assert response.status_code == 200
    body = response.json()
    assert body["count"] == len(body["results"]) <= 5
    assert all(job["why"] for job in body["results"])


def test_recommend_validates_top_n(docx_upload):
    response = client.post("/recommend", files=docx_upload, data={"top_n": "500"})
    assert response.status_code == 422


def test_recommend_location_filter(docx_upload):
    response = client.post(
        "/recommend",
        files=docx_upload,
        data={"threshold": "0.0", "location": "Springfield"},
    )
    assert response.status_code == 200
    assert all("springfield" in job["location"].lower() for job in response.json()["results"])
