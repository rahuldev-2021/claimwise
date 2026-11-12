# LLM Module (Phase 5)

Model-agnostic LLM integration for contextual claim assessment.

## Design

- **Unified contract:** `BaseLLMProvider` in `interfaces/base_provider.py`
- **Factory:** `ProviderFactory.create(settings)` — `mock`, `gemini`, `openai`, `anthropic`, `ollama`
- **Orchestration:** `LLMOrchestrator` — prompts, provider call, JSON parse, grounding validation
- **No business rules** in this package

## Configuration

Set `LLM_ENABLED=true` and `LLM_PROVIDER`. Install optional extras only for providers you use:

```bash
pip install -e ".[llm-gemini]"
pip install -e ".[llm-openai]"
pip install -e ".[llm-anthropic]"
```

## Testing

Use `LLM_PROVIDER=mock` for deterministic CI tests. Live Gemini tests use `@pytest.mark.llm_live`.
