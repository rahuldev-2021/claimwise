"""Assess complaint vs diagnosis consistency using NLP structured output."""

from app.modules.nlp.schemas import NLPAnalysisResult
from app.modules.technical_validation.schemas import ComplaintDiagnosisAssessment
from app.schemas.claim import ClaimInput
from app.schemas.technical_validation import ConsistencyLevel


def assess_complaint_diagnosis(
    claim: ClaimInput,
    nlp: NLPAnalysisResult,
) -> ComplaintDiagnosisAssessment:
    comparison = nlp.complaint_diagnosis_comparison
    structured = nlp.structured_extraction

    matching = comparison.matching_components
    unrelated = comparison.unrelated_components
    symptom = structured.symptom
    component = structured.component

    complaint_blob = claim.customer_complaint.lower()
    diagnosis_blob = claim.technician_diagnosis.lower()

    if not diagnosis_blob.strip() or len(diagnosis_blob) < 15:
        return ComplaintDiagnosisAssessment(
            consistency=ConsistencyLevel.INSUFFICIENT_INFORMATION,
            summary="Technician diagnosis is missing or too brief for consistency assessment.",
        )

    negated_complaint = any(
        phrase in complaint_blob
        for phrase in ("no abnormal", "no noise", "not ", "without ")
    )
    noise_in_diagnosis = any(w in diagnosis_blob for w in ("noise", "rattle", "squeal", "vibration"))
    if negated_complaint and noise_in_diagnosis:
        return ComplaintDiagnosisAssessment(
            consistency=ConsistencyLevel.INCONSISTENT,
            summary="Customer text negates symptoms while diagnosis describes active symptoms.",
        )

    if matching:
        level = ConsistencyLevel.CONSISTENT if not unrelated else ConsistencyLevel.PARTIALLY_CONSISTENT
        summary = (
            f"Shared component context: {', '.join(matching)}."
            if matching
            else "Components align between complaint and diagnosis."
        )
        if unrelated:
            summary += f" Some terms differ: {', '.join(unrelated)}."
        if symptom:
            summary += f" Complaint symptom: {symptom.replace('_', ' ')}."
        return ComplaintDiagnosisAssessment(consistency=level, summary=summary)

    if symptom and component:
        return ComplaintDiagnosisAssessment(
            consistency=ConsistencyLevel.PARTIALLY_CONSISTENT,
            summary=(
                f"Structured extraction links symptom ({symptom}) and component ({component}) "
                "but explicit component overlap is limited."
            ),
        )

    if unrelated:
        return ComplaintDiagnosisAssessment(
            consistency=ConsistencyLevel.INCONSISTENT,
            summary=f"Component terminology differs: {', '.join(unrelated)}.",
        )

    return ComplaintDiagnosisAssessment(
        consistency=ConsistencyLevel.INSUFFICIENT_INFORMATION,
        summary="Insufficient structured overlap between complaint and diagnosis.",
    )
