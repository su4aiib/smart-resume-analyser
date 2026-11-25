from app.core.skills import extract_skills, group_by_category, load_entries, skill_names


def test_taxonomy_has_enough_entries():
    entries = load_entries()
    assert len(entries) >= 150
    categories = {entry.category for entry in entries}
    assert {
        "languages",
        "frameworks",
        "databases",
        "cloud_devops",
        "data_ml",
        "tools",
        "soft_skills",
    } <= categories


def test_alias_maps_to_canonical_name():
    names = skill_names("Built services in JS and deployed on k8s.")
    assert "JavaScript" in names
    assert "Kubernetes" in names


def test_java_does_not_match_javascript():
    names = skill_names("Strong JavaScript skills.")
    assert "JavaScript" in names
    assert "Java" not in names


def test_word_boundary_for_short_terms():
    # "Ruby" must not match inside a longer token.
    assert "Ruby" not in skill_names("RubyMine is an IDE")


def test_hits_have_correct_offsets():
    text = "Python and Docker"
    hits = extract_skills(text)
    assert [h.skill for h in hits] == ["Python", "Docker"]
    for hit in hits:
        assert text[hit.start_char : hit.end_char] == hit.matched_text


def test_hits_record_alias_text():
    hits = extract_skills("Experience with AWS and PostgreSQL.")
    by_skill = {h.skill: h.matched_text for h in hits}
    assert by_skill["Amazon Web Services"] == "AWS"
    assert by_skill["PostgreSQL"] == "PostgreSQL"


def test_overlapping_aliases_keep_longest_span():
    hits = extract_skills("We built REST APIs for the team.")
    rest_hits = [h for h in hits if h.skill == "REST APIs"]
    assert len(rest_hits) == 1
    assert rest_hits[0].matched_text == "REST APIs"


def test_group_by_category(strong_text):
    grouped = group_by_category(extract_skills(strong_text))
    assert "Python" in grouped["languages"]
    assert "Docker" in grouped["cloud_devops"]
    assert list(grouped) == sorted(grouped)
