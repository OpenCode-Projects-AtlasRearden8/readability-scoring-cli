"""Command-line interface for readability-score.

Fully offline: local files in, plain text / JSON / CSV out. No network,
no endpoints, no secrets.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .jargon import LexiconEntry, find_hits, load_lexicon
from .metrics import (
    DEFAULT_HOTSPOT_LIMIT,
    DEFAULT_LONG_SENTENCE_THRESHOLD,
    DocReport,
    analyze_text,
)
from .report import format_batch_report, format_single_report, json_payload, write_csv

DEFAULT_EXTENSIONS = ".txt,.md,.markdown,.text"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="readability-score",
        description=(
            "Score plain-language readability (Flesch-Kincaid-style grades, "
            "SMOG-style counts, average sentence length, long-sentence "
            "hotspots, custom jargon flags). Fully offline."
        ),
    )
    parser.add_argument("path", help="A document file, or a folder of documents to batch-score")
    parser.add_argument(
        "--lexicon",
        action="append",
        default=[],
        metavar="FILE",
        help="Custom jargon lexicon file (.txt one term per line, or .csv). Repeatable",
    )
    parser.add_argument(
        "--long-sentence",
        type=int,
        default=DEFAULT_LONG_SENTENCE_THRESHOLD,
        metavar="N",
        help=f"Words that make a sentence 'long' (default {DEFAULT_LONG_SENTENCE_THRESHOLD})",
    )
    parser.add_argument(
        "--hotspots",
        type=int,
        default=DEFAULT_HOTSPOT_LIMIT,
        metavar="N",
        help=f"Hotspot examples to quote back (default {DEFAULT_HOTSPOT_LIMIT})",
    )
    parser.add_argument(
        "--grade-target",
        type=float,
        default=None,
        metavar="N",
        help="Plain-language target Flesch-Kincaid grade (e.g. 8); flags files above it",
    )
    parser.add_argument(
        "--csv-out",
        metavar="FILE",
        default=None,
        help="Write batch results as CSV to this file",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format for stdout (default text; json prints structured data)",
    )
    parser.add_argument(
        "--ext",
        default=DEFAULT_EXTENSIONS,
        metavar="LIST",
        help=f"Comma-separated folder-scan extensions (default {DEFAULT_EXTENSIONS})",
    )
    parser.add_argument(
        "--no-recursive",
        action="store_true",
        help="Scan the folder only, not subfolders",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    return parser


def collect_files(
    root: Path, extensions: list[str], recursive: bool = True
) -> list[Path]:
    exts = {ext.lower() for ext in extensions}
    if recursive:
        candidates = (p for p in root.rglob("*") if p.is_file())
    else:
        candidates = (p for p in root.iterdir() if p.is_file())
    picked = [
        p
        for p in candidates
        if p.suffix.lower() in exts
        and not p.name.startswith(".")
        and not any(part.startswith(".") for part in p.relative_to(root).parts[:-1])
    ]
    return sorted(picked)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig", errors="replace")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    root = Path(args.path)
    if not root.exists():
        print(f"error: path does not exist: {root}", file=sys.stderr)
        return 1

    extensions = [ext.strip().lower() for ext in args.ext.split(",") if ext.strip()]
    if root.is_file():
        files = [root]
    else:
        files = collect_files(root, extensions, recursive=not args.no_recursive)
    if not files:
        print(
            f"error: no documents found under {root} (extensions: {', '.join(extensions)})",
            file=sys.stderr,
        )
        return 1

    lexicons: list[LexiconEntry] = []
    lexicon_names: list[str] = []
    try:
        for lexicon_path in args.lexicon:
            entries = load_lexicon(lexicon_path)
            lexicons.extend(entries)
            lexicon_names.append(str(lexicon_path))
    except OSError as exc:
        print(f"error: could not read lexicon: {exc}", file=sys.stderr)
        return 1

    def jargon_matcher(sentences: list[str]):
        return find_hits(sentences, lexicons)

    docs: list[DocReport] = []
    failures = 0
    for path in files:
        try:
            text = read_text(path)
        except OSError as exc:
            print(f"warning: could not read {path}: {exc}", file=sys.stderr)
            failures += 1
            continue
        display = str(path)
        docs.append(
            analyze_text(
                text,
                source=display,
                long_sentence_threshold=args.long_sentence,
                hotspot_limit=args.hotspots,
                jargon_matcher=jargon_matcher if lexicons else None,
            )
        )
    if not docs:
        print("error: no documents could be read", file=sys.stderr)
        return 1

    if args.format == "json":
        print(json_payload(docs))
    elif root.is_file():
        print(
            format_single_report(
                docs[0],
                lexicon_names=lexicon_names or None,
                long_sentence_threshold=args.long_sentence,
                hotspot_limit=args.hotspots,
                grade_target=args.grade_target,
            )
        )
    else:
        print(
            format_batch_report(
                docs,
                scanned_root=str(root),
                lexicon_names=lexicon_names or None,
                grade_target=args.grade_target,
            )
        )

    if args.csv_out:
        try:
            write_csv(args.csv_out, docs, grade_target=args.grade_target)
            print(f"CSV written: {args.csv_out}")
        except OSError as exc:
            print(f"error: could not write CSV: {exc}", file=sys.stderr)
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
