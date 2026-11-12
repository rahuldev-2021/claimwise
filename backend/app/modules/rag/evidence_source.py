"""Evidence scope vs searchable source type for retrieval and review."""

from enum import Enum

from app.schemas.repair_document import RepairDocument


class EvidenceSourceType(str, Enum):
    """Where a retrieved passage originated — not a trust label."""

    GLOBAL_KNOWLEDGE = "GLOBAL_KNOWLEDGE"
    CLAIM_UPLOAD = "CLAIM_UPLOAD"


def resolve_evidence_source_type(*, evidence_scope: str) -> str:
    scope = (evidence_scope or "").strip().lower()
    if scope == "claim":
        return EvidenceSourceType.CLAIM_UPLOAD.value
    if scope == "global":
        return EvidenceSourceType.GLOBAL_KNOWLEDGE.value
    return ""


def resolve_from_document(doc: RepairDocument) -> str:
    scope = (doc.evidence_scope or "").strip().lower()
    if not scope and doc.claim_id:
        scope = "claim"
    elif not scope:
        scope = "global"
    return resolve_evidence_source_type(evidence_scope=scope)
