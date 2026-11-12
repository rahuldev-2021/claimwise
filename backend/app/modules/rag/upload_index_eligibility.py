"""Decide whether a claim upload should be indexed in Chroma (rebuildable search index)."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import Enum

from app.modules.rag.document_cleaner import clean_text, is_blank
from app.schemas.repair_document import DocumentType, RepairDocument, VectorIndexStatus


class IndexAction(str, Enum):
    INDEX = "index"
    REINDEX = "reindex"
    SKIP = "skip"


@dataclass(frozen=True)
class UploadIndexEligibility:
    action: IndexAction
    reason: str
    fingerprint: str = ""


_UPLOAD_INDEX_TYPES: frozenset[DocumentType] = frozenset(
    {
        DocumentType.TECHNICIAN_REPORT,
        DocumentType.DIAGNOSTIC_REPORT,
        DocumentType.REPAIR_HISTORY,
        DocumentType.PART_REFERENCE,
        DocumentType.LABOUR_REFERENCE,
    }
)


def content_fingerprint(text: str) -> str:
    normalized = clean_text(text)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def assess_claim_upload_for_index(
    doc: RepairDocument,
    *,
    claim_id: str,
    org_id: str,
    min_text_chars: int,
    vector_store_has_document: bool,
) -> UploadIndexEligibility:
    """Fail closed: do not index empty, mis-scoped, or unsupported uploads."""
    fp = content_fingerprint(doc.content)

    if doc.org_id and doc.org_id != org_id:
        return UploadIndexEligibility(
            IndexAction.SKIP,
            "document org_id does not match claim",
            fp,
        )
    if doc.claim_id and doc.claim_id != claim_id:
        return UploadIndexEligibility(
            IndexAction.SKIP,
            "document claim_id does not match current claim",
            fp,
        )

    if doc.document_type not in _UPLOAD_INDEX_TYPES:
        return UploadIndexEligibility(
            IndexAction.SKIP,
            f"document type {doc.document_type.value} is not eligible for vector index",
            fp,
        )

    if is_blank(doc.content):
        return UploadIndexEligibility(IndexAction.SKIP, "empty document content", fp)

    cleaned = clean_text(doc.content)
    if len(cleaned) < min_text_chars:
        return UploadIndexEligibility(
            IndexAction.SKIP,
            f"extracted text shorter than minimum ({min_text_chars} chars)",
            fp,
        )

    stored_fp = (doc.content_fingerprint or "").strip()
    if (
        doc.vector_index_status == VectorIndexStatus.INDEXED
        and stored_fp == fp
        and vector_store_has_document
    ):
        return UploadIndexEligibility(
            IndexAction.SKIP,
            "already indexed with same content",
            fp,
        )

    if vector_store_has_document and stored_fp and stored_fp != fp:
        return UploadIndexEligibility(
            IndexAction.REINDEX,
            "content changed since last index",
            fp,
        )

    if vector_store_has_document and doc.vector_index_status == VectorIndexStatus.INDEXED:
        return UploadIndexEligibility(
            IndexAction.REINDEX,
            "reconcile vector index with Mongo record",
            fp,
        )

    return UploadIndexEligibility(IndexAction.INDEX, "eligible for indexing", fp)
