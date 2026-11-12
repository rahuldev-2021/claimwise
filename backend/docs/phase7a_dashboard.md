# Phase 7A: Reviewer Dashboard

## Architecture

```
Browser (React/Vite/Tailwind)
    → FastAPI /api/v1/*
        → Sample claim repository
        → AssessmentService (Phases 2–5)
        → Reviewer feedback JSON file
```

## API mapping

| UI feature | Endpoint |
|------------|----------|
| Dashboard / claims list | `GET /api/v1/claims` |
| Claim detail header | `GET /api/v1/claims/{id}` |
| Full AI assessment | `POST /api/v1/assessment/analyze` |
| Reviewer feedback | `POST` / `GET /api/v1/reviewer-feedback/{claim_id}` |
| Health | `GET /health`, `GET /api/v1/rag/health`, `GET /api/v1/llm/health` |

## Phase 6 boundary

The Financial tab shows **submitted** parts/labour only and a fixed placeholder: *Financial validation – Pending Phase 6 integration*. No ML predictions are rendered.

## Dashboard KPI limitations

Claim counts come from live `GET /claims`. Recommendation-oriented KPIs use **sessionStorage** summaries for assessments run in the current browser session only.

## Authentication

Not implemented (Phase 7B / production hardening). CORS is configured via `CORS_ORIGINS`.

## Phase 7A feature matrix

| Feature | Status |
|---------|--------|
| Dashboard overview | Implemented |
| Claims search/filter | Implemented (make filter client-side) |
| Claim detail tabs | Implemented |
| Assessment run | Implemented (real API) |
| Reviewer feedback persistence | Implemented (JSON file) |
| Financial ML | Blocked (Phase 6) |
| Production auth | Not implemented |

**Overall Phase 7A: PASS** for integrated reviewer UI against Phases 1–5 APIs.
