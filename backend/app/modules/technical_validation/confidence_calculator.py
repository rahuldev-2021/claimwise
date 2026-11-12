"""Explainable confidence from rule outcomes and evidence (not calibrated probability)."""

from app.modules.technical_validation.schemas import ValidationContext
from app.schemas.technical_validation import (
    ConfidenceLevel,
    EvidenceSupportClass,
    TechnicalStatus,
)


def calculate_confidence(ctx: ValidationContext) -> tuple[ConfidenceLevel, float | None]:
    """Return qualitative level and optional weighted score in [0,1]."""
    score = 0.5
    if ctx.suggested_status == TechnicalStatus.SUPPORTED:
        score = 0.82
    elif ctx.suggested_status == TechnicalStatus.QUESTIONABLE:
        score = 0.45
    elif ctx.suggested_status == TechnicalStatus.INSUFFICIENT_EVIDENCE:
        score = 0.35
    elif ctx.suggested_status == TechnicalStatus.NEEDS_REVIEW:
        score = 0.4

    direct = sum(
        1 for c in ctx.classified if c.support_class == EvidenceSupportClass.DIRECT_SUPPORT
    )
    contradict = sum(
        1 for c in ctx.classified if c.support_class == EvidenceSupportClass.CONTRADICTORY
    )

    if direct:
        score = min(1.0, score + 0.08 * min(direct, 3))
    if contradict:
        score = max(0.1, score - 0.15 * min(contradict, 2))
    if ctx.missing:
        score = max(0.1, score - 0.05 * min(len(ctx.missing), 4))
    if ctx.empty_retrieval:
        score = 0.2

    score = round(score, 3)

    if contradict and ctx.suggested_status == TechnicalStatus.NEEDS_REVIEW:
        level = ConfidenceLevel.LOW
    elif ctx.suggested_status == TechnicalStatus.SUPPORTED and direct >= 1 and not contradict:
        level = ConfidenceLevel.HIGH if direct >= 1 else ConfidenceLevel.MEDIUM
    elif ctx.suggested_status == TechnicalStatus.INSUFFICIENT_EVIDENCE:
        level = ConfidenceLevel.INDETERMINATE
    elif score >= 0.75:
        level = ConfidenceLevel.HIGH
    elif score >= 0.5:
        level = ConfidenceLevel.MEDIUM
    else:
        level = ConfidenceLevel.LOW

    return level, score
