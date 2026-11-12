"""Keep Chroma aligned with Mongo when claim evidence documents change."""

from __future__ import annotations

from datetime import datetime, timezone

from app.repositories.mongo_repair_document_repository import MongoRepairDocumentRepository
from app.schemas.repair_document import RepairDocument, VectorIndexStatus
from app.services.rag_service import RAGService


def remove_claim_document_from_search(
    *,
    document_id: str,
    org_id: str,
    documents: MongoRepairDocumentRepository,
    rag: RAGService,
) -> bool:
    """Delete vector chunks first; Mongo record removal is a separate explicit step."""
    rag.purge_document_from_index(document_id)
    return documents.update_fields(
        document_id,
        org_id,
        {
            "vector_index_status": VectorIndexStatus.PENDING.value,
            "vector_indexed_at": None,
            "vector_index_error": None,
        },
    )


def mark_document_replaced(
    *,
    document_id: str,
    org_id: str,
    updated: RepairDocument,
    documents: MongoRepairDocumentRepository,
    rag: RAGService,
) -> None:
    """Purge stale chunks so the next investigation re-indexes from Mongo."""
    rag.purge_document_from_index(document_id)
    payload = updated.model_dump(mode="json")
    payload.update(
        {
            "vector_index_status": VectorIndexStatus.PENDING.value,
            "vector_indexed_at": None,
            "vector_index_error": None,
        }
    )
    documents.update_fields(document_id, org_id, payload)
