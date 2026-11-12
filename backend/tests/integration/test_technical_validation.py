"""Integration tests for technical validation service and pipeline."""

import pytest

from app.modules.technical_validation.technical_validation_pipeline import validate_technical
from app.schemas.technical_validation import EvidenceSupportClass, TechnicalStatus
from app.services.nlp_analysis_service import NLPAnalysisService
from app.services.technical_validation_service import TechnicalValidationService


@pytest.fixture()
def tv_service(settings, indexed_rag):
    service = TechnicalValidationService.for_tests(settings)
    service._rag = indexed_rag
    return service


def test_clm002_not_blind_supported(repository, tv_service):
    """Scenario A: direct measurement evidence may appear but verdict stays reviewable."""
    claim = repository.get_claim("CLM-002")
    result = tv_service.analyze_claim(claim, top_k=5)
    if result.technical_status == TechnicalStatus.SUPPORTED:
        direct = [
            e
            for e in result.supporting_evidence
            if e.support_class == EvidenceSupportClass.DIRECT_SUPPORT
        ]
        assert direct, "SUPPORTED requires direct supporting evidence"
        assert result.human_review_required is False
    else:
        assert result.technical_status in (
            TechnicalStatus.QUESTIONABLE,
            TechnicalStatus.NEEDS_REVIEW,
            TechnicalStatus.INSUFFICIENT_EVIDENCE,
        )
    assert result.human_review_required or result.technical_status != TechnicalStatus.SUPPORTED
    assert result.triggered_rules


def test_clm001_heavy_repair_needs_review(repository, tv_service):
    """Scenario E: engine block vs timing-chain scope."""
    claim = repository.get_claim("CLM-001")
    result = tv_service.analyze_claim(claim, top_k=5)
    assert result.technical_status == TechnicalStatus.NEEDS_REVIEW
    assert "R_HEAVY_REPAIR_LIGHT_DIAG" in result.triggered_rules
    assert result.human_review_required is True


def test_empty_rag_insufficient(settings, repository):
    """Scenario K: unindexed corpus."""
    service = TechnicalValidationService.for_tests(settings)
    claim = repository.get_claim("CLM-002")
    with pytest.raises(Exception) as exc:
        service.analyze_claim(claim, auto_ingest=False)
    from app.services.rag_service import RAGNotReadyError

    assert isinstance(exc.value, RAGNotReadyError)


def test_suspect_diagnosis_blocks_supported_without_direct(settings, repository, indexed_rag):
    """Scenario B: tentative diagnosis without direct supporting passages."""
    claim = repository.get_claim("CLM-001")
    nlp = NLPAnalysisService(settings).analyze_claim(claim)
    retrieval = indexed_rag.retrieve_for_claim(claim, top_k=3, run_nlp=False)
    result = validate_technical(claim, nlp, retrieval)
    assert "suspect" in claim.technician_diagnosis.lower()
    if not any(
        e.support_class == EvidenceSupportClass.DIRECT_SUPPORT
        for e in result.supporting_evidence
    ):
        assert result.technical_status != TechnicalStatus.SUPPORTED


def test_auto_ingest_when_index_empty(settings, repository):
    service = TechnicalValidationService.for_tests(settings)
    claim = repository.get_claim("CLM-002")
    result = service.analyze_claim(claim, top_k=3, auto_ingest=True)
    assert result.claim_id == "CLM-002"
    assert result.technical_status is not None
