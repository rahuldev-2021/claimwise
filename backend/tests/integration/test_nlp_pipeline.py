from app.modules.nlp.pipeline import NLPPipeline
from app.repositories.sample_claim_repository import SampleClaimRepository
from tests.conftest import SAMPLE_DATA_DIR


def test_pipeline_clm001_structured_extraction():
    repo = SampleClaimRepository(SAMPLE_DATA_DIR)
    claim = repo.get_claim("CLM-001")
    result = NLPPipeline().analyze(claim)
    assert result.claim_id == "CLM-001"
    assert result.original_complaint == claim.customer_complaint
    assert result.structured_extraction.symptom == "abnormal_noise"
    assert result.structured_extraction.component in ("engine", "timing_chain")
    assert result.structured_extraction.part_number == "FR3Z-6006-A"
    assert result.processing_metadata.pipeline_version == "0.4.0"
    assert result.structured_extraction.failure_mode is None


def test_pipeline_clm002_braking():
    repo = SampleClaimRepository(SAMPLE_DATA_DIR)
    claim = repo.get_claim("CLM-002")
    result = NLPPipeline().analyze(claim)
    assert result.structured_extraction.component == "braking_system" or any(
        e.canonical == "braking_system"
        for ext in result.field_extractions
        for e in ext.entities
    )


def test_pipeline_clm008_timing_chain_repair():
    repo = SampleClaimRepository(SAMPLE_DATA_DIR)
    claim = repo.get_claim("CLM-008")
    result = NLPPipeline().analyze(claim)
    assert result.structured_extraction.repair_action == "replace"
    assert "timing" in (result.structured_extraction.part_number or "").lower() or any(
        "timing" in e.canonical for e in result.recommended_repair.entities
    )
