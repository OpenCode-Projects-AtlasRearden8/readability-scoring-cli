"""readability-score: offline plain-language readability scoring for CLI."""

from .metrics import (
    DEFAULT_HOTSPOT_LIMIT,
    DEFAULT_LONG_SENTENCE_THRESHOLD,
    DocReport,
    Hotspot,
    JargonHit,
    analyze_text,
    flesch_kincaid_grade,
    flesch_label,
    flesch_reading_ease,
    smog_style_grade,
)

__version__ = "1.0.0"

__all__ = [
    "DEFAULT_HOTSPOT_LIMIT",
    "DEFAULT_LONG_SENTENCE_THRESHOLD",
    "DocReport",
    "Hotspot",
    "JargonHit",
    "analyze_text",
    "flesch_kincaid_grade",
    "flesch_label",
    "flesch_reading_ease",
    "smog_style_grade",
    "__version__",
]
