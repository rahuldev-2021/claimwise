from app.core.config import Settings
from app.modules.nlp.fallback_decision import evaluate_fallback
from app.modules.nlp.pipeline import NLPPipeline
from tests.unit.test_nlp_braking_sample import _braking_claim


def test_simple_braking_claim_does_not_trigger_llm():
    settings = Settings(LLM_NLP_ENABLED=False, LLM_NLP_MIN_TRIGGER_COUNT=2)
    claim = _braking_claim()
    result = NLPPipeline().analyze(claim)
    decision = evaluate_fallback(claim, result, settings)
    assert decision.considered
    assert not decision.triggered


def test_missing_dtc_does_not_auto_trigger():
    settings = Settings(LLM_NLP_MIN_TRIGGER_COUNT=1)
    claim = _braking_claim()
    result = NLPPipeline().analyze(claim)
    decision = evaluate_fallback(claim, result, settings)
    assert "MISSING_DTC" not in decision.trigger_codes
