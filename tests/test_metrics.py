import math
from pathlib import Path

from readability_score.metrics import (
    analyze_text,
    flesch_kincaid_grade,
    flesch_label,
    flesch_reading_ease,
    smog_style_grade,
)

DATA = Path(__file__).parent / "data"


def load(name: str) -> str:
    return (DATA / name).read_text(encoding="utf-8")


def test_formula_hand_computed_sentence():
    text = "The cat sat."
    assert flesch_kincaid_grade(3, 1, 3) == 0.39 * 3 + 11.8 * 1.0 - 15.59
    assert flesch_reading_ease(3, 1, 3) == 206.835 - 1.015 * 3 - 84.6 * 1.0


def test_smog_formula_matches():
    assert smog_style_grade(12, 30) == 1.0430 * math.sqrt(12) + 3.1291


def test_smog_needs_three_sentences():
    assert smog_style_grade(5, 2) is None


def test_metrics_none_on_empty():
    report = analyze_text("")
    assert report.flesch_reading_ease is None
    assert report.flesch_kincaid_grade is None
    assert report.smog_grade is None
    assert report.words == 0
    assert report.avg_sentence_length == 0.0


def test_easy_text_scores_easier_than_hard_text():
    easy = analyze_text(load("easy.txt"), source="easy.txt")
    hard = analyze_text(load("hard.txt"), source="hard.txt")
    assert easy.flesch_kincaid_grade is not None
    assert hard.flesch_kincaid_grade is not None
    assert easy.flesch_kincaid_grade < 8
    assert hard.flesch_kincaid_grade > 10
    assert easy.flesch_kincaid_grade < hard.flesch_kincaid_grade
    assert easy.flesch_reading_ease > hard.flesch_reading_ease
    assert easy.avg_sentence_length < hard.avg_sentence_length
    assert hard.smog_grade is not None and hard.smog_grade > easy.smog_grade


def test_long_sentence_hotspots():
    long_sentence = " ".join(["Word"] + ["word"] * 24) + "."
    text = f"Short one here. {long_sentence} Also short."
    report = analyze_text(text, long_sentence_threshold=20, hotspot_limit=1)
    assert report.long_sentence_count == 1
    assert len(report.hotspots) == 1
    assert report.hotspots[0].words == 25
    assert report.hotspots[0].index == 2


def test_hotspot_limit_and_sorting():
    sentences = [
        "Short.",
        " ".join(["Anna"] * 21) + ".",
        " ".join(["Benjamin"] * 31) + ".",
        " ".join(["Carla"] * 26) + ".",
    ]
    report = analyze_text(" ".join(sentences), hotspot_limit=2)
    assert report.long_sentence_count == 3
    assert [h.words for h in report.hotspots] == [31, 26]


def test_flesch_label_bands():
    assert flesch_label(95) == "Very easy"
    assert flesch_label(65) == "Plain English"
    assert flesch_label(35) == "Difficult"
    assert flesch_label(None) == "n/a"
