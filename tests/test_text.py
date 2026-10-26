from readability_score.text import (
    count_syllables,
    split_sentences,
    tokenize_words,
)


def test_syllables_known_words():
    cases = {
        "cat": 1,
        "cake": 1,
        "table": 2,
        "apple": 2,
        "little": 2,
        "while": 1,
        "hello": 2,
        "beautiful": 3,
        "elephant": 3,
        "butterfly": 3,
        "walked": 1,
        "carried": 2,
        "ocean": 2,
        "rhythm": 1,
        "medicine": 3,
        "hypertension": 4,
    }
    for word, expected in cases.items():
        assert count_syllables(word) == expected, word


def test_syllables_edge_cases():
    assert count_syllables("") == 0
    assert count_syllables("!!!") == 0
    assert count_syllables("2026") == 1
    assert count_syllables("XYZ") == 1


def test_tokenize_words():
    assert tokenize_words("Don't stop-me now: 3 times!") == ["Don't", "stop-me", "now", "3", "times"]
    assert tokenize_words("...") == []


def test_sentences_basic():
    text = "First one. Second one? Third one! Done."
    assert split_sentences(text) == ["First one.", "Second one?", "Third one!", "Done."]


def test_sentences_abbreviations_and_decimals():
    text = "Dr. Smith saw the patient. Take 1.5 tablets daily. Then rest."
    sentences = split_sentences(text)
    assert len(sentences) == 3
    assert sentences[0].startswith("Dr. Smith")
    assert "1.5 tablets" in sentences[1]


def test_sentences_markdown_bullets_are_separate():
    text = "Do these things:\n- Wash your hands\n- Dry them well\nCall if fever."
    sentences = split_sentences(text)
    assert "Wash your hands" in sentences[1]
    assert any("Dry them well" == s for s in sentences)
    assert len(sentences) >= 4


def test_sentences_blank_lines_split_blocks():
    text = "One no-period line\nand more no-period words.\n\nNext block here."
    sentences = split_sentences(text)
    assert len(sentences) == 2


def test_sentences_empty_input():
    assert split_sentences("") == []
    assert split_sentences("   \n\n  ") == []
