"""Citation and source traceability.

Converts normalized retrieval hits into fully-cited ``RetrievedPassage``
objects and assembles the final ``RetrievalResult``.  Every passage carries:

* document id, chunk id, original title, document type, verification status
* the retrieved text (and parent context when available)
* the retrieval method, score, rank, and rerank score (when present)

Citations are built only from data that was actually retrieved — nothing is
fabricated.  A document's ``verification_status`` is reported verbatim, so an
unverified source is never presented as verified.
"""

from typing import Callable

from app.modules.rag.schemas import (
    RetrievalResult,
    RetrievalStrategy,
    RetrievedPassage,
)


class CitationManager:
    """Builds cited retrieval results from normalized hits."""

    def __init__(
        self,
        document_lookup: Callable[[str], object] | None = None,
    ) -> None:
        # document_lookup maps document_id -> RepairDocument (or None).
        self._document_lookup = document_lookup

    def build_result(
        self,
        *,
        query: str,
        strategy: RetrievalStrategy,
        hits: list,
        rerank_scores: list[float | None] | None = None,
        parent_map: dict[str, str] | None = None,
        total_candidates: int = 0,
        embedding_model: str = "",
        embedding_dimension: int = 0,
    ) -> RetrievalResult:
        """Assemble a ``RetrievalResult`` from normalized hits.

        ``hits`` are objects exposing ``chunk_id``, ``document_id``, ``text``,
        ``score``, ``rank`` and ``metadata`` (the VectorHit / LexicalHit /
        HybridHit models all satisfy this).  ``rerank_scores`` is an optional
        parallel list aligned to ``hits``.
        """
        parent_map = parent_map or {}
        rerank_scores = rerank_scores or [None] * len(hits)

        passages: list[RetrievedPassage] = []
        for index, hit in enumerate(hits):
            metadata = getattr(hit, "metadata", None) or {}
            document_id = getattr(hit, "document_id", "") or ""
            title, document_type, verification_status = self._document_fields(
                document_id, metadata
            )
            evidence_scope = str(metadata.get("evidence_scope", "") or "")
            evidence_source_type = str(metadata.get("evidence_source_type", "") or "")
            passages.append(
                RetrievedPassage(
                    chunk_id=getattr(hit, "chunk_id", ""),
                    document_id=document_id,
                    title=title,
                    document_type=document_type,
                    verification_status=verification_status,
                    evidence_scope=evidence_scope,
                    evidence_source_type=evidence_source_type,
                    text=getattr(hit, "text", "") or "",
                    parent_text=parent_map.get(getattr(hit, "chunk_id", "")),
                    retrieval_method=strategy,
                    score=float(getattr(hit, "score", 0.0)),
                    rank=int(getattr(hit, "rank", index + 1)),
                    rerank_score=rerank_scores[index]
                    if index < len(rerank_scores)
                    else None,
                    metadata=dict(metadata),
                )
            )

        source_document_ids = _unique_in_order(
            p.document_id for p in passages if p.document_id
        )

        return RetrievalResult(
            query=query,
            strategy=strategy,
            passages=passages,
            source_document_ids=source_document_ids,
            total_candidates=total_candidates,
            embedding_model=embedding_model,
            embedding_dimension=embedding_dimension,
        )

    def _document_fields(
        self, document_id: str, metadata: dict[str, object]
    ) -> tuple[str, str, str]:
        """Resolve (title, document_type, verification_status) for a document.

        Prefers the authoritative document record when available; falls back
        to chunk metadata.  Never invents a title.
        """
        document_type = str(metadata.get("document_type", ""))
        verification_status = str(metadata.get("verification_status", ""))
        title = ""

        if self._document_lookup is not None and document_id:
            doc = self._document_lookup(document_id)
            if doc is not None:
                title = getattr(doc, "title", "") or ""
                doc_type = getattr(doc, "document_type", None)
                if doc_type is not None:
                    document_type = doc_type.value if hasattr(doc_type, "value") else str(doc_type)
                verif = getattr(doc, "verification_status", None)
                if verif is not None:
                    verification_status = verif.value if hasattr(verif, "value") else str(verif)

        return title, document_type, verification_status


def _unique_in_order(values) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result
