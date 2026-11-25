"""Streamlit front end. Calls the FastAPI service over HTTP.

Run:  streamlit run ui/streamlit_app.py
Set API_URL if the API is not at http://localhost:8000.
"""

from __future__ import annotations

import html
import os

import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://localhost:8000").rstrip("/")
MIME_TYPES = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root {
  --accent: #2563eb;
  --accent-hover: #1d4ed8;
  --accent-soft: #eff6ff;
  --line: #dbe3ef;
  --card-shadow: 0 1px 2px rgba(15, 23, 42, .05), 0 10px 30px -14px rgba(15, 23, 42, .18);
}

.stApp, .stApp p, .stApp label, .stApp li, .stApp h1, .stApp h2, .stApp h3, .stApp h4,
.stApp button, .stApp textarea, .stApp input, .stApp [data-testid="stMetricValue"],
.stApp [data-testid="stMetricLabel"], .stApp [data-testid="stTab"],
.stApp [data-testid="stProgress"], .stApp [data-testid="stCaptionContainer"],
.stApp [data-testid="stWidgetLabel"], .stApp [data-testid="stMarkdownContainer"],
.stApp .chip, .stApp .ring-value {
  font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', sans-serif;
}
.stApp {
  background:
    radial-gradient(900px 480px at 12% -5%, #e0ecff 0%, transparent 60%),
    radial-gradient(900px 480px at 92% 0%, #eef4ff 0%, transparent 60%),
    #f5f7fb;
}
[data-testid="stHeader"] { background: transparent; }

/* Text is always black on the light page. */
.stApp p, .stApp label, .stApp li, .stApp h1, .stApp h2, .stApp h3, .stApp h4,
.stApp h5, .stApp h6, .stApp strong, .stApp b, .stApp small,
.stApp [data-testid="stWidgetLabel"], .stApp [data-testid="stWidgetLabel"] *,
.stApp [data-testid="stMetricLabel"], .stApp [data-testid="stMetricValue"],
.stApp [data-testid="stMetricDelta"], .stApp [data-testid="stTab"],
.stApp [data-testid="stProgress"] *, .stApp [data-testid="stFileUploaderFileName"],
.stApp [data-testid="stFileUploaderFileData"], .stApp [data-testid="stFileUploaderFileData"] *,
.stApp textarea, .stApp input {
  color: #000 !important;
}
.stApp input::placeholder, .stApp textarea::placeholder { color: #64748b !important; }

.block-container { padding-top: 3rem; max-width: 1100px; }
@keyframes fadeUp {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: none; }
}

/* Hero text sits in a card. */
.tg-title {
  text-align: center; margin: 0 auto 2rem; max-width: 760px;
  background: #fff; border: 1px solid var(--line); border-radius: 20px;
  padding: 2rem 2.2rem; box-shadow: var(--card-shadow);
  animation: fadeUp .6s ease both;
}
.tg-title h1 {
  font-size: 2.6rem; font-weight: 800; letter-spacing: -.02em; line-height: 1.15;
  color: #000; margin: 0 0 .7rem;
}
.tg-title mark {
  background: var(--accent-soft); color: #000; padding: .02em .28em; border-radius: 8px;
}
.tg-title p { color: #000; font-size: 1.1rem; margin: 0; }

/* Every bordered box (results, job cards) is a white card. */
[data-testid="stVerticalBlockBorderWrapper"] > div > div {
  background: #fff; border: 1px solid var(--line) !important; border-radius: 18px;
  box-shadow: var(--card-shadow); padding: 1.1rem 1.25rem;
}

/* Captions become small label boxes. */
[data-testid="stCaptionContainer"] {
  display: inline-block; background: #fff; border: 1px solid var(--line);
  border-radius: 999px; padding: .35rem .9rem; margin: .25rem 0 .5rem;
  box-shadow: 0 1px 2px rgba(15, 23, 42, .04);
}
[data-testid="stCaptionContainer"] p { margin: 0; }

/* Upload area */
[data-testid="stFileUploader"] { max-width: 820px; margin: 0 auto; }
[data-testid="stFileUploader"] section {
  background: #fff !important; border: 2px dashed #93b4f5 !important;
  border-radius: 22px !important;
  box-shadow: var(--card-shadow);
  min-height: 380px; padding: 3rem 2rem !important;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  transition: border-color .2s ease, box-shadow .2s ease, background .2s ease;
}
[data-testid="stFileUploader"] section:hover {
  border-color: var(--accent) !important; background: #fbfdff !important;
  box-shadow: 0 18px 40px -20px rgba(37, 99, 235, .35);
}
[data-testid="stFileUploader"] section::before {
  content: "Drop your resume here";
  color: #000; font-size: 1.2rem; font-weight: 600; margin-bottom: .4rem;
}
[data-testid="stFileUploader"] section::after {
  content: "PDF or DOCX"; color: #000; font-size: .95rem; margin-bottom: 1.4rem;
  background: var(--accent-soft); border-radius: 999px; padding: .25rem .8rem;
}
[data-testid="stFileUploaderDropzoneInstructions"] { display: none !important; }
[data-testid="stFileUploader"] label { font-size: 1.15rem; font-weight: 600; }
[data-testid="stFileUploaderFile"] {
  background: var(--accent-soft); border: 1px solid #bfd4ff; border-radius: 14px;
  padding: .6rem .9rem;
}

/* Buttons */
.stButton button[kind="primary"], button[data-testid="stBaseButton-primary"],
[data-testid="stFileUploader"] section button {
  background: var(--accent) !important; color: #fff !important; border: none !important;
  border-radius: 12px !important; padding: .7rem 1.6rem !important;
  font-size: 1rem !important; font-weight: 600 !important;
  box-shadow: 0 6px 16px -6px rgba(37, 99, 235, .6);
  transition: transform .15s ease, background .15s ease, box-shadow .15s ease;
}
.stButton button[kind="primary"]:hover, button[data-testid="stBaseButton-primary"]:hover,
[data-testid="stFileUploader"] section button:hover {
  background: var(--accent-hover) !important; transform: translateY(-1px);
  box-shadow: 0 10px 22px -8px rgba(37, 99, 235, .7);
}
.stButton button[kind="primary"]:active, button[data-testid="stBaseButton-primary"]:active,
[data-testid="stFileUploader"] section button:active {
  transform: translateY(1px) scale(.98);
}
.stButton button[kind="secondary"], button[data-testid="stBaseButton-secondary"] {
  background: #fff !important; color: #000 !important; border: 1px solid #cbd5e1 !important;
  border-radius: 12px !important; font-weight: 600 !important;
  box-shadow: 0 1px 2px rgba(15, 23, 42, .06);
  transition: transform .15s ease, border-color .15s ease, background .15s ease;
}
.stButton button[kind="secondary"]:hover, button[data-testid="stBaseButton-secondary"]:hover {
  background: var(--accent-soft) !important; border-color: var(--accent) !important;
  transform: translateY(-1px);
}

/* Tabs as a segmented control */
[data-baseweb="tab-list"] {
  background: #e9eef7; border-radius: 14px; padding: 4px; gap: 4px;
  width: fit-content; max-width: 100%; margin-bottom: 1rem;
}
[data-baseweb="tab-highlight"], [data-baseweb="tab-border"] { display: none !important; }
[data-baseweb="tab"] {
  border-radius: 10px !important; padding: .55rem 1.1rem !important;
  transition: background .15s ease;
}
[data-baseweb="tab"][aria-selected="true"] {
  background: #fff; box-shadow: 0 2px 8px -4px rgba(15, 23, 42, .25);
}
[data-baseweb="tab"]:hover { background: rgba(255, 255, 255, .6); }

/* Text inputs as rounded boxes */
[data-baseweb="textarea"], [data-baseweb="input"] {
  background: #fff !important; border: 1px solid #cbd5e1 !important;
  border-radius: 12px !important; box-shadow: 0 1px 2px rgba(15, 23, 42, .04);
}
[data-baseweb="textarea"]:focus-within, [data-baseweb="input"]:focus-within {
  border-color: var(--accent) !important; box-shadow: 0 0 0 3px rgba(37, 99, 235, .18) !important;
}
.stApp textarea, .stApp input { background: transparent !important; }

/* Analysis visuals */
.ring-wrap { position: relative; width: 150px; height: 150px; margin: .3rem auto 0; }
.ring {
  width: 150px; height: 150px; border-radius: 50%;
  background: conic-gradient(var(--accent) calc(var(--p) * 1%), #e2e8f0 0);
  -webkit-mask: radial-gradient(farthest-side,
    transparent calc(100% - 14px), #000 calc(100% - 13px));
          mask: radial-gradient(farthest-side,
    transparent calc(100% - 14px), #000 calc(100% - 13px));
}
.ring-value {
  position: absolute; inset: 0; display: flex; flex-direction: column;
  align-items: center; justify-content: center; font-size: 2.1rem; font-weight: 700;
}
.ring-value small { font-size: .8rem; font-weight: 500; }

.chip {
  display: inline-block; border-radius: 999px; padding: .2rem .75rem; margin: .15rem .3rem .15rem 0;
  font-size: .85rem; font-weight: 500; border: 1px solid transparent;
}
.chip-skill { background: #eef2ff; color: #3730a3; border-color: #c7d2fe; }
.chip-ok { background: #ecfdf5; color: #065f46; border-color: #a7f3d0; }
.chip-miss { background: #fef2f2; color: #991b1b; border-color: #fecaca; }
.muted { font-style: italic; }

@media (max-width: 640px) {
  .tg-title { padding: 1.4rem 1.1rem; }
  .tg-title h1 { font-size: 2rem; }
  .tg-title p { font-size: 1rem; }
  [data-testid="stFileUploader"] section { min-height: 300px; padding: 2rem 1rem !important; }
}
</style>
"""

HERO = """
<div class="tg-title">
  <h1><mark>Smart Resume Analyzer:</mark> Your Resume, Decoded in Seconds</h1>
  <p>Score your resume, see its skills, and match it to any job.</p>
</div>
"""


def chips(items: list[str], css_class: str) -> str:
    if not items:
        return '<span class="muted">none</span>'
    return "".join(f'<span class="chip {css_class}">{html.escape(i)}</span>' for i in items)


def ring_html(percent: float, caption: str) -> str:
    value = max(0.0, min(100.0, float(percent)))
    return (
        f'<div class="ring-wrap"><div class="ring" style="--p:{value:.1f}"></div>'
        f'<div class="ring-value">{value:.0f}<small>{html.escape(caption)}</small></div></div>'
    )


def call_api(path: str, data: dict | None = None) -> dict | None:
    extension = "." + uploaded.name.rsplit(".", 1)[-1].lower()
    files = {
        "file": (
            uploaded.name,
            uploaded.getvalue(),
            MIME_TYPES.get(extension, "application/octet-stream"),
        )
    }
    try:
        response = requests.post(f"{API_URL}{path}", files=files, data=data, timeout=60)
    except requests.RequestException as exc:
        st.error(f"Could not reach the API at {API_URL}: {exc}")
        return None
    if response.status_code != 200:
        detail = response.json().get("detail", "Request failed.")
        message = detail.get("message", str(detail)) if isinstance(detail, dict) else str(detail)
        st.error(message)
        return None
    return response.json()


st.set_page_config(page_title="Smart Resume Analyzer", page_icon="📄", layout="wide")
st.markdown(CSS, unsafe_allow_html=True)
st.markdown(HERO, unsafe_allow_html=True)

uploaded = st.file_uploader(
    "Upload your resume",
    type=["pdf", "docx"],
)
st.caption("PDF or DOCX · up to 5 MB · up to 10 pages · processed in memory, never stored")
if uploaded is None:
    st.stop()

if st.session_state.get("announced_upload") != uploaded.name:
    st.toast(f"Resume uploaded: {uploaded.name}", icon="✅")
    st.session_state["announced_upload"] = uploaded.name

tab_analyze, tab_match, tab_recommend = st.tabs(
    ["🔍 Analyze my resume", "🎯 Match a job", "💼 Recommended jobs"]
)

with tab_analyze:
    if st.button("Analyze resume", type="primary", key="analyze"):
        with st.spinner("Reading your resume..."):
            result = call_api("/analyze")
        if result:
            score = result["score"]
            if score >= 90:
                st.balloons()
            verdict = (
                "Excellent"
                if score >= 85
                else "Strong"
                if score >= 70
                else "Good start"
                if score >= 50
                else "Needs work"
            )
            with st.container(border=True):
                col_score, col_details = st.columns([1, 2])
                with col_score:
                    st.markdown(ring_html(score, "score"), unsafe_allow_html=True)
                    st.markdown(
                        f"<p style='text-align:center'><b>{verdict}</b></p>",
                        unsafe_allow_html=True,
                    )
                with col_details:
                    skill_total = sum(len(skills) for skills in result["skills"].values())
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Words", result["word_count"])
                    m2.metric("Skills found", skill_total)
                    m3.metric("Tips", len(result["suggestions"]))
                    st.markdown("#### 📋 Score breakdown")
                    for check in result["checks"]:
                        label = check["name"].replace("_", " ").title()
                        fraction = (
                            check["points"] / check["max_points"] if check["max_points"] else 0.0
                        )
                        st.progress(
                            min(max(fraction, 0.0), 1.0),
                            text=f"{label} · {check['points']:.0f}/{check['max_points']:.0f}",
                        )

            with st.container(border=True):
                if result["suggestions"]:
                    st.markdown("#### 💡 How to earn more points")
                    for suggestion in result["suggestions"]:
                        st.markdown(f"- {suggestion}")

                st.markdown("#### 🧠 Skills found")
                if result["skills"]:
                    for category, skills in result["skills"].items():
                        st.markdown(f"**{category.replace('_', ' ').title()}**")
                        st.markdown(chips(skills, "chip-skill"), unsafe_allow_html=True)
                else:
                    st.caption("No skills from the taxonomy were detected in this resume.")

with tab_match:
    job_text = st.text_area(
        "Job description",
        height=200,
        placeholder="Paste the job description here...",
    )
    if st.button("Match my resume", key="match", type="primary"):
        if not job_text.strip():
            st.warning("Paste a job description first.")
        else:
            with st.spinner("Comparing..."):
                result = call_api("/match", data={"jd_text": job_text})
            if result:
                if result["score_pct"] >= 70:
                    st.balloons()
                with st.container(border=True):
                    col_ring, col_bars = st.columns([1, 2])
                    with col_ring:
                        st.markdown(ring_html(result["score_pct"], "match"), unsafe_allow_html=True)
                    with col_bars:
                        st.progress(
                            min(result["skill_score_pct"] / 100, 1.0),
                            text=f"Skill overlap · {result['skill_score_pct']}%",
                        )
                        st.progress(
                            min(result["text_score_pct"] / 100, 1.0),
                            text=f"Text similarity · {result['text_score_pct']}%",
                        )
                with st.container(border=True):
                    st.markdown("#### ✅ Matched skills")
                    st.markdown(chips(result["matched_skills"], "chip-ok"), unsafe_allow_html=True)
                    st.markdown("#### ❌ Missing skills")
                    st.markdown(
                        chips(result["missing_skills"], "chip-miss"), unsafe_allow_html=True
                    )

with tab_recommend:
    col_a, col_b, col_c = st.columns(3)
    top_n = col_a.slider("Number of jobs", 1, 50, 10)
    threshold = col_b.slider("Minimum score", 0.0, 1.0, 0.2, 0.05)
    location = col_c.text_input("Location contains", placeholder="e.g. Remote")
    if st.button("Find matching jobs", key="recommend", type="primary"):
        form = {"top_n": top_n, "threshold": threshold}
        if location.strip():
            form["location"] = location.strip()
        with st.spinner("Ranking jobs..."):
            result = call_api("/recommend", data=form)
        if result:
            if result["count"] == 0:
                st.info(
                    "No jobs met the minimum score. Lower the slider or clear the location filter."
                )
            else:
                st.markdown(f"**{result['count']}** matching jobs, best fit first")
            for job in result["results"]:
                with st.container(border=True):
                    st.markdown(f"**{job['title']}** · {job['company']}")
                    st.caption(f"📍 {job['location']}")
                    st.progress(
                        min(job["score_pct"] / 100, 1.0),
                        text=f"Match · {job['score_pct']}%",
                    )
                    st.markdown(
                        chips(job["matched_skills"], "chip-ok")
                        + chips(job["missing_skills"], "chip-miss"),
                        unsafe_allow_html=True,
                    )
                    st.caption(job["why"])
