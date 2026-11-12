"""Text normalization for RAG document ingestion.

Unlike the NLP preprocessing step (which lowercases for entity matching),
RAG cleaning preserves original case so that part numbers, fault codes and
proper nouns remain searchable and quotable.  It only normalizes whitespace
and strips surrounding blank lines.
"""

import re


def clean_text(text: str | None) -> str:
    """Normalize whitespace while preserving case and technical tokens.

    * Collapses runs of whitespace (spaces, tabs, newlines) to a single space.
    * Strips leading/trailing whitespace.
    * Returns an empty string for ``None`` or blank input.
    """
    if text is None:
        return ""
    normalized = re.sub(r"\s+", " ", text).strip()
    return normalized


def is_blank(text: str | None) -> bool:
    """True when the text is ``None`` or contains no non-whitespace chars."""
    return not (text or "").strip()
