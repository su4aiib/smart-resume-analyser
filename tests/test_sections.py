from app.core.sections import detect_sections


def test_detects_standard_sections(strong_text):
    sections = detect_sections(strong_text)
    for name in ("summary", "skills", "experience", "education", "projects", "certifications"):
        assert name in sections, name
    assert "header" in sections
    assert "Jane Doe" in sections["header"]


def test_section_body_excludes_header_line(strong_text):
    sections = detect_sections(strong_text)
    assert not sections["education"].lower().startswith("education")
    assert "State University" in sections["education"]


def test_header_aliases_are_mapped():
    text = "Jane\nProfessional Experience:\nBuilt things.\nTechnical Skills\nPython"
    sections = detect_sections(text)
    assert sections["experience"] == "Built things."
    assert sections["skills"] == "Python"


def test_empty_sections_are_omitted():
    sections = detect_sections("Jane\nEducation\n\nSkills\nPython")
    assert "education" not in sections
    assert sections["skills"] == "Python"
