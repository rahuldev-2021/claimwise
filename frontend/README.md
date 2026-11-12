# CLAIMWISE Frontend (Phase 7A)

React + TypeScript reviewer workbench for Phases 1–5 backend APIs.

## Prerequisites

- Node.js 18+
- Backend running at `http://127.0.0.1:8000` (see `backend/README.md`)

## Setup

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Open http://localhost:5173. API calls use `VITE_API_BASE_URL` (default `http://127.0.0.1:8000`). The dev server proxy uses the same value for relative `/api` fallbacks.

## Environment

| Variable | Purpose |
|----------|---------|
| `VITE_API_BASE_URL` | Backend origin, e.g. `http://127.0.0.1:8000` (must match backend `HOST`/`PORT`) |
| `VITE_DEV_PORT` | Optional Vite port (default `5173`) |
| `VITE_DEV_USER` | Display-only reviewer name in header (not authentication) |

## Scripts

| Command | Purpose |
|---------|---------|
| `npm run dev` | Development server |
| `npm run build` | Production build |
| `npm test` | Vitest unit tests |
| `npm run generate-api-types` | Regenerate types from backend OpenAPI (backend must be running) |

## Security note

Authentication/authorization is **not** implemented in Phase 7A. Do not expose this UI to untrusted networks without a gateway.
