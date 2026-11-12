from app.modules.llm.schemas.llm_assessment import LLMAssessmentResponse, TechnicalAlignment
from app.modules.llm.validation.response_parser import parse_json_dict
from app.modules.llm.validation.response_validator import EvidenceCatalog, validate_assessment_response
from app.modules.rag.schemas import RetrievalResult, RetrievalStrategy, RetrievedPassage
from app.schemas.technical_validation import EvidenceItem, TechnicalStatus, TechnicalValidationResult


def _catalog():
    retrieval = RetrievalResult(
        query="q",
        strategy=RetrievalStrategy.HYBRID,
        passages=[
            RetrievedPassage(
                chunk_id="c1",
                document_id="DOC-002",
                title="Pad",
                document_type="TECHNICIAN_REPORT",
                verification_status="VERIFIED",
                text="Pad thickness measured at 1.8 mm.",
                retrieval_method=RetrievalStrategy.HYBRID,
                score=0.8,
                rank=1,
            )
        ],
    )
    tv = TechnicalValidationResult(
        claim_id="CLM-002",
        technical_status=TechnicalStatus.QUESTIONABLE,
        diagnosis_summary="pads",
        repair_assessment="replace",
        supporting_evidence=[
            EvidenceItem(
                document_id="DOC-002",
                relevant_excerpt="Pad thickness measured at 1.8 mm.",
                evidence_type="supporting",
                chunk_id="c1",
            )
        ],
    )
    return EvidenceCatalog(retrieval, tv), tv


def test_valid_json_parses():
    raw = '{"summary":"ok","respects_technical_validation":true}'
    data = parse_json_dict(raw)
    assert data["summary"] == "ok"


def test_verbose_keys_stripped_before_validate():
    catalog, tv = _catalog()
    data = {
        "summary": "Brief summary.",
        "suggested_alignment": TechnicalAlignment.PARTIALLY_ALIGNED.value,
        "respects_technical_validation": True,
        "schema_version": "assessment_schema_v2",
        "technical_interpretation": {"advisory_status": "QUESTIONABLE", "explanation": "ok"},
        "diagnostic_gaps": ["should not appear"],
        "cited_evidence": [{"document_id": "DOC-FAKE", "excerpt": "bad"}],
        "repair_interpretations": [{"normalized_operation": "wrong", "authoritative_justification_status": "JUSTIFIED"}],
    }
    parsed, errors = validate_assessment_response(data, catalog=catalog, technical=tv)
    assert errors == []
    assert parsed is not None
    assert parsed.cited_evidence == []
    assert parsed.diagnostic_gaps == []


def test_minimal_response_model_dump():
    catalog, tv = _catalog()
    data = LLMAssessmentResponse(
        summary="x",
        technical_interpretation={"advisory_status": "QUESTIONABLE", "explanation": "x"},
    ).model_dump()
    parsed, errors = validate_assessment_response(data, catalog=catalog, technical=tv)
    assert parsed is not None
    assert not errors
