"""Build human-readable recommendation explanations."""

from app.modules.recommendation.schemas.context import RecommendationContext
from app.schemas.recommendation import OverallRecommendation


def build_explanation(
    recommendation: OverallRecommendation,
    ctx: RecommendationContext,
) -> list[str]:
    lines = list(ctx.reasons)
    lines.append(f"Overall recommendation: {recommendation.value}.")
    if not ctx.financial_enabled:
        lines.append("Financial validation was disabled for this assessment.")
    elif ctx.financial is None:
        lines.append("Financial validation did not run.")
    elif ctx.financial.predicted_parts_cost is None:
        lines.append(
            f"Financial status: {ctx.financial.financial_status.value} (predictions unavailable)."
        )
    else:
        lines.append(
            f"Financial status: {ctx.financial.financial_status.value}. {ctx.financial.explanation}"
        )
    if ctx.llm_assessment and ctx.llm_available:
        lines.append(f"LLM advisory summary: {ctx.llm_assessment.assessment.summary}")
    elif ctx.llm_execution.status.value == "DISABLED":
        lines.append("LLM contextual reasoning disabled by configuration.")
    else:
        lines.append("LLM contextual reasoning was unavailable or failed validation.")
    lines.append("Human reviewer makes the final claim decision.")
    return lines
