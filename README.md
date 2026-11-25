# Smart Resume Analyzer & Job Recommendation System

Upload a resume (PDF or DOCX) and get:

- Extracted text and detected sections (Summary, Skills, Experience, Education, Projects, Certifications)
- Skills found from a taxonomy of 180+ skills, including aliases (`JS` -> JavaScript, `k8s` -> Kubernetes)
- A 0-100 resume score with a specific suggestion for every lost point
- A match score against a pasted job description, with matched and missing skills
- Ranked job recommendations from a job-postings CSV, each with a "why" explanation

Everything runs offline. No API keys are required.

## Stack

| Layer | Technology |
|---|---|
| Language | Python 3.11+ |
| Parsing | pdfplumber (PDF), python-docx (DOCX) |
| Skill extraction | spaCy `en_core_web_sm` + PhraseMatcher over `data/skills.json` |
| Matching | scikit-learn TF-IDF + cosine similarity |
| Data | pandas (jobs CSV) |
| API | FastAPI + uvicorn, pydantic models |
| Storage | SQLite (standard library `sqlite3`), metadata only |
| UI | Streamlit, calling the API over HTTP |
| Tests / lint | pytest, httpx, ruff |
| Deployment | Docker, docker-compose |

## Setup (Windows PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev]"
python -m spacy download en_core_web_sm
```

On macOS or Linux, use `source .venv/bin/activate` instead of the activate script.

## Running

Start the API (terminal 1):

```powershell
python -m uvicorn app.api.main:app --reload
```

Open the interactive docs at http://localhost:8000/docs.

Start the UI (terminal 2):

```powershell
streamlit run ui/streamlit_app.py
```

The UI expects the API at `http://localhost:8000`. Set `API_URL` to change this.

### Docker

```powershell
docker compose up --build
```

- API: http://localhost:8000
- UI: http://localhost:8501

## Testing and linting

```powershell
pytest
pytest --cov=app.core --cov-report=term-missing
ruff check .
ruff format --check .
```

## API

All file endpoints take `multipart/form-data` with a `file` field (PDF or DOCX, 5 MB max, 10 pages max for PDFs).

Errors return a JSON body of the form `{"detail": {"code": "...", "message": "..."}}`.

| Code | Meaning | HTTP status |
|---|---|---|
| `unsupported_type` | File is not PDF or DOCX | 422 |
| `empty_file` | File has no content | 422 |
| `invalid_file` | File could not be read | 422 |
| `no_text` | No extractable text (for example, a scanned PDF) | 422 |
| `file_too_large` | Over 5 MB | 413 |
| `too_many_pages` | PDF over 10 pages | 413 |
| `empty_job_description` | `/match` called with blank `jd_text` | 422 |

### `GET /health`

```json
{"status": "ok"}
```

### `POST /parse`

Form field: `file`.

```bash
curl -F "file=@resume.pdf" http://localhost:8000/parse
```

```json
{
  "filename": "resume.pdf",
  "word_count": 230,
  "sections": {"summary": "...", "skills": "...", "experience": "..."},
  "text": "Jane Doe\n..."
}
```

### `POST /analyze`

Form field: `file`. Stores an analysis record (ID, timestamp, score, skill names, word count, filename). Resume text is not stored.

```bash
curl -F "file=@resume.pdf" http://localhost:8000/analyze
```

```json
{
  "analysis_id": "3f9c...",
  "filename": "resume.pdf",
  "word_count": 230,
  "score": 96,
  "checks": [
    {"name": "contact_info", "points": 10.0, "max_points": 10.0, "suggestion": null},
    {"name": "length", "points": 11.5, "max_points": 15.0, "suggestion": "Resume is 230 words; aim for 300-800."}
  ],
  "suggestions": ["Resume is 230 words; aim for 300-800."],
  "skills": {"cloud_devops": ["Docker", "Kubernetes"], "languages": ["Java", "Python"]},
  "mentions": [
    {"skill": "Python", "category": "languages", "matched_text": "Python", "start_char": 120, "end_char": 126}
  ]
}
```

### `POST /match`

Form fields: `file`, `jd_text`.

```bash
curl -F "file=@resume.pdf" -F "jd_text=Python developer with FastAPI and Docker" http://localhost:8000/match
```

```json
{
  "score_pct": 71.3,
  "skill_score_pct": 100.0,
  "text_score_pct": 28.3,
  "matched_skills": ["Docker", "FastAPI", "Python"],
  "missing_skills": []
}
```

### `POST /recommend`

Form fields (all optional except `file`):

| Field | Default | Range |
|---|---|---|
| `top_n` | 10 | 1-50 |
| `threshold` | 0.2 | 0.0-1.0 |
| `location` | none | substring match, case-insensitive |
| `min_score` | none | 0.0-1.0 (applied with `threshold`, the higher wins) |

```bash
curl -F "file=@resume.pdf" -F "top_n=3" -F "location=remote" http://localhost:8000/recommend
```

```json
{
  "count": 3,
  "results": [
    {
      "job_id": "J002",
      "title": "Data Scientist",
      "company": "Pinecrest Labs",
      "location": "Remote",
      "score_pct": 48.2,
      "matched_skills": ["Python", "SQL"],
      "missing_skills": ["A/B Testing", "Tableau"],
      "why": "Matches 2 of 4 job skills. Missing: A/B Testing, Tableau."
    }
  ]
}
```

## Scoring

### Resume score (0-100)

| Check | Max | How it is scored |
|---|---|---|
| Contact info | 10 | 5 for an email address, 5 for a phone number (10+ digits) |
| Required sections | 20 | 5 each for Summary, Skills, Experience, Education |
| Skill count | 20 | Proportional to distinct skills, full marks at 8 |
| Quantified achievements | 20 | Proportional to lines with numbers or %, full marks at 5 |
| Action verbs | 15 | Share of experience bullets that start with a verb from `ACTION_VERBS` |
| Length | 15 | Full marks for 300-800 words, scaled outside that range |

Each check reports points earned and, when it loses points, a suggestion.

### Job match

```
score = 0.6 * skill_overlap + 0.4 * tfidf_cosine
skill_overlap = matched job skills / all job skills
```

The weights and thresholds live in `app/core/config.py`. If a job description contains no known skills, `skill_overlap` is 0 and the score comes from text similarity alone.

## Project layout

```
app/
  core/          Pure Python logic. No FastAPI or Streamlit imports.
    parsers.py   PDF/DOCX -> text, with upload validation
    sections.py  Section detection
    skills.py    Taxonomy loading and PhraseMatcher extraction
    scoring.py   Resume rubric
    matching.py  Job match and recommendations
    pipeline.py  parse -> sections -> skills -> score
    config.py    All constants and weights
    models.py    Dataclasses
    errors.py    ResumeError with machine-readable codes
  api/           FastAPI app, routes, pydantic schemas
  db.py          SQLite helpers
data/
  skills.json    Skill taxonomy (name, category, aliases)
  jobs.csv       Sample job postings (fictional)
ui/
  streamlit_app.py
tests/           pytest suite; fixtures in tests/fixtures (fictional data)
```

To add a skill, add an entry to `data/skills.json`. Matching is case-insensitive and token-based, so `Java` does not match `JavaScript`. To use your own jobs, replace `data/jobs.csv`. It must include `job_id,title,company,location,description`.

## Limitations

- **Skill matching is taxonomy-based.** Skills missing from `skills.json` are not detected. Single-letter skills such as `C` and `R` are excluded because they match too many ordinary words.
- **Section detection uses header lines.** Resumes with unusual headers may be scored lower on the sections check. Add aliases to `SECTION_ALIASES` in `app/core/sections.py`.
- **Scanned PDFs are not supported.** There is no OCR, so image-only PDFs return `no_text`.
- **TF-IDF is lexical.** Synonyms that share no words with the job text are not recognized. Embeddings would improve this at the cost of a model dependency.
- **Job data is a static CSV.** Live job sources are not included.
- **The SQLite store is for single-instance use.** Use a proper database for multi-instance deployment.

## Privacy

- Uploaded files are processed in memory and not written to disk.
- The database stores only analysis metadata (ID, timestamp, filename, word count, score, skill names). Resume text is never stored.
- The application makes no outbound network calls at runtime.
