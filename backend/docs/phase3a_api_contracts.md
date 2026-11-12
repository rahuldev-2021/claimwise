# Phase 3A — API contract deltas (verified pre-flight)

| Component | Change |
|-----------|--------|
| `RepairDocument` | `evidence_scope`, `org_id`, `synthetic`, `component`, `source_document_ids`, `historical_repair_id`, `REPAIR_MANUAL` |
| `RetrievalAccessContext` | `org_id`, `claim_id` — server-side only |
| `RAGService.retrieve_for_claim` | `nlp_result`, `access` optional params |
| `RetrievalPipeline._run` | `access` + scope filter before rerank/context/citations |
| `TechnicalValidationService` | `analyze_with_context(claim, nlp, retrieval)` |
| `PersistedClaim` | `rag_retrieval`, `technical_validation` |
