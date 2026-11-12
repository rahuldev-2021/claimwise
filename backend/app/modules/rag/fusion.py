"""Reciprocal Rank Fusion (RRF).

RRF combines ranked lists from different retrieval methods without needing to
normalize their raw scores (which live on incompatible scales — cosine
similarity vs. BM25).  For each document, RRF sums ``1 / (k + rank)`` across
the lists in which it appears.  A higher RRF score means the document was
ranked highly by more methods.

Reference: Cormack, Clarke & Buttler, "Reciprocal Rank Fusion outperforms
Condorcet and individual Rank Learning Methods" (2009).
"""

from dataclasses import dataclass, field


@dataclass
class RankedItem:
    """A single ranked entry from one retrieval method."""

    chunk_id: str
    rank: int  # 1-based
    score: float
    document_id: str = ""
    text: str = ""
    metadata: dict[str, object] = field(default_factory=dict)


def reciprocal_rank_fusion(
    ranked_lists: list[list[RankedItem]],
    *,
    k: int = 60,
) -> list[RankedItem]:
    """Fuse multiple ranked lists into one deduplicated, ranked list.

    * ``k`` is the RRF constant (default 60, the standard value).  Larger ``k``
      dampens the influence of top ranks.
    * Items are deduplicated by ``chunk_id``; scores are summed across lists.
    * The original per-list score is preserved on the returned item (from the
      first list that contained the item) so callers can still report the
      raw method score alongside the fusion score.
    * Ties are broken by the lexicographically smallest chunk id for
      determinism.
    """
    if not ranked_lists:
        return []

    fused: dict[str, RankedItem] = {}
    for items in ranked_lists:
        for item in items:
            existing = fused.get(item.chunk_id)
            contribution = 1.0 / (k + item.rank)
            if existing is None:
                fused[item.chunk_id] = RankedItem(
                    chunk_id=item.chunk_id,
                    rank=item.rank,
                    score=contribution,
                    document_id=item.document_id,
                    text=item.text,
                    metadata=dict(item.metadata),
                )
            else:
                existing.score += contribution

    result = sorted(
        fused.values(),
        key=lambda item: (-item.score, item.chunk_id),
    )
    # Reassign 1-based ranks in the fused order.
    for new_rank, item in enumerate(result, start=1):
        item.rank = new_rank
    return result
