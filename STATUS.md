# STATUS.md — readability-score

Last updated: 2026-10-26

## What was built

`readability-score` — a fully offline Python CLI that scores the readability of
plain-language documents (built for patient-teaching handouts and beginner
guides, where the usual target is Flesch-Kincaid grade 6–8).

Features:

- **Flesch-Kincaid-style grade estimate** and **Flesch Reading Ease** with
  plain-English labels (Plain English, Difficult, Very confusing, …).
- **SMOG-style grade** (McLaughlin formula over the full text — the standard
  adaptation for short documents; requires ≥ 3 sentences).
- **Average sentence length** in words.
- **Long-sentence hotspots** (default ≥ 20 words): quoted back with sentence
  position and word count so you can split them.
- **Custom jargon flags** from your own lexicon file (.txt one term per line,
  or .csv first column): case-insensitive, word-boundary matched, tolerant of
  simple endings (`diuretic` → `diuretics`), multi-word phrases supported.
  Each hit is counted and quoted with an example sentence.
- **Batch scoring** over a whole docs folder (recursive by default, hidden
  files skipped), with a compact summary table, mean FK grade, and optional
  `--grade-target` flagging for plain-language aims.
- **CSV export** (`--csv-out`) with stable column order; **JSON output**
  (`--format json`) for piping into other tools.
- Markdown-aware segmentation: blank lines, bullets, numbered items, and
  headings become their own sentences; common abbreviations (`Dr.`, `e.g.`,
  decimals, initials) do not split sentences.

Zero third-party runtime dependencies (Python ≥ 3.9 standard library only).
No network access, no endpoints, no telemetry, no secrets or personal data.

Project layout:

```
readability_score/    text.py (segmentation + syllables), metrics.py,
                      jargon.py, report.py (text/JSON/CSV), cli.py
examples/             two sample handouts (easy + hard) and jargon_lexicon.txt
tests/                38 pytest tests with sample texts
LICENSE               MIT, Copyright (c) 2026 Asdale Dynamics, LLC
```

## How to run it

```bash
# no install required (package sits at the repo root)
python3 -m readability_score examples/docs/patient_handout_easy.md

python3 -m readability_score examples/docs/patient_handout_hard.md \
    --lexicon examples/jargon_lexicon.txt

# batch a folder, flag files above grade 8, export CSV
python3 -m readability_score examples/docs \
    --lexicon examples/jargon_lexicon.txt \
    --grade-target 8 \
    --csv-out results.csv

# optional install to get the `readability-score` command
pip install -e .
readability-score --version
```

Useful flags: `--long-sentence N`, `--hotspots N`, `--grade-target N`,
`--format text|json`, `--ext .txt,.md`, `--no-recursive`, `--csv-out FILE`.

## Verification results (all run 2026-10-26)

- `python3 -m pytest -q` → **38 passed** in ~0.1s. Tests cover: syllable
  heuristics (known words + edge cases), sentence splitting (abbreviations,
  decimals, markdown bullets, blank lines), hand-computed FK/SMOG formula
  values, easy-vs-hard sample text ordering assertions, hotspot detection and
  limits, lexicon loading (comments, dedup, CSV header skip), boundary/suffix
  matching, CSV round-trip, text/JSON formatting, and end-to-end CLI tests
  (single file, batch + CSV, recursive vs `--no-recursive`, JSON validity,
  error exit codes, lexicon flagging).
- `python3 -m readability_score examples/docs --lexicon
  examples/jargon_lexicon.txt --grade-target 8 --csv-out results.csv` →
  batch table renders; CSV verified: 2 data rows, correct columns, `yes` in
  `over_grade_target` for the dense handout, jargon flags serialized
  (`hypertension x4; hypotension x1; ...`).
- `--format json` output parsed as valid JSON (`json.load` on stdout).
- Editable install verified in an isolated venv: `pip install -e .` +
  `readability-score --version` → `readability-score 1.0.0`, JSON mode works.
- Error handling verified: missing path → exit 1 with `error: path does not
  exist`; folder with no documents → exit 1 with a clear message.
- No network use anywhere: stdlib only, no fetches, no endpoints.

## Known gaps

- **Syllable heuristic is approximate**: a standard vowel-group algorithm plus
  a small exception list; unusual words can be off by ±1 syllable, so grades
  are style indicators, not measurements.
- **SMOG variant**: computed over the whole text rather than sampling 30
  sentences (the accepted approach for short documents); results run higher
  than classroom SMOG on jargon-dense text (the sample dense handout reports
  FK 21.8 / SMOG 8.8).
- **English-oriented**: sentence splitting expects capitalized sentence starts
  and terminal punctuation; syllables are an English heuristic.
- Sentences ending in a single capital letter followed by another capitalized
  word (e.g. "…plan B. Then…") are treated as initials and may merge.
- Folder scan matches by extension only; other formats (HTML, PDF, DOCX) are
  out of scope.
- No `--stdin` mode; scoring requires a file path or folder.
- Packaging metadata is standard setuptools; the system Python here is
  externally managed (PEP 668), so `pip install -e .` on this machine needs a
  venv — the no-install `python3 -m readability_score` path is unaffected.

## Ideas for later

- `--stdin` mode and glob patterns; HTML/PDF/DOCX text extraction.
- Grade-level "diff mode": suggest which sentences to split first.
- Multiple lexicon profiles per project (e.g. cardiology vs. diabetes).
- Optional `--jsonl` for streaming large corpora.
