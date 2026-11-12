# Technical Validation Module (Phase 4)

Deterministic, evidence-based assessment of whether the customer complaint and technician diagnosis support the recommended repair. Consumes **NLP analysis** and **RAG retrieval** outputs; it does not re-run extraction or search.

## Outputs

`TechnicalValidationResult` (`app/schemas/technical_validation.py`) includes:

- `technical_status`: `SUPPORTED` | `QUESTIONABLE` | `INSUFFICIENT_EVIDENCE` | `NEEDS_REVIEW`
- Classified supporting / contradictory evidence with `support_class`, `retrieval_score`, and separate `quality_score`
- Rule trace (`triggered_rules`, `validation_reasons`)
- `human_review_required` (default true; false only when direct verified evidence supports the case with no blocking rules)

## Pipeline

`technical_validation_pipeline.validate_technical(claim, nlp, retrieval)` orchestrates validators in this package, then `validation_rules.apply_rules` and `confidence_calculator.calculate_confidence`.

## Service & API

- `TechnicalValidationService` — loads claim, runs NLP once, retrieves passages via RAG, runs the pipeline.
- `POST /api/v1/technical-validation/analyze` — body: `claim_id` **or** inline `claim`, optional `top_k`, `retrieval_mode`, `auto_ingest`.

Config (`app/core/config.py`): `TV_DEFAULT_TOP_K`, `TV_RETRIEVAL_MODE`, `TV_AUTO_INGEST`.

## Design constraints

- Retrieval rank ≠ evidence quality.
- `REPAIR_HISTORY` alone cannot yield `SUPPORTED`.
- No invented OEM thresholds — only from claim text or retrieved procedure content.
- Not Gemini; does not auto-approve or auto-reject claims.
