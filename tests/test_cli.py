import csv
import json
import subprocess
import sys
from pathlib import Path

from readability_score.cli import main

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


def test_single_file_text_mode(capsys):
    rc = main([str(EXAMPLES / "docs" / "patient_handout_easy.md")])
    out = capsys.readouterr().out
    assert rc == 0
    assert "Flesch-Kincaid grade" in out
    assert "SMOG-style grade" in out
    assert "Avg sentence length" in out


def test_single_file_with_lexicon(capsys):
    rc = main(
        [
            str(EXAMPLES / "docs" / "patient_handout_hard.md"),
            "--lexicon",
            str(EXAMPLES / "jargon_lexicon.txt"),
        ]
    )
    out = capsys.readouterr().out
    assert rc == 0
    assert "hypertension" in out
    assert "Custom jargon flags" in out


def test_batch_with_csv_out(tmp_path, capsys):
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "a.md").write_text("Short words. Tiny steps. Rest well.", encoding="utf-8")
    (docs_dir / "b.txt").write_text(
        " ".join(["significant"] * 30) + ".", encoding="utf-8"
    )
    csv_path = tmp_path / "results.csv"
    rc = main([str(docs_dir), "--csv-out", str(csv_path), "--grade-target", "8"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "a.md" in out and "b.txt" in out
    assert "CSV written" in out
    with csv_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 2
    assert float(rows[1]["fk_grade"]) > float(rows[0]["fk_grade"])
    assert rows[1]["over_grade_target"] == "yes"


def test_batch_recursive_and_no_recursive(tmp_path, capsys):
    docs_dir = tmp_path / "docs"
    nested = docs_dir / "sub"
    nested.mkdir(parents=True)
    (docs_dir / "top.md").write_text("Top file here.", encoding="utf-8")
    (nested / "deep.md").write_text("Deep file here.", encoding="utf-8")

    rc = main([str(docs_dir)])
    out = capsys.readouterr().out
    assert rc == 0
    assert "deep.md" in out and "top.md" in out

    rc = main([str(docs_dir), "--no-recursive"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "top.md" in out
    assert "deep.md" not in out


def test_json_output_is_valid(capsys):
    rc = main([str(EXAMPLES / "docs" / "patient_handout_easy.md"), "--format", "json"])
    out = capsys.readouterr().out
    assert rc == 0
    payload = json.loads(out)
    assert payload[0]["flesch_kincaid_grade"] is not None


def test_missing_path_returns_error(capsys):
    rc = main([str(tmp_missing := Path("does/not/exist"))])
    err = capsys.readouterr().err
    assert rc == 1
    assert "does not exist" in err


def test_folder_without_documents_errors(tmp_path, capsys):
    rc = main([str(tmp_path)])
    err = capsys.readouterr().err
    assert rc == 1
    assert "no documents found" in err


def test_lexicon_flagging_end_to_end(tmp_path, capsys):
    doc = tmp_path / "handout.md"
    doc.write_text("The medication must be administered daily.", encoding="utf-8")
    lexicon = tmp_path / "lex.txt"
    lexicon.write_text("# my words\nadminister\n", encoding="utf-8")
    rc = main([str(doc), "--lexicon", str(lexicon)])
    out = capsys.readouterr().out
    assert rc == 0
    assert "'administer' x1" in out


def test_console_script_help():
    result = subprocess.run(
        [sys.executable, "-m", "readability_score", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "readability-score" in result.stdout
