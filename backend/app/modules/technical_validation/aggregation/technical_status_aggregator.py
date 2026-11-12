"""Aggregate validation findings and rule outcomes into final technical status."""

from app.modules.technical_validation.schemas import ValidationContext
from app.modules.technical_validation.validation_rules import apply_rules
from app.schemas.technical_validation import FindingType, ValidationFinding


def aggregate_technical_status(ctx: ValidationContext) -> ValidationContext:
    """Apply detection rules and set status fields on context (single aggregation path)."""
    ctx = apply_rules(ctx)
    for rule_id, message in zip(ctx.triggered_rules, ctx.validation_reasons, strict=False):
        ctx.validation_findings.append(
            ValidationFinding(
                finding_type=FindingType.RULE,
                description=message,
                rule_id=rule_id,
                explanation=message,
                requires_human_review=True,
            )
        )
    return ctx
