"""Text preprocessing for NLP pipeline. Preserves original text separately."""

import re
from dataclasses import dataclass

from app.modules.nlp.abbreviation_expander import AbbreviationResult, expand_abbreviations


@dataclass(frozen=True)
class PreprocessedText:
    original: str
    normalized: str
    norm_to_orig: tuple[int, ...] = ()


def preprocess_text(text: str | None) -> PreprocessedText:
    """Normalize text for matching without discarding the original."""
    original = text if text is not None else ""
    if not original.strip():
        return PreprocessedText(original=original, normalized="", norm_to_orig=())

    normalized = original.strip()
    normalized = re.sub(r"\s+", " ", normalized)
    normalized = re.sub(r"\s+([.,;:!?])", r"\1", normalized)
    normalized = normalized.lower()

    expanded: AbbreviationResult = expand_abbreviations(normalized)
    return PreprocessedText(
        original=original,
        normalized=expanded.normalized,
        norm_to_orig=expanded.norm_to_orig,
    )
