# Phase 2.2 — LLM NLP Fallback (implementation report)

## 1. Reused components

- `NLPPipeline` deterministic path and `ContextualExtractionProvider` protocol
- Phase 5 `ProviderFactory` / `BaseLLMProvider` (single LLM stack; `LLM_NLP_*` overrides model/provider)
- Existing `NLPAnalysisResult` contract (extended additively)
- Investigation + `NLPAnalysisService` wiring via `build_nlp_pipeline(settings)`

## 2. New components

- `entity_confidence.py` — confirmed vs heuristic tiers (Stage 0)
- `fallback_decision.py`, `llm_nlp_schemas.py`, `llm_context_builder.py`, `llm_nlp_prompt.py`
- `llm_nlp_validator.py`, `llm_nlp_reconcile.py`, `llm_contextual_provider.py`
- `pipeline_factory.py`, `nlp_llm_provider.py`

## 3. Pipeline version

`0.4.0` (`processing_metadata.llm_fallback` optional metadata)

## 4. Defaults

- `LLM_NLP_ENABLED=false`
- `LLM_NLP_FALLBACK_MODE=conditional`
- `LLM_NLP_MIN_TRIGGER_COUNT=2`
- Fallback uses confirmed entities only; never triggers on missing DTC/mileage/spaCy off alone

## 5. Failure behaviour

LLM timeout/invalid JSON/schema failure → deterministic output preserved; `llm_fallback.execution.error_code` set; claim processing not blocked.

## 6. Testing

- **153 unit tests passed** (mock LLM only for NLP fallback paths)
- Live provider not validated in CI (`@pytest.mark.llm_live` unchanged)

## 7. Known limitations / deferred

- No production accuracy claims without labeled eval + live provider runs
- Frontend does not surface `llm_fallback` metadata yet
- PII redaction beyond “no secrets in logs” not added
- Further spaCy chunk quality filters optional beyond confirmed tier

## 8. Partial / mock-only

LLM integration is **mock-tested** in unit tests; enabling `LLM_NLP_ENABLED=true` with real `LLM_NLP_PROVIDER` requires credentials and manual verification.
