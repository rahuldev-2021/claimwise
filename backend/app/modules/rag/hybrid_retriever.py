"""Hybrid retrieval: semantic + lexical fused with Reciprocal Rank Fusion.

Runs both the semantic and lexical retrievers over the same (optionally
expanded) query, then fuses the two ranked lists with RRF.  The result is a
single deduplicated, ranked list where each entry carries:

* ``rrf_score`` — the fusion score used for final ranking.
* ``semantic_score`` / ``lexical_score`` — the original per-method scores
  (``None`` when that method did not return the chunk).

This preserves the provenance of each score rather than blending raw,
incompatible numbers.
"""

from app.modules.rag.fusion import RankedItem, reciprocal_rank_fusion
from app.modules.rag.lexical_retriever import BM25Retriever
from app.modules.rag.schemas import HybridHit
from app.modules.rag.semantic_retriever import SemanticRetriever


class HybridRetriever:
    """Combines semantic and lexical retrieval with RRF."""

    def __init__(
        self,
        semantic: SemanticRetriever,
        lexical: BM25Retriever,
        *,
        rrf_k: int = 60,
        retrieval_depth: int = 20,
    ) -> None:
        self._semantic = semantic
        self._lexical = lexical
        self._rrf_k = rrf_k
        self._retrieval_depth = retrieval_depth

    def retrieve(
        self,
        query: str,
        *,
        top_k: int = 5,
        where: dict[str, object] | None = None,
    ) -> list[HybridHit]:
        """Retrieve and fuse.  ``retrieval_depth`` controls how many candidates
        each method returns before fusion; ``top_k`` is the final list size."""
        if not query or not query.strip():
            return []

        depth = max(self._retrieval_depth, top_k)
        semantic_hits = self._semantic.retrieve(query, top_k=depth, where=where)
        lexical_hits = self._lexical.retrieve(query, top_k=depth, where=where)

        semantic_items = [
            RankedItem(
                chunk_id=h.chunk_id,
                rank=h.rank,
                score=h.score,
                document_id=h.document_id,
                text=h.text,
                metadata=h.metadata,
            )
            for h in semantic_hits
        ]
        lexical_items = [
            RankedItem(
                chunk_id=h.chunk_id,
                rank=h.rank,
                score=h.score,
                document_id=h.document_id,
                text=h.text,
                metadata=h.metadata,
            )
            for h in lexical_hits
        ]

        fused = reciprocal_rank_fusion(
            [semantic_items, lexical_items], k=self._rrf_k
        )

        # Index original scores by chunk id for provenance.
        semantic_scores = {h.chunk_id: h.score for h in semantic_hits}
        lexical_scores = {h.chunk_id: h.score for h in lexical_hits}

        hits: list[HybridHit] = []
        for item in fused[:top_k]:
            hits.append(
                HybridHit(
                    chunk_id=item.chunk_id,
                    document_id=item.document_id,
                    text=item.text,
                    rrf_score=round(item.score, 6),
                    rank=item.rank,
                    semantic_score=semantic_scores.get(item.chunk_id),
                    lexical_score=lexical_scores.get(item.chunk_id),
                    metadata=dict(item.metadata),
                )
            )
        return hits
