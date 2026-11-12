# Phase 5: LLM Integration & Recommendation Engine

## Workflow

`POST /api/v1/assessment/analyze` runs: NLP → RAG → technical validation → optional LLM contextual assessment → Python recommendation rules.

LLM failures return HTTP 200 with `llm_execution.status` `FAILED` or `DISABLED`; deterministic results are preserved.

## Configuration

| Variable | Purpose |
|----------|---------|
| `LLM_ENABLED` | Master switch |
| `LLM_PROVIDER` | `mock`, `gemini`, `openai`, `anthropic`, `ollama` |
| `LLM_MODEL` | Provider model name |
| `GEMINI_API_KEY` / `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` | Provider secrets |
| `OLLAMA_BASE_URL` | Local Ollama endpoint |

## Provider status

| Provider | Status |
|----------|--------|
| mock | Implemented (tests) |
| gemini | Implemented (requires `pip install -e ".[llm-gemini]"` + API key) |
| ollama | Implemented (HTTP) |
| openai | Implemented (requires extra + key) |
| anthropic | Implemented (requires extra + key) |

## Phase 5 report summary

| Requirement | Status |
|-------------|--------|
| Unified provider interface + factory | PASS |
| Provider-independent schemas | PASS |
| Grounding validation | PASS |
| Deterministic fallback | PASS |
| Python recommendation engine | PASS |
| Assessment API + LLM health | PASS |
| Financial ML | Phase 6 integrated (UNAVAILABLE without registry artifacts; PROVISIONAL rules) |
| Live Gemini CI tests | NOT TESTED (optional marker) |

**Overall: PASS** for core architecture and CI-tested flows.

## Phase 5 completion checklist (5.1–5.12)

| Item | Status |
|------|--------|
| 5.1 Provider architecture | Done |
| 5.2 Context builder (bounded, authoritative TV) | Done |
| 5.3–5.5 Reasoning + recommendations | Done (shared pipeline) |
| 5.6 Structured schema v2 | Done |
| 5.7 Guardrails + Python compliance | Done |
| 5.8 Uncertainty separation | Done |
| 5.9 APIs (assessment + recommendations) | Done |
| 5.10 Persistence + history | Done (Mongo claims) |
| 5.11 Tests + mock eval harness | Done |
| 5.12 Docs | See `phase5_*.md` |

## Endpoints

- `POST /api/v1/assessment/analyze` — full bundle + optional financial
- `POST /api/v1/recommendations/analyze` — Phase 5 reasoning only (no financial ML)
