"""Map RAG passages to EvidenceItem with full provenance."""

from app.modules.rag.schemas import RetrievedPassage
from app.modules.technical_validation.schemas import ClassifiedEvidence
from app.schemas.technical_validation import EvidenceItem, EvidenceSupportClass


def passage_to_evidence_item(
    item: ClassifiedEvidence,
    *,
    evidence_type: str,
) -> EvidenceItem:
    meta = {}
    return EvidenceItem(
        document_id=item.document_id,
        relevant_excerpt=item.excerpt,
        evidence_type=evidence_type,
        chunk_id=item.chunk_id,
        title=item.title,
        document_type=item.document_type,
        verification_status=item.verification_status,
        evidence_source_type=item.evidence_source_type or None,
        evidence_scope=getattr(item, "evidence_scope", None) or None,
        source_document_ids=getattr(item, "source_document_ids", None),
        historical_repair_id=getattr(item, "historical_repair_id", None),
        source_claim_id=getattr(item, "source_claim_id", None),
        assessment_reason=getattr(item, "assessment_reason", None),
        support_class=item.support_class,
        retrieval_score=item.retrieval_score,
        quality_score=item.quality_score,
        relevance_score=item.quality_score,
    )


def enrich_classified_from_passage(
    classified: ClassifiedEvidence,
    passage: RetrievedPassage,
    *,
    assessment_reason: str | None = None,
) -> ClassifiedEvidence:
    return ClassifiedEvidence(
        document_id=classified.document_id,
        chunk_id=classified.chunk_id,
        title=classified.title,
        document_type=classified.document_type,
        verification_status=classified.verification_status,
        excerpt=classified.excerpt,
        support_class=classified.support_class,
        retrieval_score=classified.retrieval_score,
        quality_score=classified.quality_score,
        vehicle_applicable=classified.vehicle_applicable,
        evidence_source_type=passage.evidence_source_type
        or str(passage.metadata.get("evidence_source_type", "")),
        evidence_scope=passage.evidence_scope
        or str(passage.metadata.get("evidence_scope", "")),
        source_document_ids=_meta_str(passage.metadata.get("source_document_ids")),
        historical_repair_id=_meta_str(passage.metadata.get("historical_repair_id")),
        source_claim_id=_meta_str(passage.metadata.get("source_claim_id")),
        assessment_reason=assessment_reason,
    )


def _meta_str(value: object) -> str | None:
    if value is None:
        return None
    return str(value)
