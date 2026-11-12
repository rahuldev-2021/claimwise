from app.modules.llm.validation.enrich_from_tv import build_template_assessment_from_tv, enrich_llm_payload_from_tv
from app.modules.llm.validation.response_validator import EvidenceCatalog, validate_assessment_response
from app.modules.rag.schemas import RetrievalResult, RetrievalStrategy
from app.schemas.technical_validation import (
    RepairActionAssessment,
    RepairJustificationStatus,
    TechnicalStatus,
    TechnicalValidationResult,
)


def test_enrich_adds_repair_rows_from_tv():
    tv = TechnicalValidationResult(
        claim_id="CLM-1",
        technical_status=TechnicalStatus.SUPPORTED,
        diagnosis_summary="d",
        repair_assessment="r",
        repair_action_assessments=[
            RepairActionAssessment(
                original_text="replace front brake pads",
                normalized_operation="replace front brake pads",
                justification_status=RepairJustificationStatus.JUSTIFIED,
                explanation="Pad below spec.",
            ),
            RepairActionAssessment(
                original_text="resurface rotors",
                normalized_operation="resurface rotors",
                justification_status=RepairJustificationStatus.PARTIALLY_JUSTIFIED,
                explanation="Within tolerance.",
            ),
        ],
    )
    data = enrich_llm_payload_from_tv(
        {
            "summary": "Pads justify replacement; rotor work is precautionary.",
            "suggested_alignment": "PARTIALLY_ALIGNED",
            "respects_technical_validation": True,
            "schema_version": "assessment_schema_v2",
            "technical_interpretation": {
                "advisory_status": "SUPPORTED",
                "explanation": "Supported.",
            },
        },
        tv,
    )
    assert len(data["repair_interpretations"]) == 2
    assert data["repair_interpretations"][0]["normalized_operation"] == "replace front brake pads"

    catalog = EvidenceCatalog(
        RetrievalResult(query="q", strategy=RetrievalStrategy.HYBRID, passages=[]),
        tv,
    )
    parsed, errors = validate_assessment_response(data, catalog=catalog, technical=tv)
    assert errors == []
    assert parsed is not None


def test_template_assessment_from_tv():
    tv = TechnicalValidationResult(
        claim_id="CLM-1",
        technical_status=TechnicalStatus.SUPPORTED,
        diagnosis_summary="d",
        repair_assessment="r",
        explanation="Pads below spec justify replacement.",
    )
    tpl = build_template_assessment_from_tv(tv)
    assert tpl.summary
    assert tpl.technical_interpretation.advisory_status == "SUPPORTED"
