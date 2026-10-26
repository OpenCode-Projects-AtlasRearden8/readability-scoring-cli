"""Custom jargon flagging driven by a user-supplied lexicon file.

Lexicon format (.txt): one term per line; blank lines and lines starting
with '#' are ignored. A .csv lexicon may also be used; the first column
is the term and any remaining columns are treated as notes.
Matching is case-insensitive, respects word boundaries, and allows
simple plural/verb endings (s, es, ed, ing, ly) so "diuretic" also
flags "diuretics".
"""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path

from .metrics import JargonHit

_SUFFIX = r"(?:s|es|ed|ing|ly)?"


@dataclass(frozen=True)
class LexiconEntry:
    term: str
    pattern: re.Pattern


def build_pattern(term: str) -> re.Pattern:
    words = [re.escape(word) for word in term.split()]
    body = r"\s+".join(words)
    return re.compile(
        rf"(?<![A-Za-z0-9]){body}{_SUFFIX}(?![A-Za-z0-9])", re.IGNORECASE
    )


def load_lexicon(path: str | Path) -> list[LexiconEntry]:
    lexicon_path = Path(path)
    raw_terms: list[str] = []
    if lexicon_path.suffix.lower() == ".csv":
        with lexicon_path.open(newline="", encoding="utf-8-sig") as handle:
            for row in csv.reader(handle):
                if not row:
                    continue
                term = row[0].strip()
                if not term or term.lower() == "term":
                    continue
                if not term.startswith("#"):
                    raw_terms.append(term)
    else:
        with lexicon_path.open(encoding="utf-8-sig") as handle:
            for line in handle:
                term = line.strip()
                if term and not term.startswith("#"):
                    raw_terms.append(term)

    entries: list[LexiconEntry] = []
    seen: set[str] = set()
    for term in raw_terms:
        key = term.lower()
        if key in seen:
            continue
        seen.add(key)
        entries.append(LexiconEntry(term=term, pattern=build_pattern(term)))
    return entries


def find_hits(sentences: list[str], entries: list[LexiconEntry]) -> list[JargonHit]:
    """Count lexicon matches per sentence list, quoting the first example."""
    hits: list[JargonHit] = []
    for entry in entries:
        total = 0
        example_index = 0
        example = ""
        for index, sentence in enumerate(sentences, start=1):
            found = entry.pattern.findall(sentence)
            if found and example_index == 0:
                example_index = index
                example = sentence
            total += len(found)
        if total:
            hits.append(
                JargonHit(
                    term=entry.term,
                    count=total,
                    example_index=example_index,
                    example=example,
                )
            )
    return hits
