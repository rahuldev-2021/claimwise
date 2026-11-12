# RAG Module (Phase 3)

Retrieves ranked repair evidence from historical documents using **semantic search**, **BM25 lexical search**, and **hybrid RRF fusion**, with full citation traceability.

## Quick start

```bash
pip install -r requirements.txt
pip install -e ".[rag]"   # optional: sentence-transformers for production embeddings

# After starting the API:
curl -X POST http://127.0.0.1:8000/api/v1/rag/ingest -d "{\"force_reindex\":true}"
```

## Key modules

| Module | Role |
|--------|------|
| `document_loader.py` / `document_parser.py` | Load `RepairDocument` records (JSON today) |
| `ingestion.py` | Chunk, embed, upsert Chroma, rebuild BM25 |
| `chunking.py` | Recursive, overlap, parent windows |
| `embedding_provider.py` | Protocol + MiniLM + deterministic test provider |
| `vector_store.py` | ChromaDB with explicit embeddings |
| `lexical_retriever.py` | BM25 (+ overlap fallback for tiny corpora) |
| `semantic_retriever.py` | Vector top-K |
| `hybrid_retriever.py` / `fusion.py` | RRF |
| `query_processor.py` | Claim queries + taxonomy expansion |
| `metadata_filter.py` | Chroma `where` clauses |
| `retrieval_pipeline.py` | Orchestration |
| `citation_manager.py` | `RetrievalResult` assembly |
| `evaluation.py` | Labelled metrics |
| `runtime.py` | Chroma client + parent text registry |

## Modes

- **basic** — semantic only (`RetrievalMode.BASIC`)
- **advanced** — hybrid semantic + BM25 + RRF (default)

## Configuration

See `app/core/config.py`: `RAG_PERSIST_DIR`, `RAG_EMBEDDING_MODEL`, chunk sizes, RRF `k`, relevance threshold.

## Limitations

- 12 synthetic JSON documents; one chunk per short doc in practice.
- Deterministic hash embeddings in tests do not reflect real semantic quality.
- Cross-encoder reranking is optional and not required for core flows.
- Metadata filters use exact equality (missing optional fields exclude a document).

See [`docs/phase3_rag.md`](../../docs/phase3_rag.md) for full detail.
