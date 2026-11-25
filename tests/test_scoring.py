from app.core.config import ACTION_VERBS
from app.core.scoring import (
    check_action_verbs,
    check_contact,
    check_length,
    check_quantified,
    check_sections,
    check_skill_count,
    count_words,
    score_resume,
)
from app.core.sections import detect_sections
from app.core.skills import extract_skills


def test_rubric_weights_sum_to_100(strong_text):
    sections = detect_sections(strong_text)
    result = score_resume(strong_text, sections, set())
    assert sum(check.max_points for check in result.checks) == 100


def test_strong_resume_scores_high(strong_text):
    sections = detect_sections(strong_text)
    skills = {hit.skill for hit in extract_skills(strong_text)}
    result = score_resume(strong_text, sections, skills)
    assert result.total >= 85
    assert all(check.passed or check.suggestion for check in result.checks)


def test_weak_resume_scores_low_with_suggestions(fixtures):
    from app.core.parsers import parse_resume

    text = parse_resume("weak_resume.docx", (fixtures / "weak_resume.docx").read_bytes())
    sections = detect_sections(text)
    skills = {hit.skill for hit in extract_skills(text)}
    result = score_resume(text, sections, skills)
    assert result.total < 40
    assert len(result.suggestions) >= 4


def test_contact_full_marks():
    check = check_contact("Jane\njane@example.com\n+1 555-010-2345")
    assert check.points == 10


def test_contact_missing_phone():
    check = check_contact("jane@example.com")
    assert check.points == 5
    assert "phone number" in check.suggestion


def test_contact_ignores_year_ranges():
    check = check_contact("Worked 2019 - 2021 and 2022 - 2023")
    assert check.points == 0


def test_sections_partial_credit():
    check = check_sections({"summary": "x", "skills": "y"})
    assert check.points == 10
    assert "Experience" in check.suggestion and "Education" in check.suggestion


def test_skill_count_scales_to_target():
    assert check_skill_count({f"s{i}" for i in range(8)}).points == 20
    half = check_skill_count({f"s{i}" for i in range(4)})
    assert half.points == 10
    assert half.suggestion is not None


def test_quantified_lines_scale():
    text = "\n".join(["Improved speed by 20%"] * 5 + ["No numbers here"])
    assert check_quantified(text).points == 20
    assert check_quantified("Nothing measurable").points == 0


def test_action_verbs_ratio():
    experience = "- Led the team\n- Built APIs\n- Helped with stuff\n- Did things"
    check = check_action_verbs(experience)
    assert check.points == 15 * 2 / 4


def test_action_verbs_without_bullets_uses_lines():
    check = check_action_verbs("Developed tooling\nManaged releases")
    assert check.points == 15


def test_action_verbs_missing_section():
    check = check_action_verbs("")
    assert check.points == 0
    assert check.suggestion


def test_action_verb_list_is_sizeable():
    assert len(ACTION_VERBS) >= 50


def test_length_bands():
    assert check_length("word " * 500).points == 15
    short = check_length("word " * 150)
    assert short.points == 7.5
    long = check_length("word " * 1200)
    assert 0 < long.points < 15
    assert check_length("word " * 2000).points == 0


def test_count_words_ignores_punctuation():
    assert count_words("Hello, world! It's 2024.") == 5
