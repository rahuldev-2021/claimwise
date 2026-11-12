import json

from app.modules.nlp.llm_context_builder import build_nlp_llm_context
from app.modules.nlp.pipeline import NLPPipeline
from tests.unit.test_nlp_braking_sample import _braking_claim


def test_context_uses_compact_coverage_not_full_entity_dump():
    claim = _braking_claim()
    det = NLPPipeline().analyze(claim)
    raw = build_nlp_llm_context(claim, det)
    payload = json.loads(raw)
    assert "deterministic_entities" not in payload
    assert "deterministic_coverage" in payload
    assert payload["deterministic_coverage"]["confirmed_entity_count"] >= 1
    assert "original_complaint" not in payload
    assert "source_fields" in payload
