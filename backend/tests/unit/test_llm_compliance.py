from app.modules.llm.compliance import verify_respects_technical_validation
from app.modules.llm.schemas.llm_assessment import (
    LLMAssessmentResponse,
    TechnicalAlignment,
    TechnicalInterpretation,
)


def test_rejects_aligned_when_insufficient_evidence():
    from app.schemas.technical_validation import TechnicalStatus, TechnicalValidationResult

    tv = TechnicalValidationResult(
        claim_id="C1",
        technical_status=TechnicalStatus.INSUFFICIENT_EVIDENCE,
        diagnosis_summary="x",
        repair_assessment="y",
    )
    parsed = LLMAssessmentResponse(
        summary="fully supported repair",
        suggested_alignment=TechnicalAlignment.ALIGNED,
        technical_interpretation=TechnicalInterpretation(
            advisory_status=TechnicalStatus.INSUFFICIENT_EVIDENCE.value,
            explanation="",
        ),
    )
    errors = verify_respects_technical_validation(parsed, tv)
    assert any("INSUFFICIENT_EVIDENCE" in e for e in errors)
