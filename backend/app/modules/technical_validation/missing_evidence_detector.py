"""Identify missing evidence items for reviewer follow-up."""

from app.modules.nlp.schemas import NLPAnalysisResult
from app.modules.technical_validation.diagnostic_evidence_validator import (
    claim_has_measurement,
    retrieval_has_procedure_threshold,
)
from app.modules.technical_validation.schemas import ClassifiedEvidence, EvidenceSupportClass
from app.modules.rag.schemas import RetrievalResult
from app.schemas.claim import ClaimInput
from app.schemas.technical_validation import (
    ConsistencyLevel,
    FindingSeverity,
    MissingEvidenceFinding,
    MissingEvidenceScope,
)


def detect_missing_evidence(
    claim: ClaimInput,
    nlp: NLPAnalysisResult,
    retrieval: RetrievalResult,
    classified: list[ClassifiedEvidence],
    *,
    consistency: ConsistencyLevel,
    suspected_only: bool,
) -> tuple[list[str], list[MissingEvidenceFinding]]:
    legacy: list[str] = []
    structured: list[MissingEvidenceFinding] = []

    for item in nlp.missing_information:
        msg = f"{item.code}: {item.message}"
        structured.append(
            MissingEvidenceFinding(
                missing_item=item.message,
                source_scope_checked=MissingEvidenceScope.SUBMITTED_DIAGNOSIS,
                reason=msg,
                why_it_matters="NLP identified a gap in submitted claim text (advisory).",
                priority=FindingSeverity.INFO,
            )
        )

    for hint in nlp.repair_alignment_hints:
        if hint.type.value.startswith("missing_diagnostic"):
            legacy.append(f"NLP hint: {hint.description}")
            structured.append(
                MissingEvidenceFinding(
                    missing_item=hint.description,
                    source_scope_checked=MissingEvidenceScope.SUBMITTED_DIAGNOSIS,
                    reason="NLP repair alignment hint",
                )
            )

    if suspected_only and not claim_has_measurement(claim):
        has_direct = any(c.support_class == EvidenceSupportClass.DIRECT_SUPPORT for c in classified)
        if not has_direct:
            text = "Diagnostic measurements or fault codes to confirm suspected failure."
            legacy.append(text)
            structured.append(
                MissingEvidenceFinding(
                    missing_item="Measurements or DTC codes in submitted diagnosis",
                    source_scope_checked=MissingEvidenceScope.SUBMITTED_DIAGNOSIS,
                    reason=text,
                    why_it_matters="Diagnosis uses tentative language without corroborating measurements.",
                )
            )

    if retrieval_has_procedure_threshold(retrieval) and not claim_has_measurement(claim):
        text = "Inspection measurements referenced in procedure/evidence but not documented on the claim."
        legacy.append(text)
        structured.append(
            MissingEvidenceFinding(
                missing_item="Inspection measurements on claim",
                source_scope_checked=MissingEvidenceScope.RETRIEVED_KNOWLEDGE,
                reason=text,
                why_it_matters="Retrieved procedure mentions thresholds; claim text lacks measurements.",
            )
        )

    if consistency == ConsistencyLevel.INSUFFICIENT_INFORMATION:
        text = "Clearer technician diagnosis linking complaint to inspection findings."
        structured.append(
            MissingEvidenceFinding(
                missing_item="Diagnosis clarity",
                source_scope_checked=MissingEvidenceScope.SUBMITTED_DIAGNOSIS,
                reason=text,
                priority=FindingSeverity.INFO,
            )
        )

    if not retrieval.passages:
        text = "No relevant passages were found in the retrieved evidence for this query."
        legacy.append(text)
        structured.append(
            MissingEvidenceFinding(
                missing_item="Retrieved technical passages",
                source_scope_checked=MissingEvidenceScope.RETRIEVED_KNOWLEDGE,
                reason=text,
                why_it_matters="Empty retrieval does not prove knowledge is unavailable globally.",
            )
        )

    if not claim.supporting_document_ids:
        text = "Optional: supporting document IDs attached to the claim for cross-check."
        structured.append(
            MissingEvidenceFinding(
                missing_item="Supporting uploads",
                source_scope_checked=MissingEvidenceScope.CLAIM_UPLOAD,
                reason=text,
                priority=FindingSeverity.INFO,
            )
        )

    seen: set[str] = set()
    deduped_legacy: list[str] = []
    for m in legacy:
        key = m.lower()
        if key not in seen:
            seen.add(key)
            deduped_legacy.append(m)
    return deduped_legacy, structured
