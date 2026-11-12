# Phase 5 LLM provider guide

See also `docs/llm_provider_guide.md` for install extras.

## Configuration

| Variable | Purpose |
|----------|---------|
| `LLM_ENABLED` | Master switch |
| `LLM_PROVIDER` | `mock`, `gemini`, `openai`, `anthropic`, `ollama` |
| `LLM_MODEL` | Model name |
| `LLM_PROMPT_VERSION` | Default `assessment_v2` |
| `LLM_CONTEXT_MAX_CHARS` / `LLM_CONTEXT_MAX_PASSAGES` | Context bounds |
| `PHASE5_REUSE_CACHED_STAGES` | Reuse persisted NLP/RAG/TV when TV fingerprint matches |
| `PHASE5_REUSE_LLM_IF_FINGERPRINT_MATCH` | Skip LLM call when latest record fingerprint matches |

## CI vs live

- CI: `LLM_PROVIDER=mock` (`tests/integration/test_assessment.py`, `scripts/run_phase5_eval.py` default).
- Live quality: `pytest -m llm_live` or `run_phase5_eval.py --live` with API keys set.

## Health

`GET /api/v1/llm/health` — provider probe (unauthenticated).
