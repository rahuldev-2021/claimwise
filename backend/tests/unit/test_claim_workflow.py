from app.schemas.claim import ClaimStatus
from app.schemas.reviewer_feedback import ReviewerDecision
from app.services.claim_workflow import claim_status_for_reviewer_decision


def test_reviewer_decision_maps_to_claim_status():
    assert claim_status_for_reviewer_decision(ReviewerDecision.APPROVED) == ClaimStatus.COMPLETED
    assert claim_status_for_reviewer_decision(ReviewerDecision.REJECTED) == ClaimStatus.CLOSED
    assert claim_status_for_reviewer_decision(ReviewerDecision.REQUESTED_INFO) == ClaimStatus.PENDING_INFORMATION
    assert claim_status_for_reviewer_decision(ReviewerDecision.ESCALATED) == ClaimStatus.UNDER_REVIEW
    assert claim_status_for_reviewer_decision(ReviewerDecision.PENDING) is None
