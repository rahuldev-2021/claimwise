"""Central RAG retrieval pipeline.

Orchestrates the full retrieval flow:

    query / claim
      -> query construction (+ optional taxonomy expansion)
      -> metadata filtering
      -> semantic / lexical / hybrid retrieval (configurable strategy)
      -> optional reranking
      -> context selection (parent-child + dedup + cap)
      -> citation assembly
      -> structured RetrievalResult

The strategy is configurable so basic (semantic) and advanced (hybrid +
optional rerank) retrieval can be compared.  This module performs *evidence
retrieval only* — it never validates a repair or makes a recommendation.
"""

import logging
from typing import Optional

from app.modules.rag.citation_manager import CitationManager
from app.modules.rag.context_builder import ContextBuilder
from app.modules.rag.embedding_provider import EmbeddingProvider
from app.modules.rag.hybrid_retriever import HybridRetriever
from app.modules.rag.lexical_retriever import BM25Retriever
from app.modules.rag.metadata_filter import build_where
from app.modules.rag.query_processor import Query, QueryProcessor
from app.modules.rag.reranker import NoopReranker, Reranker, RerankerUnavailable
from app.modules.rag.schemas import (
    RetrievalMode,
    RetrievalResult,
    RetrievalStrategy,
)
from app.modules.rag.retrieval_access import (
    RetrievalAccessContext,
    filter_hits_by_scope,
)
from app.modules.rag.semantic_retriever import SemanticRetriever
from app.modules.rag.vector_store import VectorStore

logger = logging.getLogger(__name__)


class RetrievalPipeline:
    """Coordinates query processing, retrieval, rerank and citation."""

    def __init__(
        self,
        *,
        embeddings: EmbeddingProvider,
        store: VectorStore,
        lexical: BM25Retriever,
        query_processor: QueryProcessor | None = None,
        reranker: Reranker | None = None,
        context_builder: ContextBuilder | None = None,
        citation_manager: CitationManager | None = None,
        parent_map: dict[str, str] | None = None,
        rrf_k: int = 60,
        retrieval_depth: int = 20,
        relevance_threshold: float = 0.0,
        scope_fetch_multiplier: int = 4,
    ) -> None:
        self._embeddings = embeddings
        self._store = store
        self._lexical = lexical
        self._query_processor = query_processor or QueryProcessor()
        self._reranker = reranker or NoopReranker()
        self._parent_map = parent_map or {}
        self._context_builder = context_builder or ContextBuilder(parent_map=self._parent_map)
        self._citation_manager = citation_manager or CitationManager()
        self._rrf_k = rrf_k
        self._retrieval_depth = retrieval_depth
        self._relevance_threshold = relevance_threshold
        self._scope_fetch_multiplier = max(1, scope_fetch_multiplier)

        self._semantic = SemanticRetriever(embeddings, store)
        self._hybrid = HybridRetriever(
            self._semantic, lexical, rrf_k=rrf_k, retrieval_depth=retrieval_depth
        )

    # ── public API ────────────────────────────────────────────────────

    def retrieve(
        self,
        query: str,
        *,
        top_k: int = 5,
        mode: RetrievalMode = RetrievalMode.ADVANCED,
        where: dict[str, object] | None = None,
        expand: bool = True,
        rerank: bool = False,
    ) -> RetrievalResult:
        """Retrieve evidence for a raw text query."""
        q = self._query_processor.build_from_text(query)
        return self._run(
            q, top_k=top_k, mode=mode, where=where, rerank=rerank, access=None
        )

    def retrieve_for_claim(
        self,
        claim: object,
        nlp_result: object | None = None,
        *,
        top_k: int = 5,
        mode: RetrievalMode = RetrievalMode.ADVANCED,
        filter_fields: tuple[str, ...] = ("repair_category",),
        expand: bool = True,
        rerank: bool = False,
        min_passages_fallback: int = 2,
        fallback_filter_fields: tuple[str, ...] = ("repair_category",),
        access: RetrievalAccessContext | None = None,
    ) -> RetrievalResult:
        """Retrieve evidence for a claim, reusing NLP output for the query.

        When strict metadata filters return too few passages, re-query with
        relaxed filters (fallback_filter_fields) and set ``filter_fallback_applied``.
        """
        from app.modules.rag.metadata_filter import build_from_claim

        q = self._query_processor.build_from_claim(claim, nlp_result, expand=expand)
        where = build_from_claim(claim, fields=filter_fields)
        result = self._run(
            q,
            top_k=top_k,
            mode=mode,
            where=where,
            rerank=rerank,
            access=access,
        )
        if (
            len(result.passages) < min_passages_fallback
            and filter_fields != fallback_filter_fields
        ):
            where_relaxed = build_from_claim(claim, fields=fallback_filter_fields)
            relaxed = self._run(
                q,
                top_k=top_k,
                mode=mode,
                where=where_relaxed,
                rerank=rerank,
                access=access,
            )
            if len(relaxed.passages) > len(result.passages):
                relaxed.filter_fallback_applied = True
                return relaxed
        return result

    def retrieve_chunk_ids(
        self,
        query: str,
        *,
        top_k: int = 5,
        mode: RetrievalMode = RetrievalMode.ADVANCED,
        where: dict[str, object] | None = None,
    ) -> list[str]:
        """Return just the ranked chunk ids (used by the evaluation harness)."""
        result = self.retrieve(
            query, top_k=top_k, mode=mode, where=where, expand=False
        )
        return [p.chunk_id for p in result.passages]

    # ── internals ─────────────────────────────────────────────────────

    def _run(
        self,
        q: Query,
        *,
        top_k: int,
        mode: RetrievalMode,
        where: dict[str, object] | None,
        rerank: bool,
        access: RetrievalAccessContext | None = None,
    ) -> RetrievalResult:
        search_text = q.full_text
        strategy = (
            RetrievalStrategy.SEMANTIC
            if mode == RetrievalMode.BASIC
            else RetrievalStrategy.HYBRID
        )

        pool_size = max(self._retrieval_depth, top_k * 2)
        max_pool = max(pool_size, top_k * self._scope_fetch_multiplier)
        hits: list = []
        total_candidates = 0
        while pool_size <= max_pool:
            hits = self._fetch_hits(
                search_text, mode=mode, where=where, pool_size=pool_size
            )
            total_candidates = len(hits)
            scoped = filter_hits_by_scope(hits, access)
            if len(scoped) >= top_k or pool_size >= max_pool:
                hits = scoped
                break
            pool_size *= 2
        else:
            hits = filter_hits_by_scope(hits, access)

        hits = hits[:top_k]

        # Optional reranking (degrades gracefully if the model is unavailable).
        rerank_scores: list[float | None] | None = None
        if rerank and hits:
            hits, rerank_scores = self._apply_rerank(search_text, hits)

        # Context selection: parent-child + dedup + cap.
        hits = self._context_builder.build(hits)

        return self._citation_manager.build_result(
            query=q.original,
            strategy=strategy,
            hits=hits,
            rerank_scores=rerank_scores,
            parent_map=self._parent_map,
            total_candidates=total_candidates,
            embedding_model=self._embeddings.model_name,
            embedding_dimension=self._embeddings.dimension,
        )

    def _apply_rerank(
        self, query: str, hits: list
    ) -> tuple[list, list[float | None]]:
        """Rerank hits; fall back to original order if the reranker fails."""
        passages = [{"text": h.text} for h in hits]
        try:
            scores = self._reranker.rerank(query, passages)
        except RerankerUnavailable as exc:
            logger.warning("Reranker unavailable, using original order: %s", exc)
            return hits, [None] * len(hits)

        # Sort by rerank score (desc), keeping original retrieval score intact.
        order = sorted(
            range(len(hits)),
            key=lambda i: (scores[i] is None, -(scores[i] or 0.0)),
        )
        reordered = [hits[i] for i in order]
        reordered_scores = [scores[i] for i in order]
        # Reassign ranks after reranking.
        for new_rank, hit in enumerate(reordered, start=1):
            hit.rank = new_rank
        return reordered, reordered_scores

    def _fetch_hits(
        self,
        search_text: str,
        *,
        mode: RetrievalMode,
        where: dict[str, object] | None,
        pool_size: int,
    ) -> list:
        if mode == RetrievalMode.BASIC:
            hits = self._semantic.retrieve(search_text, top_k=pool_size, where=where)
            if self._relevance_threshold > 0.0:
                hits = [h for h in hits if h.score >= self._relevance_threshold]
            return hits
        return self._hybrid.retrieve(search_text, top_k=pool_size, where=where)
