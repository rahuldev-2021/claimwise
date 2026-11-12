"""RAG passage fields survive technical validation evidence items."""

from app.modules.technical_validation.technical_validation_pipeline import validate_technical
from app.services.nlp_analysis_service import NLPAnalysisService
from tests.conftest import SAMPLE_DATA_DIR


def test_provenance_on_evidence_items(settings, indexed_rag, repository):
    claim = repository.get_claim("CLM-002")
    nlp = NLPAnalysisService(settings).analyze_claim(claim)
    retrieval = indexed_rag.retrieve_for_claim(claim, top_k=5, run_nlp=False)
    result = validate_technical(claim, nlp, retrieval, top_k=5)

    assert result.input_fingerprint
    assert result.pipeline_version
    if result.supporting_evidence:
        item = result.supporting_evidence[0]
        assert item.chunk_id
        assert item.document_id
        assert item.verification_status is not None

    for finding in result.validation_findings:
        for ref in finding.supporting_evidence_refs + finding.contradictory_evidence_refs:
            if ref:
                assert ref in {
                    *(e.chunk_id for e in result.supporting_evidence if e.chunk_id),
                    *(e.document_id for e in result.supporting_evidence),
                    *(e.chunk_id for e in result.contradictory_evidence if e.chunk_id),
                    *(e.document_id for e in result.contradictory_evidence),
                }
