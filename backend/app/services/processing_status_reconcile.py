"""Align persisted claim processing flags with current platform state."""

from __future__ import annotations

from app.schemas.processing_status import OverallStatus, ProcessingStatus, StageStatus

_STALE_RAG_MARKERS = (
    "vector index is empty",
    "run post /api/v1/rag/ingest",
    "vector store unavailable",
)


def _is_stale_empty_index_rag_failure(error: str | None) -> bool:
    if not error:
        return True
    lowered = error.lower()
    return any(marker in lowered for marker in _STALE_RAG_MARKERS)


def reconcile_processing_status(
    ps: ProcessingStatus,
    *,
    rag_indexed: bool,
) -> ProcessingStatus:
    """Fix investigation snapshots that predate startup ingest or a warm index."""
    out = ps.model_copy(deep=True)

    if rag_indexed and out.rag.status == StageStatus.FAILED:
        if _is_stale_empty_index_rag_failure(out.rag.error):
            out.rag.status = StageStatus.COMPLETED
            out.rag.error = None

    has_failure = any(
        stage.status == StageStatus.FAILED
        for stage in (
            out.nlp,
            out.rag,
            out.technical_validation,
            out.financial_validation,
            out.recommendation,
        )
    ) or out.documents.failed > 0

    if not has_failure and out.overall == OverallStatus.FAILED:
        out.overall = OverallStatus.READY
    elif has_failure and out.rag.status != StageStatus.FAILED:
        if out.nlp.status != StageStatus.FAILED and out.documents.failed == 0:
            if out.overall == OverallStatus.FAILED and rag_indexed:
                out.overall = OverallStatus.READY

    return out
