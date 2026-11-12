"""Second-pass JSON repair with a minimal prompt (syntax + schema hints only)."""

import json

from app.schemas.technical_validation import TechnicalValidationResult

REPAIR_SYSTEM = (
    "You fix invalid JSON. Return exactly one object with ONLY: summary, suggested_alignment, "
    "respects_technical_validation, schema_version, technical_interpretation. "
    "No repair_interpretations. summary max 280 chars; technical_interpretation.explanation max 150."
)


def build_json_repair_prompt(
    broken_text: str,
    validation_errors: list[str],
    technical: TechnicalValidationResult,
    *,
    max_broken_chars: int = 14_000,
) -> str:
    payload = {
        "task": "Fix the broken JSON so it parses and satisfies the checklist.",
        "validation_errors": validation_errors[:10],
        "required_checklist": {
            "respects_technical_validation": True,
            "schema_version": "assessment_schema_v2",
            "technical_interpretation": {
                "advisory_status": technical.technical_status.value,
                "explanation": "string max 150 chars",
            },
        },
        "broken_model_output": (broken_text or "")[:max_broken_chars],
    }
    return json.dumps(payload, ensure_ascii=False)
