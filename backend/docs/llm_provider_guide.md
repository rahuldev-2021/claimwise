# LLM Provider Guide

## Switching providers

Set environment variables only — business logic does not change.

```env
LLM_ENABLED=true
LLM_PROVIDER=gemini
LLM_MODEL=gemini-2.0-flash
GEMINI_API_KEY=your-key
```

```env
LLM_PROVIDER=ollama
LLM_MODEL=llama3.2
OLLAMA_BASE_URL=http://localhost:11434
```

## Adding a new provider

1. Create `app/modules/llm/providers/<name>_provider.py` implementing `BaseLLMProvider`.
2. Register in `app/modules/llm/factory/provider_factory.py`.
3. Add config keys and optional `pyproject.toml` extra.
4. Document credentials and capability flags.

## Fallback

Set `LLM_FALLBACK_PROVIDER` to a second provider name. Fallback usage is recorded in `llm_execution.attempt_notes` and `status=FALLBACK`.

## Security

- Never commit API keys.
- Logs include claim IDs and metadata only, not full complaint text or keys.
- Retrieved documents are treated as untrusted in prompts.
