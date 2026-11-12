"""Assess whether recommended repair scope matches diagnostic findings."""

from app.modules.technical_validation.schemas import RepairJustificationAssessment
from app.schemas.claim import ClaimInput
from app.schemas.technical_validation import FindingSeverity, FindingType, ValidationFinding


def assess_repair_scope(
    claim: ClaimInput,
    repair_justification: RepairJustificationAssessment,
) -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []
    if repair_justification.heavy_vs_light_mismatch:
        findings.append(
            ValidationFinding(
                finding_type=FindingType.REPAIR_SCOPE,
                description="Recommended repair scope may exceed documented diagnosis scope.",
                severity=FindingSeverity.MATERIAL,
                rule_id="R_HEAVY_REPAIR_LIGHT_DIAG",
                related_claim_fields=[
                    "technician_diagnosis",
                    "recommended_repair.recommended_action",
                ],
                explanation=repair_justification.summary,
                requires_human_review=True,
            )
        )
    return findings
