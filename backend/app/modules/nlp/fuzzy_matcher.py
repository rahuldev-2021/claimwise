"""Controlled fuzzy matching for automotive taxonomy aliases."""

from dataclasses import dataclass
from difflib import SequenceMatcher
import re
from typing import Iterable

from app.modules.nlp.taxonomy_data import TAXONOMY_ALIASES

_STOPWORDS = frozenset(
    {
        "a",
        "an",
        "the",
        "and",
        "or",
        "at",
        "in",
        "on",
        "is",
        "was",
        "were",
        "with",
        "from",
        "to",
        "of",
        "for",
    }
)

_FUZZY_CATEGORIES = ("component", "part", "symptom", "failure_mode")


@dataclass(frozen=True)
class FuzzyAliasEntry:
    category: str
    canonical: str
    alias: str


@dataclass(frozen=True)
class FuzzyMatch:
    span_start: int
    span_end: int
    category: str
    canonical: str
    surface: str
    matched_alias: str
    ratio: float


def _build_fuzzy_catalog() -> list[FuzzyAliasEntry]:
    catalog: list[FuzzyAliasEntry] = []
    for category in _FUZZY_CATEGORIES:
        for canonical, aliases in TAXONOMY_ALIASES.get(category, {}).items():
            for alias in aliases:
                catalog.append(FuzzyAliasEntry(category, canonical, alias.lower()))
            catalog.append(FuzzyAliasEntry(category, canonical, canonical.replace("_", " ")))
    return catalog


_FUZZY_CATALOG = _build_fuzzy_catalog()


def _word_spans(text: str) -> list[tuple[int, int, str]]:
    return [(m.start(), m.end(), m.group().lower()) for m in re.finditer(r"[a-z0-9]+", text)]


def _overlaps_covered(start: int, end: int, covered: Iterable[tuple[int, int]]) -> bool:
    for c_start, c_end in covered:
        if start < c_end and end > c_start:
            return True
    return False


def _ratio(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


def find_fuzzy_matches(
    text: str,
    covered_spans: set[tuple[int, int]],
    *,
    threshold: float = 0.86,
    min_alias_len: int = 4,
    max_window_words: int = 4,
) -> list[FuzzyMatch]:
    """Return fuzzy alias hits for spans not already covered by exact matches."""
    if not text.strip():
        return []

    words = _word_spans(text)
    if not words:
        return []

    matches: list[FuzzyMatch] = []
    seen: set[tuple[int, int, str, str]] = set()

    for window_size in range(1, max_window_words + 1):
        for i in range(len(words) - window_size + 1):
            chunk = words[i : i + window_size]
            if all(w in _STOPWORDS for _, _, w in chunk):
                continue
            span_start = chunk[0][0]
            span_end = chunk[-1][1]
            if _overlaps_covered(span_start, span_end, covered_spans):
                continue
            phrase = " ".join(w for _, _, w in chunk)
            if len(phrase) < min_alias_len and window_size == 1:
                continue

            best: FuzzyMatch | None = None
            for entry in _FUZZY_CATALOG:
                if len(entry.alias) < min_alias_len and " " not in entry.alias:
                    continue
                if abs(len(entry.alias) - len(phrase)) > max(3, len(entry.alias) // 2):
                    continue
                r = _ratio(phrase, entry.alias)
                if r < threshold:
                    continue
                if best is None or r > best.ratio:
                    best = FuzzyMatch(
                        span_start=span_start,
                        span_end=span_end,
                        category=entry.category,
                        canonical=entry.canonical,
                        surface=text[span_start:span_end],
                        matched_alias=entry.alias,
                        ratio=round(r, 4),
                    )
            if best is not None:
                key = (best.span_start, best.span_end, best.category, best.canonical)
                if key not in seen:
                    seen.add(key)
                    matches.append(best)

    return matches
