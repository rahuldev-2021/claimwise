"""Context selection and light compression.

Post-processes a ranked list of retrieved hits before they become cited
passages:

* **Parent-child context** — when a hit's metadata carries ``parent_text``
  (set at chunking time for long documents), it is attached so the passage can
  be understood in context.  Short documents have no parent text and are left
  as-is.
* **Redundancy removal** — near-duplicate passages (high token overlap with an
  already-kept passage) are dropped.  This is a deterministic Jaccard
  similarity check; it never rewrites or alters the text, so diagnostic
  meaning is preserved and nothing is invented.
* **Cap** — at most ``max_passages`` passages are kept, in rank order.

No LLM is used in this phase.
"""

from app.modules.rag.lexical_retriever import tokenize


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 1.0
    union = a | b
    if not union:
        return 0.0
    return len(a & b) / len(union)


class ContextBuilder:
    """Attaches parent context and removes redundant passages.

    ``parent_map`` maps ``chunk_id -> parent_text`` for chunks that have a
    parent window (long documents).  It is maintained by the ingestion
    pipeline and kept out of the vector store to avoid bloating metadata.
    """

    def __init__(
        self,
        max_passages: int = 5,
        dedup_threshold: float = 0.85,
        parent_map: dict[str, str] | None = None,
    ) -> None:
        self._max_passages = max(1, max_passages)
        self._dedup_threshold = dedup_threshold
        self._parent_map = parent_map or {}

    def build(self, hits: list) -> list:
        """Return a cleaned, capped list of hits (same type as input)."""
        kept: list = []
        kept_tokens: list[set[str]] = []

        for hit in hits:
            text = getattr(hit, "text", "") or ""
            tokens = set(tokenize(text))

            # Skip near-duplicates of an already-kept passage.
            if any(
                _jaccard(tokens, prev) >= self._dedup_threshold for prev in kept_tokens
            ):
                continue

            kept.append(hit)
            kept_tokens.append(tokens)
            if len(kept) >= self._max_passages:
                break

        return kept

    def parent_text_for(self, chunk_id: str) -> str | None:
        """Return the parent context for ``chunk_id``, if any."""
        parent = self._parent_map.get(chunk_id)
        if isinstance(parent, str) and parent.strip():
            return parent
        return None
