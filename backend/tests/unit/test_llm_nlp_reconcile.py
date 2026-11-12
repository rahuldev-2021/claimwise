import json

from app.core.config import Settings
from app.modules.nlp.llm_contextual_provider import LLMContextualExtractionProvider
from app.modules.nlp.llm_nlp_schemas import LLMNlpExtractionResponse
from app.modules.nlp.llm_nlp_reconcile import reconcile_llm_extraction
from app.modules.nlp.pipeline import NLPPipeline
from app.modules.nlp.schemas import EntityCategory, TextSourceField
from tests.unit.test_nlp_braking_sample import _braking_claim


def test_llm_supplements_new_entity_without_overwriting_deterministic():
    claim = _braking_claim()
    det = NLPPipeline().analyze(claim)
    llm = LLMNlpExtractionResponse.model_validate(
        {
            "entities": [
                {
                    "temp_id": "LX1",
                    "text": "road test",
                    "canonical": "road_test",
                    "category": "diagnostic_finding",
                    "source_field": "technician_diagnosis",
                    "source_excerpt": "road test",
                    "negated": False,
                }
            ],
            "relationships": [],
            "observations": [],
        }
    )
    merged, conflicts = reconcile_llm_extraction(det, llm)
    assert not conflicts
    diag_ents = next(
        e for e in merged.field_extractions if e.source_field == TextSourceField.TECHNICIAN_DIAGNOSIS
    ).entities
    assert any(e.extraction_method.value == "llm" and e.llm_reconciled for e in diag_ents)


def test_llm_disabled_never_invokes_provider(monkeypatch):
    settings = Settings(LLM_NLP_ENABLED=False, LLM_NLP_FALLBACK_MODE="always")
    provider = LLMContextualExtractionProvider(settings)
    called = {"n": 0}

    def _boom(*_a, **_k):
        called["n"] += 1
        raise AssertionError("provider should not be called")

    monkeypatch.setattr(
        "app.modules.nlp.llm_contextual_provider.create_nlp_llm_provider", _boom
    )
    det = NLPPipeline().analyze(_braking_claim())
    out = provider.enrich(_braking_claim(), det)
    assert called["n"] == 0
    assert out.processing_metadata.llm_fallback is not None
    assert not out.processing_metadata.llm_fallback.decision.invoked
