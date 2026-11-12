# Phase 5 security and guardrails

## Validation layers

1. Pydantic `LLMAssessmentResponse` (`extra=forbid`)
2. `EvidenceCatalog` — document/chunk ID and excerpt grounding
3. `verify_respects_technical_validation` — Python compliance (SR-2)
4. Repair operation keys must match Phase 4 `repair_action_assessments`

## Fail-safe

- LLM validation failure → `llm_execution.status=FAILED`, HTTP 200 with TV + deterministic recommendation
- No automatic claim decisions; `human_review_required=true`

## Auth

- `/assessment/analyze` and `/recommendations/analyze` require `claims:assess` and org-scoped claims.

## Logging

`record_assessment` / `record_recommendation_run` log fingerprints, prompt/schema versions, not claim text or API keys.
