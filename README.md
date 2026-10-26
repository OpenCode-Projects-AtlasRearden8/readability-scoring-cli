# readability-score

**Offline plain-language readability scoring for the command line.**

`readability-score` reads a document (or a whole folder of documents) and tells you,
in plain English, how hard it is to read — with **zero network access, zero
dependencies, and zero endpoints**. It was built for writing patient-teaching
handouts and beginner-friendly guides, where the goal is usually a reading
grade around 6–8.

Built by **Asdale Dynamics, LLC** — the plain-English AI education company behind
*The Massive AI Manual* and [dylanasdale.github.io](https://dylanasdale.github.io).
Healthcare education only; this tool is **not medical advice**.

---

## What it measures

| Metric | What it tells you |
| --- | --- |
| **Flesch-Kincaid grade** (style estimate) | The U.S. school-grade reading level a heuristic assigns (e.g. `7.4` ≈ 7th–8th grade). |
| **Flesch Reading Ease** | A 0–100 score; higher is easier, with plain-English labels (`Easy`, `Difficult`, …). |
| **SMOG-style grade** | A grade estimate from polysyllable counts (McLaughlin's SMOG formula, computed over the full text rather than 30 sampled sentences). |
| **Average sentence length** | Words per sentence — the single easiest thing to fix. |
| **Long-sentence hotspots** | Sentences over a word threshold (default 20), **quoted back** with their location so you can split them. |
| **Custom jargon flags** | Terms from **your own lexicon file**, counted and quoted with an example sentence (e.g. flag `hypertension` so you remember to say "high blood pressure"). |

Everything runs locally with Python's standard library only. No install is
strictly required, nothing is uploaded, and no results leave your machine.

## Quick start

```bash
# from this folder, no install needed
python3 -m readability_score examples/docs/patient_handout_easy.md

python3 -m readability_score examples/docs/patient_handout_hard.md \
    --lexicon examples/jargon_lexicon.txt
```

Sample output (trimmed):

```
Readability report — examples/docs/patient_handout_easy.md
====================================================================
Sentences 17 | Words 106 | Syllables 125 | Polysyllabic words 2
Avg sentence length: 6.2 words
Long sentences (>=20 words): 0 (0.0%)

Flesch Reading Ease: 100.7 (Very easy)
Flesch-Kincaid grade: 0.8
SMOG-style grade: 5.1

Long-sentence hotspots (>=20 words): none
```

Batch-score a whole folder and export CSV:

```bash
python3 -m readability_score examples/docs \
    --lexicon examples/jargon_lexicon.txt \
    --grade-target 8 \
    --csv-out results.csv
```

```
Scanned 2 file(s) under examples/docs
--------------------------------------------------------------------
file                                          words  sent   avg     FK   SMOG jargon
--------------------------------------------------------------------
examples/docs/patient_handout_easy.md           106    17   6.2    0.8    5.1      0
examples/docs/patient_handout_hard.md           142    12  11.8   21.8    8.8     12 !
--------------------------------------------------------------------
Mean Flesch-Kincaid grade: 11.3
Plain-language target grade 8.0: 1 of 2 file(s) above target ('!' marks them)
Jargon lexicon: examples/jargon_lexicon.txt
CSV written: results.csv
```

## Install (optional)

```bash
pip install -e .          # provides the `readability-score` command
readability-score --version
```

Without installing, run `python3 -m readability_score ...` from inside this
folder — the package sits at the repo root, so no path tricks are needed.

## CLI reference

```
readability-score PATH [options]

PATH                    a document file, or a folder to batch-score
--lexicon FILE          custom jargon lexicon (.txt: one term per line;
                        .csv: first column). Repeatable. '#' lines are comments
--long-sentence N       word count that makes a sentence "long" (default 20)
--hotspots N            how many hotspot sentences to quote back (default 3)
--grade-target N        plain-language target FK grade (e.g. 8); flags files above it
--csv-out FILE          write batch results as CSV (stable column order)
--format text|json      stdout format; json is one structured record per file
--ext LIST              folder-scan extensions (default .txt,.md,.markdown,.text)
--no-recursive          scan the folder only, not subfolders
--version               print version
```

Exit codes: `0` success, `1` runtime error (bad path, unreadable file, empty
folder), `2` argparse usage error.

## CSV columns

`file, words, sentences, avg_sentence_length, long_sentence_count,
long_sentence_pct, flesch_reading_ease, fk_grade, smog_grade, polysyllables,
jargon_flags, over_grade_target`

`jargon_flags` is `term xN; other xM`; `over_grade_target` is `yes/no/empty`
(empty when no `--grade-target` was given). Scores are blank when a document
is too short to score.

## Lexicon file format

```text
# jargon_lexicon.txt — one term per line, '#' lines are comments
hypertension
diuretic
blood pressure cuff
```

Matching is case-insensitive, respects word boundaries, and allows simple
endings, so `diuretic` also flags `diuretics`, and `administer` flags
`administered`. Multi-word phrases work. A `.csv` file also works — the first
column is the term, extra columns are ignored (a header row `term,...` is
skipped).

## Reading the numbers

- **Flesch-Kincaid grade ≤ 8** is the usual plain-language aim; many patient
  education style guides target **6–8**.
- **Long sentences** are the fastest fix: find them (they're quoted back),
  split them, re-score.
- **Jargon flags** are a nudge, not a ban — sometimes the medical term is
  required; the flag just reminds you to define it in the same sentence.

## How it works (honest limits)

- Sentence splitting uses terminal punctuation, markdown/blank-line blocks,
  and a small abbreviation list (`Dr.`, `e.g.`, decimals, initials). Sentences
  are expected to start with a capital letter or stand on their own line.
- Syllable counts use a standard English vowel-group heuristic plus a tiny
  exception list. Expect roughly ±1 syllable on unusual words; the grade
  estimates are style indicators, not clinical measurements.
- SMOG is computed over the **whole text** (the standard adaptation for short
  documents) rather than sampling 30 sentences; fewer than 3 sentences is not
  scored.
- English-oriented. Other languages will skew.

## Development

```bash
python3 -m pytest -q       # 38 tests, all offline
```

Project layout:

```
readability_score/   text.py, metrics.py, jargon.py, report.py, cli.py
examples/            sample handouts + jargon_lexicon.txt
tests/               pytest suite with sample texts
```

## License

MIT — see [LICENSE](LICENSE). Copyright (c) 2026 **Asdale Dynamics, LLC**.

From Dylan Asdale's plain-English AI project: *The Massive AI Manual* and
[dylanasdale.github.io](https://dylanasdale.github.io) — AI explained like a
friend would. This tool is for healthcare **education only** and is never a
substitute for professional medical advice.
