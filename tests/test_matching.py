import pandas as pd
import pytest

from app.core.config import JOBS_PATH, MAX_TOP_N, SKILL_WEIGHT, TEXT_WEIGHT
from app.core.matching import load_jobs, match_resume_to_job, recommend_jobs, text_similarity


def test_weights_sum_to_one():
    assert SKILL_WEIGHT + TEXT_WEIGHT == pytest.approx(1.0)


def test_job_match_reports_matched_and_missing(strong_text, job_description):
    result = match_resume_to_job(strong_text, job_description)
    assert "Python" in result.matched_skills
    assert "Terraform" in result.matched_skills
    assert result.missing_skills == ()  # every JD skill is in the resume
    assert 0 < result.score <= 1
    expected = SKILL_WEIGHT * result.skill_score + TEXT_WEIGHT * result.text_score
    assert result.score == pytest.approx(expected, abs=1e-3)


def test_job_match_with_missing_skills(strong_text):
    result = match_resume_to_job(strong_text, "We need Rust, Haskell and Elixir experts.")
    assert set(result.missing_skills) == {"Elixir", "Haskell", "Rust"}
    assert result.skill_score == 0


def test_job_without_known_skills_has_zero_skill_score(strong_text):
    result = match_resume_to_job(strong_text, "Looking for a friendly person to help customers.")
    assert result.skill_score == 0


def test_text_similarity_handles_empty_input():
    assert text_similarity("", ["anything here"]) == [0.0]
    assert text_similarity("resume", []) == []


def test_recommendations_are_ranked_and_capped(strong_text):
    jobs = load_jobs()
    results = recommend_jobs(strong_text, jobs, top_n=5, threshold=0.0)
    assert len(results) <= 5
    scores = [r.match.score for r in results]
    assert scores == sorted(scores, reverse=True)


def test_top_n_is_clamped_to_max(strong_text):
    results = recommend_jobs(strong_text, load_jobs(), top_n=10_000, threshold=0.0)
    assert len(results) <= MAX_TOP_N


def test_threshold_filters_low_matches(strong_text):
    results = recommend_jobs(strong_text, load_jobs(), threshold=0.99)
    assert results == []


def test_location_filter(strong_text):
    results = recommend_jobs(strong_text, load_jobs(), threshold=0.0, location="remote", top_n=50)
    assert results
    assert all("remote" in r.location.lower() for r in results)


def test_min_score_combines_with_threshold(strong_text):
    results = recommend_jobs(strong_text, load_jobs(), threshold=0.0, min_score=0.5, top_n=50)
    assert all(r.match.score >= 0.5 for r in results)


def test_each_recommendation_explains_itself(strong_text):
    results = recommend_jobs(strong_text, load_jobs(), threshold=0.0, top_n=3)
    for result in results:
        assert isinstance(result.match.matched_skills, tuple)
        assert isinstance(result.match.missing_skills, tuple)


def test_load_jobs_validates_columns(tmp_path):
    bad = tmp_path / "jobs.csv"
    pd.DataFrame({"job_id": ["1"], "title": ["x"]}).to_csv(bad, index=False)
    with pytest.raises(ValueError, match="missing columns"):
        load_jobs(bad)


def test_bundled_jobs_file_loads():
    jobs = load_jobs(JOBS_PATH)
    assert len(jobs) >= 30
    assert jobs["job_id"].is_unique
