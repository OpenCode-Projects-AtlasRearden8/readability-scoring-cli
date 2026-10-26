"""Text segmentation and syllable estimation for readability scoring.

Everything here is deterministic and offline: sentence splitting, word
tokenizing, and an English syllable heuristic suitable for readability
style estimates (Flesch-Kincaid, Flesch Reading Ease, SMOG-style counts).
"""

from __future__ import annotations

import re

_WORD_RE = re.compile(r"[A-Za-z0-9]+(?:['\u2019\-][A-Za-z0-9]+)*")
_SENTENCE_SPLIT_RE = re.compile(
    r"(?<=[.!?])['\"”’)\]]*\s+(?=['\"“‘(\[]?[A-Z0-9])"
)
_BULLET_RE = re.compile(r"^(?:#{1,6}\s+|[-*\u2022\u2023\u2013\u2014>#]\s+|\d{1,2}[.)]\s+)")
_BULLET_LEAD_RE = re.compile(r"^(?:#{1,6}\s+|[-*\u2022\u2023\u2013\u2014>#]\s+|\d{1,2}[.)]\s+)")
_ELLIPSIS_RE = re.compile(r"\.\.\.")
_DECIMAL_RE = re.compile(r"(?<=\d)\.(?=\d)")
_ABBREV_RE = re.compile(
    r"\b(?:Mr|Mrs|Ms|Dr|Prof|Rev|Hon|St|Sr|Jr|vs|Inc|Ltd|approx|Dept|Univ|Fig|Vol|e\.g|i\.e)\."
)
_INITIAL_RE = re.compile(r"(?<=\s)([A-HJ-Z])\.(?=\s)")

_VOWELS = "aeiouy"
_SILENT_END_RE = re.compile(r"(?:[^laeiouy]es|ed|[^laeiouy]e)$")
_Y_START_RE = re.compile(r"^y")
_VOWEL_GROUP_RE = re.compile(r"[aeiouy]+")

SYLLABLE_EXCEPTIONS = {
    "medicine": 3,
    "business": 2,
    "every": 2,
    "evening": 2,
    "careful": 2,
    "carefully": 3,
    "different": 3,
    "disease": 2,
    "area": 3,
    "idea": 3,
    "minute": 2,
    "science": 2,
    "diagnosis": 4,
    "diagnoses": 4,
}


def _protect(text: str) -> tuple[str, list[tuple[str, str]]]:
    """Hide periods that do not end sentences behind placeholder tokens."""
    swaps: list[tuple[str, str]] = []

    def swap(match: re.Match) -> str:
        key = f"\x00{len(swaps)}\x00"
        swaps.append((key, match.group(0)))
        return key

    text = _DECIMAL_RE.sub(swap, text)
    text = _ELLIPSIS_RE.sub(swap, text)
    text = _ABBREV_RE.sub(swap, text)
    text = _INITIAL_RE.sub(swap, text)
    return text, swaps


def _restore(text: str, swaps: list[tuple[str, str]]) -> str:
    for key, original in swaps:
        text = text.replace(key, original)
    return text


def _blocks(text: str) -> list[str]:
    """Group lines into paragraph-like blocks.

    Blank lines separate blocks. Bullet, numbered, and heading lines
    become their own block so a markdown handout does not collapse its
    bullets into one enormous pseudo-sentence.
    """
    blocks: list[str] = []
    current: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            if current:
                blocks.append(" ".join(current))
                current = []
            continue
        if _BULLET_RE.match(line):
            if current:
                blocks.append(" ".join(current))
                current = []
            blocks.append(_BULLET_LEAD_RE.sub("", line))
        else:
            current.append(line)
    if current:
        blocks.append(" ".join(current))
    return blocks


def split_sentences(text: str) -> list[str]:
    """Split text into sentence strings, returning at least [] for empty."""
    protected, swaps = _protect(text)
    sentences: list[str] = []
    for block in _blocks(protected):
        for raw in _SENTENCE_SPLIT_RE.split(block):
            restored = _restore(raw.strip(), swaps)
            if restored and any(ch.isalnum() for ch in restored):
                sentences.append(restored)
    return sentences


def tokenize_words(text: str) -> list[str]:
    """Return word tokens; numbers count as words, punctuation does not."""
    return _WORD_RE.findall(text)


def count_syllables(word: str) -> int:
    """Estimate syllables in one token with an English vowel-group heuristic.

    Tokens with no letters (pure numbers) count as one syllable so they
    still count honestly toward word and sentence-length totals.
    """
    letters = re.sub(r"[^a-z]", "", word.lower())
    if not letters:
        return 1 if any(ch.isdigit() for ch in word) else 0
    if letters in SYLLABLE_EXCEPTIONS:
        return SYLLABLE_EXCEPTIONS[letters]
    count = 0
    stem = letters
    if len(stem) > 2 and stem.endswith("le"):
        if stem[-3] not in _VOWELS:
            count += 1
            stem = stem[:-2]
        else:
            stem = stem[:-1]
    stem = _SILENT_END_RE.sub("", stem)
    stem = _Y_START_RE.sub("", stem)
    count += len(_VOWEL_GROUP_RE.findall(stem))
    return max(1, count)


def syllable_counts(words: list[str]) -> list[int]:
    """Estimate syllables for each word token."""
    return [count_syllables(word) for word in words]
