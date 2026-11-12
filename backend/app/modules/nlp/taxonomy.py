"""Taxonomy normalization: map surface forms to canonical automotive terms."""

import re
from typing import Optional

from app.modules.nlp.taxonomy_data import TAXONOMY_ALIASES


def _build_alias_index() -> dict[str, tuple[str, str]]:
    """Map lowercase alias -> (category, canonical)."""
    index: dict[str, tuple[str, str]] = {}
    for category, canonical_map in TAXONOMY_ALIASES.items():
        for canonical, aliases in canonical_map.items():
            for alias in aliases:
                key = alias.lower().strip()
                if key in index and index[key][1] != canonical:
                    continue
                index[key] = (category, canonical)
            index[canonical.lower()] = (category, canonical)
    return index


_ALIAS_INDEX = _build_alias_index()


def normalize_term(text: str, category: Optional[str] = None) -> tuple[str, str, str]:
    """Return (category, canonical, matched_surface) or passthrough as unknown."""
    lowered = text.lower().strip()
    if not lowered:
        return "unknown", "unknown", text

    entry = _ALIAS_INDEX.get(lowered)
    if entry:
        cat, canonical = entry
        if category is None or cat == category:
            return cat, canonical, text

    if category and category in TAXONOMY_ALIASES:
        for canonical, aliases in TAXONOMY_ALIASES[category].items():
            for alias in sorted(aliases, key=len, reverse=True):
                if re.search(r"\b" + re.escape(alias) + r"\b", lowered):
                    return category, canonical, alias

    return category or "unknown", _slugify(lowered), text


def _slugify(value: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return value or "unknown"


def lookup_aliases(category: str, canonical: str) -> list[str]:
    """Return known aliases for a canonical term in a category."""
    return list(TAXONOMY_ALIASES.get(category, {}).get(canonical, []))
