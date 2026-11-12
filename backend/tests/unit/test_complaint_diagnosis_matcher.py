from app.modules.nlp.complaint_diagnosis_matcher import compare_complaint_and_diagnosis
from app.modules.nlp.information_extractor import extract_from_claim
from app.repositories.sample_claim_repository import SampleClaimRepository
from tests.conftest import SAMPLE_DATA_DIR


def test_clm001_flags_repair_scope_mismatch_without_validity_verdict():
    repo = SampleClaimRepository(SAMPLE_DATA_DIR)
    claim = repo.get_claim("CLM-001")
    extractions, _ = extract_from_claim(claim)
    comparison = compare_complaint_and_diagnosis(claim, extractions)
    assert comparison.notes_for_reviewer
    assert not hasattr(comparison, "technical_status")
    assert any("extensive" in note.lower() or "verification" in note.lower() for note in comparison.notes_for_reviewer)
