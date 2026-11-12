"""Query construction and lightweight expansion.

Builds a retrieval query from a claim (or raw text) and optionally expands it
with canonical automotive terms and known synonyms drawn from the existing NLP
taxonomy.  Expansion is deliberately conservative:

* The original query is always preserved and searched first.
* Only terms that are *relevant* to the claim (its structured extraction and
  recommended repair) are added — no unrelated expansion.
* Expansion is capped (``max_expansions``) and can be disabled entirely.
* This is a deterministic, taxonomy-driven expansion.  The interface is shaped
  so a future LLM-based rewriter (Phase 5, Gemini) can replace it without
  changing the pipeline.
"""

from dataclasses import dataclass, field

from app.modules.nlp.taxonomy import lookup_aliases


@dataclass
class Query:
    """A retrieval query with its provenance and optional expansions."""

    original: str
    expanded_terms: list[str] = field(default_factory=list)
    source: str = "text"  # "text" | "claim"

    @property
    def full_text(self) -> str:
        """The text actually sent to the retrievers.

        The original query leads, followed by distinct expansion terms joined
        with ``;`` so each term is independently searchable.
        """
        parts = [self.original]
        seen = {self.original.lower()}
        for term in self.expanded_terms:
            key = term.lower()
            if key not in seen:
                seen.add(key)
                parts.append(term)
        return "; ".join(parts)


# Categories whose canonical terms are useful for expanding a retrieval query.
_EXPANSION_CATEGORIES = ("component", "part", "symptom", "failure_mode")


class QueryProcessor:
    """Builds and expands retrieval queries."""

    def __init__(self, max_expansions: int = 8) -> None:
        self._max_expansions = max(0, max_expansions)

    def build_from_text(self, text: str) -> Query:
        """Build a query from raw text with no expansion."""
        return Query(original=text.strip(), source="text")

    def build_from_claim(
        self,
        claim: object,
        nlp_result: object | None = None,
        *,
        expand: bool = True,
    ) -> Query:
        """Build a query from a claim, optionally expanding via the taxonomy.

        The base query combines the customer complaint, technician diagnosis
        and recommended-repair text.  When ``expand`` is true and an
        ``nlp_result`` (with ``structured_extraction``) is supplied, canonical
        terms and aliases are appended (capped at ``max_expansions``).
        """
        complaint = getattr(claim, "customer_complaint", "") or ""
        diagnosis = getattr(claim, "technician_diagnosis", "") or ""
        repair = getattr(claim, "recommended_repair", None)
        repair_bits = []
        if repair is not None:
            for attr in ("repair_category", "part_description", "recommended_action"):
                value = getattr(repair, attr, None)
                if value:
                    repair_bits.append(str(value))

        original = " ".join(
            filter(None, [complaint.strip(), diagnosis.strip(), " ".join(repair_bits)])
        ).strip()

        query = Query(original=original, source="claim")
        if expand and self._max_expansions > 0:
            structured = getattr(nlp_result, "structured_extraction", None)
            query.expanded_terms = self._expand(claim, structured)
        return query

    # ── expansion ─────────────────────────────────────────────────────

    def _expand(self, claim: object, structured: object | None) -> list[str]:
        """Collect relevant canonical terms + aliases, capped and deduped."""
        terms: list[str] = []
        seen: set[str] = set()

        def add(term: str) -> None:
            if not term:
                return
            key = term.lower()
            if key in seen:
                return
            seen.add(key)
            terms.append(term)

        if structured is not None:
            for category in _EXPANSION_CATEGORIES:
                canonical = getattr(structured, category, None)
                if not canonical:
                    continue
                add(canonical.replace("_", " "))
                for alias in lookup_aliases(category, canonical):
                    add(alias)

        # Also expand from the recommended repair's part description.
        repair = getattr(claim, "recommended_repair", None)
        if repair is not None:
            description = getattr(repair, "part_description", None)
            if description:
                add(description)

        return terms[: self._max_expansions]
