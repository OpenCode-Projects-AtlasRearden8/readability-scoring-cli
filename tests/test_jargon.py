from readability_score.jargon import build_pattern, find_hits, load_lexicon


def make_entries(tmp_path, content, suffix=".txt"):
    lex_file = tmp_path / f"lexicon{suffix}"
    lex_file.write_text(content, encoding="utf-8")
    return load_lexicon(lex_file)


def test_load_lexicon_skips_comments_and_blanks(tmp_path):
    entries = make_entries(
        tmp_path,
        "# comment\n\nhypertension\n  diuretic  \n",
    )
    assert [entry.term for entry in entries] == ["hypertension", "diuretic"]


def test_lexicon_deduplicates_case_insensitively(tmp_path):
    entries = make_entries(tmp_path, "Hypertension\nhypertension\n")
    assert len(entries) == 1


def test_csv_lexicon_uses_first_column(tmp_path):
    entries = make_entries(
        tmp_path,
        "term,note\nhypertension,high blood pressure\ndiuretic,water pill\n",
        suffix=".csv",
    )
    assert [entry.term for entry in entries] == ["hypertension", "diuretic"]


def test_word_boundaries_and_suffixes():
    pattern = build_pattern("diuretic")
    assert pattern.search("Take the diuretic daily")
    assert pattern.search("Diuretics help")
    assert not pattern.search("prediuretic")

    hypertension = build_pattern("hypertension")
    assert hypertension.search("Uncontrolled hypertension is risky")
    assert not hypertension.search("hypertensive crisis")


def test_multiword_phrase_match():
    pattern = build_pattern("blood pressure")
    assert pattern.search("Check your blood pressure cuff")
    assert pattern.search("blood-pressure cuff") is None


def test_find_hits_counts_and_quotes_example():
    entries = [type("E", (), {"term": "fever", "pattern": build_pattern("fever")})()]
    sentences = [
        "Call your clinic today.",
        "Call if you get a fever.",
        "A fever over 101 needs care. Fever returning is worse.",
    ]
    hits = find_hits(sentences, entries)
    assert len(hits) == 1
    assert hits[0].count == 3
    assert hits[0].example_index == 2
    assert "fever" in hits[0].example.lower()


def test_find_hits_empty_input():
    assert find_hits([], []) == []
