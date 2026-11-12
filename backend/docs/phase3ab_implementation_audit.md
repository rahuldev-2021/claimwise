# Phase 3A–3B implementation audit

**Date:** 2026-03-12  
**Status:** Awaiting human approval before Phase 5 / frontend work.

## Implemented

- Evidence scope metadata at ingest (`global` vs `claim` + `org_id` / `claim_id`).
- `evidence_source_type` (`GLOBAL_KNOWLEDGE` / `CLAIM_UPLOAD`) on chunk metadata and `RetrievedPassage`; surfaced on `EvidenceItem`.
- Verification preserved end-to-end; claim uploads capped in TV quality when not `VERIFIED`.
- Upload index eligibility (min text, scope, type, idempotent skip, per-doc reindex).
- Mongo `vector_index_status` / fingerprint tracking; Chroma purge helper for lifecycle.
- `MongoHistoricalRepairRepository` + Mongo upsert when `HISTORICAL_REPAIRS_INGEST_ENABLED` at ingest (still default off).
- Fail-closed `RetrievalScopeFilter` before rerank, context, citations.
- Investigation worker: global RAG retrieve + TV via `TechnicalValidationService`.
- Persisted `rag_retrieval` / `technical_validation` on claims.
- Independent stage statuses; `overall=READY` on intake completion.
- NLP failure skips RAG/TV.
- `HISTORICAL_REPAIRS_INGEST_ENABLED` default false; adapter + unit tests.
- Sample corpus: 15 docs, all `synthetic: true`, braking manuals/parts added.
- Chroma multi-field `where` via `$and`.
- Evaluation chunk-id validation warning.

## Partially implemented

- Real-embedding eval report (`phase3_rag_eval_report.md` template only — run locally with `[rag]`).
- Historical ingest into Chroma when flag enabled (adapter ready; DQR not approved).

## Deferred

- Full 90-document MVP corpus targets (manual count expansion beyond braking slice).
- PDF/DOCX OEM ingest.

## Test coverage

- Unit: `test_retrieval_access.py`, `test_historical_repair_adapter.py`, `test_rag_metadata_filter.py`.
- Integration: `test_investigation_rag.py`, existing RAG/TV tests (updated).
- Cross-org leakage: covered in `test_retrieval_access.py` (unit); no live multi-org integration yet.

## Regression

Run: `python -m pytest` from `backend/` before release.
