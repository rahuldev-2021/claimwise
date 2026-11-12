"""Detect explicit contradictions between claim text and evidence."""

import re

from app.modules.technical_validation.schemas import (
    ClassifiedEvidence,
    ContradictionFinding,
    EvidenceSupportClass,
)
from app.schemas.claim import ClaimInput

_NORMAL_VOLTAGE_RE = re.compile(r"\b(1[23]\.\d)\s*v\b", re.IGNORECASE)
_FAILURE_RE = re.compile(r"\b(failure|failed|defective|replace required)\b", re.IGNORECASE)


def detect_contradictions(
    claim: ClaimInput,
    classified: list[ClassifiedEvidence],
) -> tuple[list[ClassifiedEvidence], list[ContradictionFinding]]:
    """Mark contradictory passages and return findings."""
    findings: list[ContradictionFinding] = []
    updated: list[ClassifiedEvidence] = []

    complaint_negated = "no abnormal" in claim.customer_complaint.lower()
    diagnosis_noise = "noise" in claim.technician_diagnosis.lower()

    if complaint_negated and diagnosis_noise:
        findings.append(
            ContradictionFinding(
                code="COMPLAINT_VS_DIAGNOSIS_SYMPTOM",
                message="Customer denies symptoms; diagnosis documents symptoms.",
            )
        )

    diagnosis_failure = _FAILURE_RE.search(claim.technician_diagnosis)

    for item in classified:
        text = item.excerpt
        marked = item
        if diagnosis_failure and _NORMAL_VOLTAGE_RE.search(text):
            if "alternator" in text.lower() or "battery" in text.lower() or "charging" in text.lower():
                marked = _reclassify(item, EvidenceSupportClass.CONTRADICTORY)
                findings.append(
                    ContradictionFinding(
                        code="MEASUREMENT_VS_FAILURE_DIAGNOSIS",
                        message="Evidence shows nominal voltage/charging readings while diagnosis cites failure.",
                        related_document_id=item.document_id,
                    )
                )
        updated.append(marked)

    return updated, findings


def _reclassify(item: ClassifiedEvidence, support: EvidenceSupportClass) -> ClassifiedEvidence:
    return ClassifiedEvidence(
        document_id=item.document_id,
        chunk_id=item.chunk_id,
        title=item.title,
        document_type=item.document_type,
        verification_status=item.verification_status,
        excerpt=item.excerpt,
        support_class=support,
        retrieval_score=item.retrieval_score,
        quality_score=max(0.2, item.quality_score - 0.3),
        vehicle_applicable=item.vehicle_applicable,
        evidence_source_type=item.evidence_source_type,
        evidence_scope=item.evidence_scope,
        source_document_ids=item.source_document_ids,
        historical_repair_id=item.historical_repair_id,
        source_claim_id=item.source_claim_id,
        assessment_reason=item.assessment_reason,
    )
