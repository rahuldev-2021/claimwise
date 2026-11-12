# Phase 5 prompt design

- **Version:** `assessment_v2` (`app/modules/llm/prompt_management/templates/assessment_v2_system.txt`)
- **Manager:** `PromptManager` reads `LLM_PROMPT_VERSION` override.

## Context JSON (`build_context_payload`)

Includes:

- Claim summary
- NLP summary (not full entity dump)
- `technical_validation_authoritative` — statuses, repair actions, findings
- `claim_evidence` with provenance fields
- Bounded `retrieved_passages` (deduped vs TV excerpts)
- Anti-injection `instructions`

## Output schema

`LLMAssessmentResponse` schema v2: repair interpretations echo Phase 4 operation keys and statuses; `technical_interpretation.advisory_status` must match TV.
