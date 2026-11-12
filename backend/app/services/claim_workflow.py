"""Claim workflow transitions driven by reviewer decisions."""

from typing import Optional

from app.schemas.claim import ClaimStatus
from app.schemas.reviewer_feedback import ReviewerDecision
from app.services.claim_service import ClaimService

_DECISION_TO_STATUS: dict[ReviewerDecision, ClaimStatus] = {
    ReviewerDecision.APPROVED: ClaimStatus.COMPLETED,
    ReviewerDecision.REJECTED: ClaimStatus.CLOSED,
    ReviewerDecision.REQUESTED_INFO: ClaimStatus.PENDING_INFORMATION,
    ReviewerDecision.ESCALATED: ClaimStatus.UNDER_REVIEW,
}


def claim_status_for_reviewer_decision(decision: ReviewerDecision) -> Optional[ClaimStatus]:
    return _DECISION_TO_STATUS.get(decision)


def apply_reviewer_decision_to_claim(
    claim_service: ClaimService,
    claim_id: str,
    decision: ReviewerDecision,
) -> Optional[ClaimStatus]:
    """Persist workflow status on the Mongo claim record when one exists."""
    status = claim_status_for_reviewer_decision(decision)
    if status is None:
        return None
    org_id = claim_service.get_persisted_org_id(claim_id)
    if not org_id:
        return None
    updated = claim_service.update_persisted(
        claim_id,
        org_id,
        {"claim.claim_status": status.value},
    )
    return status if updated else None
