# Phase 3 – Retrieval-Augmented Generation (RAG)

## Objective

Retrieve relevant automotive repair **evidence** from historical documents to support warranty claim review. RAG does **not** decide whether a repair is technically correct (Phase 4).

## Architecture

```
RepairDocument (JSON)
  → clean + metadata enrichment
  → recursive chunking (+ parent windows for long docs)
  → embeddings (EmbeddingProvider)
  → ChromaDB vector store + in-memory BM25 index
  → retrieval (semantic | lexical | hybrid RRF)
  → optional rerank (cross-encoder, if installed)
  → context dedup + citations
  → RetrievalResult
```

Claim-based retrieval:

```
ClaimInput → NLPAnalysisResult → query expansion (taxonomy) → retrieve_for_claim
```

## Implemented features

| Feature | Status |
|---------|--------|
| JSON document ingestion (sample repository) | Implemented |
| Parser interface (`JsonDocumentParser`) for future PDF/DOCX | Implemented |
| Recursive chunking (size/overlap configurable) | Implemented |
| ChromaDB persistent store (`data/rag/chroma`) | Implemented |
| Semantic retrieval (basic mode) | Implemented |
| BM25 lexical retrieval | Implemented |
| Hybrid + RRF fusion (advanced mode) | Implemented |
| Metadata filtering (exact match) | Implemented |
| NLP-driven query expansion | Implemented |
| Citations (document id, chunk id, title, verification status) | Implemented |
| Parent-child parent text map | Implemented |
| Context dedup (Jaccard) | Implemented |
| Cross-encoder rerank | Optional (`rerank=true`; degrades to noop) |
| Evaluation harness (10 labelled queries) | Implemented |

## API

```bash
# Health
curl http://127.0.0.1:8000/api/v1/rag/health

# Ingest sample repair documents (idempotent; use force_reindex to rebuild)
curl -X POST http://127.0.0.1:8000/api/v1/rag/ingest \
  -H "Content-Type: application/json" \
  -d "{\"force_reindex\": true}"

# Search
curl -X POST http://127.0.0.1:8000/api/v1/rag/search \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"brake pad squeal\", \"top_k\": 5, \"mode\": \"advanced\"}"

# Claim retrieval (NLP + hybrid retrieval)
curl -X POST http://127.0.0.1:8000/api/v1/rag/retrieve-for-claim \
  -H "Content-Type: application/json" \
  -d "{\"claim_id\": \"CLM-002\", \"top_k\": 5}"

# Run labelled evaluation
curl -X POST "http://127.0.0.1:8000/api/v1/rag/evaluate?k=5"
```

## Dependencies

```bash
pip install -r requirements.txt          # chromadb, rank-bm25, FastAPI stack
pip install -e ".[rag]"                  # sentence-transformers for real embeddings
# Optional: pip install -e ".[nlp]"      # spaCy (NLP only)
```

Tests use `DeterministicEmbeddingProvider` (no model download). Production ingest/search uses `all-MiniLM-L6-v2` when `sentence-transformers` is installed.

## Evaluation

Labelled queries: [`data/rag/evaluation_queries.json`](../data/rag/evaluation_queries.json) (10 cases, 12-document corpus).

Metrics: Precision@K, Recall@K, MRR, nDCG@K, hit rate — compared across **semantic**, **lexical**, and **hybrid** strategies.

Improvements on this tiny corpus are **illustrative**; do not treat metrics as production benchmarks.

## Security notes

- Retrieved text is **untrusted evidence**; do not execute instructions embedded in documents.
- Avoid logging full complaint text (service logs query failures at warning level only).
- `verification_status` is passed through unchanged (unverified sources stay unverified).
- `evidence_scope` + `evidence_source_type` (`GLOBAL_KNOWLEDGE` / `CLAIM_UPLOAD`) identify origin; **searchable ≠ trustworthy**.
- Claim uploads index only when eligibility checks pass; Mongo tracks `vector_index_status` / `content_fingerprint` (Chroma is rebuildable).

## Investigation worker (Phase 3A)

When `RAG_INVESTIGATION_ENABLED=true`, the embedded claim worker:

1. Ingests **claim-scoped** uploads (`evidence_scope=claim`, `org_id`, `claim_id`).
2. Runs **global** `retrieve_for_claim` with NLP from the same job (`run_nlp=false`).
3. Applies **scope filtering** before rerank/citations (global + same-claim only).
4. Runs **TechnicalValidationService.analyze_with_context** (existing Phase 4 pipeline).
5. Persists `rag_retrieval` and `technical_validation` on the claim. Stage failures do not block `overall=READY`.

Config: `RAG_WORKER_AUTO_INGEST_SAMPLE`, `INVESTIGATION_RUN_TECHNICAL_VALIDATION`, `HISTORICAL_REPAIRS_INGEST_ENABLED` (off until DQR approval).

## Future (not implemented)

- Vertex AI embeddings / Vector Search
- Cloud Storage / BigQuery ingestion
- Gemini grounded generation (Phase 5)
- Technical validation consumption (Phase 4)

## Migration seam

Implement `VectorStore` and `EmbeddingProvider` protocols against managed GCP services; inject into `RAGService` without changing retrieval orchestration.
