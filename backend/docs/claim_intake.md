# Claim intake and investigation pipeline

## Overview

Dealer technicians submit claims via `POST /api/v1/claims` (multipart). The API:

1. Validates diagnosis, amounts, and optional uploads (PDF/DOCX with magic-byte checks).
2. Persists a claim in MongoDB (`claims`) with `org_id` from the JWT (never from the client).
3. Enqueues `CLAIM_INVESTIGATION` on the `jobs` collection (transaction when supported, outbox fallback).
4. Returns `201` with the `ClaimInput` payload.

By default the API **embeds** the investigation worker (no second terminal). Start only:

```bash
cd backend
python main.py
```

To run a dedicated worker instead, set `EMBED_CLAIM_WORKER=false` and use `python -m app.worker`.

## Worker stages

| Stage | Updates |
|-------|---------|
| Documents | Extract text, classify, store `repair_documents`, private blobs under `data/uploads/{claim_id}/` |
| NLP | `nlp_analysis` on the claim document (does not overwrite `technician_diagnosis`) |
| RAG | Ingest new repair documents into Chroma |

`GET /api/v1/claims/{id}/processing-status` returns nested `processing_status` for UI polling.

## Configuration

| Variable | Default |
|----------|---------|
| `CLAIMS_UPLOAD_DIR` | `data/uploads` |
| `CLAIMS_MAX_FILE_BYTES` | 10MB |
| `CLAIMS_MAX_TOTAL_UPLOAD_BYTES` | 50MB |
| `JOB_LEASE_SECONDS` | 300 |
| `WORKER_POLL_INTERVAL_MS` | 2000 |

## Permissions

- `claims:submit` — create claim
- `claims:read` — list/get/status/download (org-scoped)

## Reliability

Jobs support lease, exponential backoff, stuck recovery, and idempotency keys. Unprocessed `outbox` events on claims are repaired by the worker on each poll.
