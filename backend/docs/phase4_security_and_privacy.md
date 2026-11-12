# Phase 4 security and privacy

## Authentication

- `POST /api/v1/technical-validation/analyze` requires `claims:assess` and valid JWT.
- `POST /api/v1/assessment/analyze` requires `claims:assess` and valid JWT.
- Claim access uses `ClaimService.get_claim_for_user` (org-scoped; super-admin exception documented in `composite_claim_repository.py`).

Client-supplied `org_id` is **never** used for authorization.

## Evidence isolation

- API retrieval passes `RetrievalAccessContext(org_id, claim_id)` from authenticated claim context.
- Phase 3 scope filter remains before rerank/context/citations in the RAG pipeline.

## Logging

- Do not log full complaint text or uploaded document bodies in TV paths.
- Use `claim_id` and `validation_id` in operational logs.

## Uploaded documents

- Treated as untrusted (`PENDING` verification, `CLAIM_UPLOAD` source type).
- Not promoted to global knowledge automatically.
