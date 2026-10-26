import csv
import json
from pathlib import Path

from readability_score.metrics import analyze_text
from readability_score.report import csv_row, format_single_report, json_payload, write_csv


def make_report(tmp_path, name="doc.txt", text="One. Two words. Three words now."):
    return analyze_text(text, source=name)


def test_csv_row_fields(tmp_path):
    doc = make_report(tmp_path)
    row = csv_row(doc)
    assert row["file"] == "doc.txt"
    assert row["sentences"] == 3
    assert row["words"] == 6
    assert row["fk_grade"]
    assert row["over_grade_target"] == ""


def test_csv_row_grade_target_flag(tmp_path):
    text = " ".join(["difficult"] * 10) + "."
    doc = analyze_text(text, source="dense.md")
    row = csv_row(doc, grade_target=8.0)
    assert row["over_grade_target"] == "yes"


def test_write_csv_roundtrip(tmp_path):
    docs = [
        analyze_text("Short text. Very easy words.", source="a.md"),
        analyze_text("Complex terminology necessitates careful consideration.", source="b.md"),
    ]
    out = tmp_path / "out.csv"
    write_csv(out, docs)
    with out.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 2
    assert rows[0]["file"] == "a.md"
    assert rows[1]["file"] == "b.md"
    assert float(rows[0]["fk_grade"]) < float(rows[1]["fk_grade"])


def test_format_single_report_quotes_hotspots(tmp_path):
    long_sentence = " ".join(["word"] * 24) + "."
    doc = analyze_text(f"Intro sentence. {long_sentence}", source="x.md")
    output = format_single_report(doc)
    assert "Flesch-Kincaid grade" in output
    assert "Long-sentence hotspots" in output
    assert "word word" in output
    assert "x.md" in output


def test_format_single_report_lexicon_names(tmp_path):
    doc = make_report(tmp_path)
    output = format_single_report(doc, lexicon_names=["lex.txt"])
    assert "Custom jargon flags (lexicon: lex.txt)" in output


def test_json_payload_structure(tmp_path):
    doc = make_report(tmp_path)
    payload = json.loads(json_payload([doc]))
    assert payload[0]["source"] == "doc.txt"
    assert "flesch_kincaid_grade" in payload[0]
    assert "hotspots" in payload[0]
