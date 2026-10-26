"""Readability metrics: Flesch Reading Ease, Flesch-Kincaid grade,
SMOG-style grade, average sentence length, long-sentence hotspots, and
custom jargon flags."""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from .text import count_syllables, tokenize_words, split_sentences

DEFAULT_LONG_SENTENCE_THRESHOLD = 20
DEFAULT_HOTSPOT_LIMIT = 3
MIN_SENTENCES_FOR_SMOG = 3


@dataclass
class Hotspot:
    index: int
    words: int
    text: str


@dataclass
class JargonHit:
    term: str
    count: int
    example_index: int
    example: str


@dataclass
class DocReport:
    source: str
    sentences: int
    words: int
    syllables: int
    polysyllables: int
    avg_sentence_length: float
    long_sentence_count: int
    long_sentence_ratio: float
    flesch_reading_ease: float | None
    flesch_kincaid_grade: float | None
    smog_grade: float | None
    hotspots: list[Hotspot] = field(default_factory=list)
    jargon_hits: list[JargonHit] = field(default_factory=list)

    @property
    def long_sentence_pct(self) -> float:
        return round(self.long_sentence_ratio * 100, 1)


def flesch_reading_ease(words: int, sentences: int, syllables: int) -> float | None:
    """206.835 - 1.015*(words/sentences) - 84.6*(syllables/words)."""
    if sentences <= 0 or words <= 0:
        return None
    return 206.835 - 1.015 * (words / sentences) - 84.6 * (syllables / words)


def flesch_kincaid_grade(words: int, sentences: int, syllables: int) -> float | None:
    """0.39*(words/sentences) + 11.8*(syllables/words) - 15.59."""
    if sentences <= 0 or words <= 0:
        return None
    return 0.39 * (words / sentences) + 11.8 * (syllables / words) - 15.59


def smog_style_grade(polysyllables: int, sentences: int) -> float | None:
    """SMOG-style grade over the full text.

    Classic SMOG samples 30 sentences (10 at the start, middle, and end).
    For short handouts the standard full-text adaptation is used:
    1.0430 * sqrt(polysyllables * 30 / sentences) + 3.1291.
    Texts with fewer than 3 sentences return None.
    """
    if sentences < MIN_SENTENCES_FOR_SMOG:
        return None
    return 1.0430 * math.sqrt(polysyllables * 30 / sentences) + 3.1291


def flesch_label(score: float | None) -> str:
    if score is None:
        return "n/a"
    if score >= 90:
        return "Very easy"
    if score >= 80:
        return "Easy"
    if score >= 70:
        return "Fairly easy"
    if score >= 60:
        return "Plain English"
    if score >= 50:
        return "Fairly difficult"
    if score >= 30:
        return "Difficult"
    return "Very confusing"


def analyze_text(
    text: str,
    *,
    source: str = "",
    long_sentence_threshold: int = DEFAULT_LONG_SENTENCE_THRESHOLD,
    hotspot_limit: int = DEFAULT_HOTSPOT_LIMIT,
    jargon_matcher=None,
) -> DocReport:
    """Score one document's text and return a DocReport.

    jargon_matcher is an optional callable taking the sentence list and
    returning a list of JargonHit.
    """
    sentences = split_sentences(text)
    word_lists = [tokenize_words(sentence) for sentence in sentences]
    syllable_lists = [[count_syllables(word) for word in words] for words in word_lists]

    total_words = sum(len(words) for words in word_lists)
    total_syllables = sum(sum(syls) for syls in syllable_lists)
    sentence_count = len(sentences)
    polysyllables = sum(1 for syls in syllable_lists if syls and max(syls) >= 3)
    avg_sentence_length = (total_words / sentence_count) if sentence_count else 0.0

    hotspots: list[Hotspot] = []
    for position, (sentence, words) in enumerate(zip(sentences, word_lists), start=1):
        if len(words) >= long_sentence_threshold:
            hotspots.append(Hotspot(index=position, words=len(words), text=sentence))
    hotspots.sort(key=lambda hotspot: hotspot.words, reverse=True)
    shown = hotspots[:hotspot_limit]

    jargon_hits = jargon_matcher(sentences) if jargon_matcher else []
    over_threshold = len(hotspots)

    return DocReport(
        source=source,
        sentences=sentence_count,
        words=total_words,
        syllables=total_syllables,
        polysyllables=polysyllables,
        avg_sentence_length=avg_sentence_length,
        long_sentence_count=over_threshold,
        long_sentence_ratio=(over_threshold / sentence_count) if sentence_count else 0.0,
        flesch_reading_ease=flesch_reading_ease(total_words, sentence_count, total_syllables),
        flesch_kincaid_grade=flesch_kincaid_grade(total_words, sentence_count, total_syllables),
        smog_grade=smog_style_grade(polysyllables, sentence_count),
        hotspots=shown,
        jargon_hits=jargon_hits,
    )
