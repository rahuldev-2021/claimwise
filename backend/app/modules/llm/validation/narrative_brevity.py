"""Clamp minimal LLM fields to prompt limits."""

from app.modules.llm.schemas.llm_assessment import LLMAssessmentResponse

SUMMARY_MAX = 280
TV_EXPLANATION_MAX = 150


def _clip(text: str, limit: int) -> str:
    text = (text or "").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def clamp_assessment_narrative(parsed: LLMAssessmentResponse) -> LLMAssessmentResponse:
    ti = parsed.technical_interpretation
    technical = (
        ti.model_copy(update={"explanation": _clip(ti.explanation, TV_EXPLANATION_MAX)})
        if ti
        else ti
    )
    repairs = [
        r.model_copy(update={"advisory_explanation": _clip(r.advisory_explanation, 150)})
        for r in parsed.repair_interpretations
    ]
    return parsed.model_copy(
        update={
            "summary": _clip(parsed.summary, SUMMARY_MAX),
            "technical_interpretation": technical,
            "repair_interpretations": repairs,
        }
    )
