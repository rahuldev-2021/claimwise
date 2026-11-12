"""Configurable validation rules."""

from dataclasses import dataclass
from typing import Callable

from app.modules.technical_validation.claim_submission_evidence import (
    CLAIM_SUBMISSION_DOC_ID,
)
from app.modules.technical_validation.schemas import ValidationContext
from app.schemas.technical_validation import (
    ConsistencyLevel,
    EvidenceSupportClass,
    TechnicalStatus,
)

_STATUS_RANK = {
    TechnicalStatus.SUPPORTED: 0,
    TechnicalStatus.QUESTIONABLE: 1,
    TechnicalStatus.INSUFFICIENT_EVIDENCE: 2,
    TechnicalStatus.NEEDS_REVIEW: 3,
}


def _worse(a: TechnicalStatus, b: TechnicalStatus) -> TechnicalStatus:
    return a if _STATUS_RANK[a] >= _STATUS_RANK[b] else b


@dataclass(frozen=True)
class ValidationRule:
    rule_id: str
    message: str
    condition: Callable[[ValidationContext], bool]
    status: TechnicalStatus


_BLOCKING_RULES = frozenset(
    {
        "R_EMPTY_RETRIEVAL",
        "R_COMPLAINT_DIAGNOSIS_DISCONNECT",
        "R_SUSPECTED_NO_FINDINGS",
        "R_EXPLICIT_CONTRADICTION",
        "R_PROCEDURE_THRESHOLD_UNKNOWN",
        "R_HISTORY_ONLY",
        "R_HEAVY_REPAIR_LIGHT_DIAG",
    }
)


def _rules() -> list[ValidationRule]:
    return [
        ValidationRule(
            rule_id="R_EMPTY_RETRIEVAL",
            message="No retrieved evidence passages available.",
            condition=lambda c: c.empty_retrieval,
            status=TechnicalStatus.INSUFFICIENT_EVIDENCE,
        ),
        ValidationRule(
            rule_id="R_COMPLAINT_DIAGNOSIS_DISCONNECT",
            message="Complaint and diagnosis show inconsistent or insufficient alignment.",
            condition=lambda c: c.complaint_diagnosis is not None
            and c.complaint_diagnosis.consistency
            in (
                ConsistencyLevel.INCONSISTENT,
                ConsistencyLevel.INSUFFICIENT_INFORMATION,
            )
            and not any(
                x.support_class == EvidenceSupportClass.DIRECT_SUPPORT
                for x in c.classified
            ),
            status=TechnicalStatus.NEEDS_REVIEW,
        ),
        ValidationRule(
            rule_id="R_SUSPECTED_NO_FINDINGS",
            message="Diagnosis is tentative but measurements or fault codes are absent.",
            condition=lambda c: "suspect" in c.claim.technician_diagnosis.lower()
            and not any(
                x.support_class == EvidenceSupportClass.DIRECT_SUPPORT
                for x in c.classified
            ),
            status=TechnicalStatus.INSUFFICIENT_EVIDENCE,
        ),
        ValidationRule(
            rule_id="R_EXPLICIT_CONTRADICTION",
            message="Contradictory evidence conflicts with diagnosis or complaint.",
            condition=lambda c: any(
                x.support_class == EvidenceSupportClass.CONTRADICTORY
                for x in c.classified
            )
            or bool(c.contradictions),
            status=TechnicalStatus.NEEDS_REVIEW,
        ),
        ValidationRule(
            rule_id="R_PROCEDURE_THRESHOLD_UNKNOWN",
            message="Procedure/threshold referenced but claim measurements are missing.",
            condition=lambda c: c.procedure_threshold_missing,
            status=TechnicalStatus.INSUFFICIENT_EVIDENCE,
        ),
        ValidationRule(
            rule_id="R_HISTORY_ONLY",
            message="Only historical/contextual evidence; no direct inspection findings.",
            condition=lambda c: c.history_only
            and not any(
                x.support_class == EvidenceSupportClass.DIRECT_SUPPORT
                for x in c.classified
            ),
            status=TechnicalStatus.QUESTIONABLE,
        ),
        ValidationRule(
            rule_id="R_HEAVY_REPAIR_LIGHT_DIAG",
            message="Recommended repair scope exceeds diagnosis scope.",
            condition=lambda c: c.repair_justification is not None
            and c.repair_justification.heavy_vs_light_mismatch,
            status=TechnicalStatus.NEEDS_REVIEW,
        ),
        ValidationRule(
            rule_id="R_DIRECT_VERIFIED_SUPPORT",
            message="Direct verified evidence supports diagnosis and repair category.",
            condition=lambda c: any(
                x.support_class == EvidenceSupportClass.DIRECT_SUPPORT
                and x.verification_status == "VERIFIED"
                for x in c.classified
            )
            and not any(
                x.support_class == EvidenceSupportClass.CONTRADICTORY
                for x in c.classified
            )
            and c.complaint_diagnosis is not None
            and c.complaint_diagnosis.consistency
            in (ConsistencyLevel.CONSISTENT, ConsistencyLevel.PARTIALLY_CONSISTENT),
            status=TechnicalStatus.SUPPORTED,
        ),
        ValidationRule(
            rule_id="R_CLAIM_ATTESTED_INSPECTION",
            message="Dealer-submitted diagnosis includes measurements or codes; attested on the claim.",
            condition=lambda c: any(
                x.document_id == CLAIM_SUBMISSION_DOC_ID
                and x.support_class == EvidenceSupportClass.DIRECT_SUPPORT
                and x.verification_status == "VERIFIED"
                for x in c.classified
            )
            and not any(
                x.support_class == EvidenceSupportClass.CONTRADICTORY
                for x in c.classified
            )
            and (
                c.complaint_diagnosis is None
                or c.complaint_diagnosis.consistency != ConsistencyLevel.INCONSISTENT
            ),
            status=TechnicalStatus.SUPPORTED,
        ),
    ]


def apply_rules(ctx: ValidationContext) -> ValidationContext:
    status: TechnicalStatus | None = None
    triggered: list[str] = []
    reasons: list[str] = []

    for rule in _rules():
        if rule.condition(ctx):
            triggered.append(rule.rule_id)
            reasons.append(rule.message)
            status = rule.status if status is None else _worse(status, rule.status)

    if status is None:
        status = TechnicalStatus.QUESTIONABLE

    human_review = True
    _support_rules = {"R_DIRECT_VERIFIED_SUPPORT", "R_CLAIM_ATTESTED_INSPECTION"}
    if (
        bool(_support_rules & set(triggered))
        and status == TechnicalStatus.SUPPORTED
        and not (set(triggered) & _BLOCKING_RULES)
    ):
        human_review = False
    elif status == TechnicalStatus.SUPPORTED:
        status = TechnicalStatus.QUESTIONABLE
        human_review = True

    ctx.suggested_status = status
    ctx.triggered_rules = triggered
    ctx.validation_reasons = reasons
    ctx.human_review_required = human_review
    return ctx
