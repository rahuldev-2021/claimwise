"""Python-side verification that LLM output respects Phase 4 (SR-2)."""

from app.modules.llm.schemas.llm_assessment import (
    LLMAssessmentResponse,
    TechnicalAlignment,
)
from app.schemas.technical_validation import RepairJustificationStatus, TechnicalStatus, TechnicalValidationResult

_OVERCONFIDENT_PHRASES = (
    "fully supported",
    "definitely supported",
    "clearly justified",
    "no further evidence",
    "warranty should be approved",
)


def verify_respects_technical_validation(
    parsed: LLMAssessmentResponse,
    technical: TechnicalValidationResult,
) -> list[str]:
    """Independent of LLM boolean; returns validation errors."""
    errors: list[str] = []

    tv_status = technical.technical_status
    align = parsed.suggested_alignment

    if tv_status == TechnicalStatus.INSUFFICIENT_EVIDENCE and align == TechnicalAlignment.ALIGNED:
        errors.append("suggested_alignment ALIGNED conflicts with INSUFFICIENT_EVIDENCE")

    if tv_status == TechnicalStatus.NEEDS_REVIEW and align == TechnicalAlignment.ALIGNED:
        if technical.contradictory_evidence or technical.validation_findings:
            errors.append("suggested_alignment ALIGNED conflicts with NEEDS_REVIEW and contradictions")

    summary_lower = parsed.summary.lower()
    if tv_status == TechnicalStatus.INSUFFICIENT_EVIDENCE:
        for phrase in _OVERCONFIDENT_PHRASES:
            if phrase in summary_lower:
                errors.append(f"overconfident language while TV is INSUFFICIENT_EVIDENCE: {phrase}")

    tv_by_op = {a.normalized_operation: a for a in technical.repair_action_assessments}
    for interp in parsed.repair_interpretations:
        auth = tv_by_op.get(interp.normalized_operation)
        if auth is None:
            errors.append(f"unknown repair operation in LLM output: {interp.normalized_operation}")
            continue
        if interp.authoritative_justification_status != auth.justification_status:
            errors.append(
                f"operation {interp.normalized_operation}: LLM changed authoritative status "
                f"from {auth.justification_status.value}"
            )

    if parsed.technical_interpretation is not None:
        if parsed.technical_interpretation.advisory_status != tv_status.value:
            errors.append(
                "technical_interpretation.advisory_status must echo technical_validation.technical_status"
            )

    unjustified = sum(
        1
        for a in technical.repair_action_assessments
        if a.justification_status
        in (
            RepairJustificationStatus.NOT_SUFFICIENTLY_JUSTIFIED,
            RepairJustificationStatus.INSUFFICIENT_INFORMATION,
        )
    )
    if (
        unjustified
        and parsed.workflow_recommendation is not None
        and parsed.workflow_recommendation.type.value == "PROCEED_TO_HUMAN_REVIEW"
        and "all operations supported" in summary_lower
    ):
        errors.append("workflow implies full support while repair actions lack justification")

    return errors
