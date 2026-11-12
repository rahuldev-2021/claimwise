"""Treat dealer-submitted inspection narrative as attestable direct evidence when measurable."""

from app.modules.technical_validation.diagnostic_evidence_validator import claim_has_measurement
from app.modules.technical_validation.schemas import ClassifiedEvidence
from app.schemas.claim import ClaimInput
from app.schemas.technical_validation import EvidenceItem, EvidenceSupportClass

CLAIM_SUBMISSION_DOC_ID = "CLAIM_SUBMISSION"
CLAIM_SUBMISSION_CHUNK_ID = "claim-diagnosis"


def build_claim_attested_evidence(claim: ClaimInput) -> tuple[ClassifiedEvidence, EvidenceItem] | None:
    """When diagnosis/complaint documents measurements or DTCs, treat as submitted inspection."""
    if not claim_has_measurement(claim):
        return None
    diagnosis = (claim.technician_diagnosis or "").strip()
    if not diagnosis:
        return None
    excerpt = diagnosis[:500]
    classified = ClassifiedEvidence(
        document_id=CLAIM_SUBMISSION_DOC_ID,
        chunk_id=CLAIM_SUBMISSION_CHUNK_ID,
        title="Dealer-submitted technician diagnosis",
        document_type="DIAGNOSTIC_REPORT",
        verification_status="VERIFIED",
        excerpt=excerpt,
        support_class=EvidenceSupportClass.DIRECT_SUPPORT,
        retrieval_score=1.0,
        quality_score=1.0,
        vehicle_applicable=True,
        evidence_source_type="CLAIM_SUBMISSION",
        evidence_scope="CURRENT_CLAIM",
        source_claim_id=claim.claim_id,
        assessment_reason="Submitted diagnosis includes documented measurements or fault codes.",
    )
    item = EvidenceItem(
        document_id=CLAIM_SUBMISSION_DOC_ID,
        relevant_excerpt=excerpt,
        evidence_type="supporting",
        chunk_id=CLAIM_SUBMISSION_CHUNK_ID,
        title=classified.title,
        document_type=classified.document_type,
        verification_status=classified.verification_status,
        support_class=EvidenceSupportClass.DIRECT_SUPPORT.value,
        evidence_source_type=classified.evidence_source_type,
        evidence_scope=classified.evidence_scope,
    )
    return classified, item
