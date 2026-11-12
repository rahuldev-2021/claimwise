import json

from app.modules.llm.context.contextual_input_builder import build_context_payload
from app.modules.nlp.pipeline import NLPPipeline
from app.modules.rag.schemas import RetrievalResult, RetrievalStrategy
from app.modules.technical_validation.technical_validation_pipeline import validate_technical
from tests.unit.test_nlp_braking_sample import _braking_claim


def test_build_context_includes_authoritative_tv_summary(indexed_rag, settings):
    claim = _braking_claim()
    nlp = NLPPipeline().analyze(claim)
    retrieval = indexed_rag.retrieve_for_claim(claim, top_k=3)
    technical = validate_technical(claim, nlp, retrieval, top_k=3)
    raw = build_context_payload(claim, nlp, retrieval, technical, settings=settings)
    payload = json.loads(raw)
    assert "technical_validation_authoritative" in payload
    assert payload["technical_validation_authoritative"]["technical_status"]
    assert "claim_evidence" in payload
    assert len(payload["retrieved_passages"]) <= settings.LLM_CONTEXT_MAX_PASSAGES
