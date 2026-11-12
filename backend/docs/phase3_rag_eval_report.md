# Phase 3 — retrieval evaluation report (template)

Run with **Sentence Transformer** embeddings on an ingested corpus — not `DeterministicEmbeddingProvider`.

```bash
pip install -e ".[rag]"
curl -X POST http://127.0.0.1:8000/api/v1/rag/ingest -d "{\"force_reindex\": true}"
curl -X POST "http://127.0.0.1:8000/api/v1/rag/evaluate?k=5"
```

## Metrics (per strategy)

| Strategy | P@K | R@K | MRR | nDCG@K | Hit@K |
|----------|-----|-----|-----|--------|-------|
| semantic | TBD | TBD | TBD | TBD | TBD |
| lexical | TBD | TBD | TBD | TBD | TBD |
| hybrid | TBD | TBD | TBD | TBD | TBD |

**Limitation:** Synthetic MVP corpus; metrics are illustrative only — not automotive production accuracy.

Do not claim hybrid superiority unless this table shows it on the same run.
