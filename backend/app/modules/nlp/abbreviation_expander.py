"""Conservative abbreviation expansion with normalized-to-original index mapping."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from functools import lru_cache

from app.modules.nlp.versions import ABBREVIATIONS_FILE


@dataclass(frozen=True)
class AbbreviationResult:
    normalized: str
    norm_to_orig: tuple[int, ...]


@lru_cache(maxsize=1)
def _load_patterns() -> list[tuple[re.Pattern[str], str]]:
    try:
        data = json.loads(ABBREVIATIONS_FILE.read_text(encoding="utf-8"))
    except OSError:
        return []
    patterns: list[tuple[re.Pattern[str], str]] = []
    for item in data.get("replacements", []):
        flags = re.IGNORECASE if item.get("ignore_case", True) else 0
        patterns.append((re.compile(item["pattern"], flags), item["replacement"]))
    return patterns


def expand_abbreviations(text: str) -> AbbreviationResult:
    if not text:
        return AbbreviationResult(normalized="", norm_to_orig=())

    chars = list(text)
    norm_to_orig = list(range(len(text)))

    for pattern, replacement in _load_patterns():
        joined = "".join(chars)
        offset = 0
        for match in pattern.finditer(joined):
            start = match.start() + offset
            end = match.end() + offset
            repl = list(replacement)
            old_len = end - start
            new_len = len(repl)
            orig_anchor = norm_to_orig[start] if start < len(norm_to_orig) else start
            orig_indices = norm_to_orig[start:end] or [orig_anchor]
            chars[start:end] = repl
            mapped = []
            for i in range(new_len):
                if new_len == len(orig_indices):
                    mapped.append(orig_indices[i])
                else:
                    mapped.append(orig_indices[min(i, len(orig_indices) - 1)])
            norm_to_orig = norm_to_orig[:start] + mapped + norm_to_orig[end:]
            offset += new_len - old_len

    return AbbreviationResult(normalized="".join(chars), norm_to_orig=tuple(norm_to_orig))


def map_span_to_original(
    norm_to_orig: tuple[int, ...], span_start: int, span_end: int
) -> tuple[int, int]:
    if not norm_to_orig or span_start >= len(norm_to_orig):
        return span_start, span_end
    end_idx = min(max(span_end - 1, span_start), len(norm_to_orig) - 1)
    return norm_to_orig[span_start], norm_to_orig[end_idx] + 1


def excerpt_from_original(original: str, surface: str) -> str:
    if not surface:
        return ""
    m = re.search(re.escape(surface), original, re.IGNORECASE)
    if m:
        return original[m.start() : m.end()]
    return surface
