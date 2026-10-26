"""Report formatting: text reports, JSON payloads, and CSV export."""

from __future__ import annotations

import csv
import json
from dataclasses import asdict
from pathlib import Path

from .metrics import DEFAULT_HOTSPOT_LIMIT, DEFAULT_LONG_SENTENCE_THRESHOLD, DocReport, flesch_label

CSV_COLUMNS = [
    "file",
    "words",
    "sentences",
    "avg_sentence_length",
    "long_sentence_count",
    "long_sentence_pct",
    "flesch_reading_ease",
    "fk_grade",
    "smog_grade",
    "polysyllables",
    "jargon_flags",
    "over_grade_target",
]


def _round_or_blank(value: float | None, digits: int = 1) -> str:
    return "" if value is None else f"{round(value, digits)}"


def csv_row(doc: DocReport, grade_target: float | None = None) -> dict[str, str]:
    over = ""
    if grade_target is not None and doc.flesch_kincaid_grade is not None:
        over = "yes" if doc.flesch_kincaid_grade > grade_target else "no"
    return {
        "file": doc.source,
        "words": doc.words,
        "sentences": doc.sentences,
        "avg_sentence_length": f"{round(doc.avg_sentence_length, 1)}",
        "long_sentence_count": doc.long_sentence_count,
        "long_sentence_pct": f"{doc.long_sentence_pct}",
        "flesch_reading_ease": _round_or_blank(doc.flesch_reading_ease),
        "fk_grade": _round_or_blank(doc.flesch_kincaid_grade),
        "smog_grade": _round_or_blank(doc.smog_grade),
        "polysyllables": doc.polysyllables,
        "jargon_flags": "; ".join(f"{hit.term} x{hit.count}" for hit in doc.jargon_hits),
        "over_grade_target": over,
    }


def write_csv(path: str | Path, docs: list[DocReport], grade_target: float | None = None) -> None:
    with Path(path).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS, lineterminator="\n")
        writer.writeheader()
        for doc in docs:
            writer.writerow(csv_row(doc, grade_target))


def _excerpt(text: str, limit: int = 100) -> str:
    cleaned = " ".join(text.split())
    if len(cleaned) > limit:
        cleaned = cleaned[: limit - 1].rstrip() + "\u2026"
    return cleaned


def format_single_report(
    doc: DocReport,
    *,
    lexicon_names: list[str] | None = None,
    long_sentence_threshold: int = DEFAULT_LONG_SENTENCE_THRESHOLD,
    hotspot_limit: int = DEFAULT_HOTSPOT_LIMIT,
    grade_target: float | None = None,
) -> str:
    lines: list[str] = []
    lines.append(f"Readability report \u2014 {doc.source}")
    lines.append("=" * 68)
    lines.append(
        f"Sentences {doc.sentences} | Words {doc.words} | Syllables {doc.syllables}"
        f" | Polysyllabic words {doc.polysyllables}"
    )
    lines.append(f"Avg sentence length: {doc.avg_sentence_length:.1f} words")
    lines.append(
        f"Long sentences (>={long_sentence_threshold} words): "
        f"{doc.long_sentence_count} ({doc.long_sentence_pct}%)"
    )
    lines.append("")
    lines.append(
        f"Flesch Reading Ease: {_round_or_blank(doc.flesch_reading_ease, 1)}"
        f" ({flesch_label(doc.flesch_reading_ease)})"
    )
    lines.append(f"Flesch-Kincaid grade: {_round_or_blank(doc.flesch_kincaid_grade, 1)}")
    lines.append(f"SMOG-style grade: {_round_or_blank(doc.smog_grade, 1)}")
    if grade_target is not None and doc.flesch_kincaid_grade is not None:
        delta = round(doc.flesch_kincaid_grade - grade_target, 1)
        verdict = "ABOVE target" if delta > 0 else "at or below target"
        lines.append(f"Plain-language target grade {grade_target}: {verdict} (by {abs(delta)})")

    lines.append("")
    if doc.hotspots:
        lines.append(
            f"Long-sentence hotspots (>={long_sentence_threshold} words)"
            f" \u2014 {doc.long_sentence_count} found, top {min(len(doc.hotspots), hotspot_limit)}:"
        )
        for hotspot in doc.hotspots:
            lines.append(
                f"  #{hotspot.index} ({hotspot.words} words): \"{_excerpt(hotspot.text)}\""
            )
    else:
        lines.append(f"Long-sentence hotspots (>={long_sentence_threshold} words): none")

    lines.append("")
    if lexicon_names:
        label = ", ".join(lexicon_names)
        if doc.jargon_hits:
            lines.append(f"Custom jargon flags (lexicon: {label}):")
            for hit in doc.jargon_hits:
                lines.append(
                    f"  '{hit.term}' x{hit.count} \u2014 sentence #{hit.example_index}:"
                    f" \"{_excerpt(hit.example)}\""
                )
        else:
            lines.append(f"Custom jargon flags (lexicon: {label}): none found")
    return "\n".join(lines)


def format_batch_report(
    docs: list[DocReport],
    *,
    scanned_root: str,
    lexicon_names: list[str] | None = None,
    grade_target: float | None = None,
) -> str:
    lines: list[str] = []
    lines.append(f"Scanned {len(docs)} file(s) under {scanned_root}")
    lines.append("-" * 68)
    header = (
        f"{'file':<44} {'words':>6} {'sent':>5} {'avg':>5} {'FK':>6} {'SMOG':>6} {'jargon':>6}"
    )
    lines.append(header)
    lines.append("-" * 68)
    for doc in docs:
        fk = _round_or_blank(doc.flesch_kincaid_grade)
        smog = _round_or_blank(doc.smog_grade)
        marker = ""
        if grade_target is not None and doc.flesch_kincaid_grade is not None:
            marker = " !" if doc.flesch_kincaid_grade > grade_target else ""
        name = doc.source
        if len(name) > 43:
            name = name[-43:]
        lines.append(
            f"{name:<44} {doc.words:>6} {doc.sentences:>5}"
            f" {doc.avg_sentence_length:>5.1f} {fk:>6} {smog:>6} {len(doc.jargon_hits):>6}{marker}"
        )
    lines.append("-" * 68)
    graded = [doc.flesch_kincaid_grade for doc in docs if doc.flesch_kincaid_grade is not None]
    if graded:
        mean_fk = sum(graded) / len(graded)
        lines.append(f"Mean Flesch-Kincaid grade: {mean_fk:.1f}")
    if grade_target is not None:
        over = [
            doc
            for doc in docs
            if doc.flesch_kincaid_grade is not None and doc.flesch_kincaid_grade > grade_target
        ]
        lines.append(
            f"Plain-language target grade {grade_target}: "
            f"{len(over)} of {len(docs)} file(s) above target ('!' marks them)"
        )
    if lexicon_names:
        lines.append(f"Jargon lexicon: {', '.join(lexicon_names)}")
    return "\n".join(lines)


def json_payload(docs: list[DocReport]) -> str:
    return json.dumps([asdict(doc) for doc in docs], indent=2, ensure_ascii=False)
