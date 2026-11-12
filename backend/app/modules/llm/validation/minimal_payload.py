"""Minimal LLM assessment JSON — only keys the product consumes."""

MINIMAL_LLM_OUTPUT_KEYS = frozenset(
    {
        "summary",
        "suggested_alignment",
        "respects_technical_validation",
        "schema_version",
        "technical_interpretation",
    }
)


def coerce_minimal_llm_payload(data: dict) -> dict:
    """Drop verbose / legacy keys so extra=forbid models accept provider output."""
    return {key: data[key] for key in MINIMAL_LLM_OUTPUT_KEYS if key in data}
