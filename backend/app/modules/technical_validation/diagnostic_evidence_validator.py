"""Classify retrieved passages by document type and textual signals."""

import re

from app.modules.rag.schemas import RetrievedPassage, RetrievalResult
from app.modules.technical_validation.evidence.evidence_trust_policy import (
    assess_passage_trust,
    display_quality_score,
)
from app.modules.technical_validation.schemas import ClassifiedEvidence, EvidenceSupportClass
from app.schemas.claim import ClaimInput

_MEASUREMENT_RE = re.compile(
    r"\b(\d+(?:\.\d+)?)\s*(?:mm|v|volts?|psi|°\s*[fc]|p0\d{3})\b",
    re.IGNORECASE,
)
_INSPECTION_RE = re.compile(
    r"\b(measured|inspection|tested|pressure test|load test|visual inspection|thickness)\b",
    re.IGNORECASE,
)
_DTC_RE = re.compile(r"\bP\d{4}\b", re.IGNORECASE)
_THRESHOLD_RE = re.compile(r"\b(minimum|specification|threshold|below)\b", re.IGNORECASE)


def classify_retrieval(claim: ClaimInput, retrieval: RetrievalResult) -> list[ClassifiedEvidence]:
    repair_category = (claim.recommended_repair.repair_category or "").upper()
    structured = None
    results: list[ClassifiedEvidence] = []
    for passage in retrieval.passages:
        results.append(
            _classify_passage(passage, claim, repair_category),
        )
    return results


def _classify_passage(
    passage: RetrievedPassage,
    claim: ClaimInput,
    repair_category: str,
) -> ClassifiedEvidence:
    text = passage.text
    doc_type = (passage.document_type or "").upper()
    vehicle_ok = _vehicle_applicable(passage.metadata, claim)

    support = EvidenceSupportClass.INSUFFICIENT
    if doc_type == "REPAIR_HISTORY":
        support = EvidenceSupportClass.INDIRECT_SUPPORT
    elif doc_type in ("LABOUR_REFERENCE", "PART_REFERENCE"):
        support = EvidenceSupportClass.CONTEXTUAL
    elif doc_type in ("TECHNICIAN_REPORT", "DIAGNOSTIC_REPORT"):
        if _MEASUREMENT_RE.search(text) or _DTC_RE.search(text) or _INSPECTION_RE.search(text):
            support = EvidenceSupportClass.DIRECT_SUPPORT
        else:
            support = EvidenceSupportClass.INDIRECT_SUPPORT
    else:
        support = EvidenceSupportClass.CONTEXTUAL

    meta_cat = str(passage.metadata.get("repair_category", "")).upper()
    if repair_category and meta_cat and repair_category != meta_cat:
        if support == EvidenceSupportClass.DIRECT_SUPPORT:
            support = EvidenceSupportClass.INDIRECT_SUPPORT

    if not vehicle_ok and support != EvidenceSupportClass.CONTEXTUAL:
        support = EvidenceSupportClass.INDIRECT_SUPPORT

    dims = assess_passage_trust(
        passage, claim, support_class=support, vehicle_applicable=vehicle_ok
    )
    quality = display_quality_score(dims)
    excerpt = passage.text[:500] if len(passage.text) > 500 else passage.text

    source_type = passage.evidence_source_type or str(
        passage.metadata.get("evidence_source_type", "")
    )
    scope = passage.evidence_scope or str(passage.metadata.get("evidence_scope", ""))

    return ClassifiedEvidence(
        document_id=passage.document_id,
        chunk_id=passage.chunk_id,
        title=passage.title,
        document_type=passage.document_type,
        verification_status=passage.verification_status,
        excerpt=excerpt,
        support_class=support,
        retrieval_score=passage.score,
        quality_score=quality,
        vehicle_applicable=vehicle_ok,
        evidence_source_type=source_type,
        evidence_scope=scope,
        source_document_ids=_meta_str(passage.metadata.get("source_document_ids")),
        historical_repair_id=_meta_str(passage.metadata.get("historical_repair_id")),
        source_claim_id=_meta_str(passage.metadata.get("source_claim_id")),
        assessment_reason=dims.trust_summary,
    )


def _meta_str(value: object) -> str | None:
    if value is None:
        return None
    return str(value)


def _vehicle_applicable(metadata: dict, claim: ClaimInput) -> bool:
    make = metadata.get("vehicle_make")
    model = metadata.get("vehicle_model")
    year = metadata.get("model_year")
    if make and make != claim.vehicle.make:
        return False
    if model and model != claim.vehicle.model:
        return False
    if year is not None and year != claim.vehicle.model_year:
        return False
    return True


def claim_has_measurement(claim: ClaimInput) -> bool:
    blob = f"{claim.customer_complaint} {claim.technician_diagnosis}"
    return bool(_MEASUREMENT_RE.search(blob) or _DTC_RE.search(blob))


def retrieval_has_procedure_threshold(retrieval: RetrievalResult) -> bool:
    for passage in retrieval.passages:
        if (passage.document_type or "").upper() in ("LABOUR_REFERENCE", "PART_REFERENCE"):
            if _THRESHOLD_RE.search(passage.text) or _MEASUREMENT_RE.search(passage.text):
                return True
        if _THRESHOLD_RE.search(passage.text) and _MEASUREMENT_RE.search(passage.text):
            return True
    return False
