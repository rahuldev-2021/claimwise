# Phase 5 architecture

## Flow

`ReasoningPipeline` (`app/services/reasoning_pipeline.py`) is shared by:

- `POST /api/v1/assessment/analyze` (optional financial ML)
- `POST /api/v1/recommendations/analyze` (reasoning only, `run_financial=false`)

Stages: NLP → RAG → Phase 4 TV → LLM orchestrator → validation → `RecommendationEngine`.

## Authority

- `TechnicalValidationResult` is authoritative for technical and per-operation statuses.
- LLM output is advisory; Python `verify_respects_technical_validation` runs independently of the LLM boolean.
- LLM disagreement triggers `R_LLM_DISAGREEMENT` / `FLAG_FOR_REVIEW`, not `REVIEW_CONTRADICTIONS`.

## Persistence

Mongo `PersistedClaim`:

- `llm_recommendation_executions[]` (append-only, capped by `LLM_RECOMMENDATION_HISTORY_MAX`)
- `latest_llm_recommendation_id`

Reuse when `phase5_input_fingerprint` matches (`app/modules/llm/fingerprint.py`).

## Modules

| Module | Role |
|--------|------|
| `app/modules/llm/` | Providers, context, validation, compliance |
| `app/modules/recommendation/` | Rules, workflow mapping, audit logs |
| `app/services/reasoning_pipeline.py` | Shared orchestration |
