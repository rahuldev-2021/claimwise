from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.api.schemas.reviewer_feedback_requests import ReviewerFeedbackCreateRequest
from app.auth.dependencies import CurrentUser, require_permissions
from app.core.config import get_settings
from app.core.exceptions import ClaimNotFoundError
from app.repositories.reviewer_feedback_repository import ReviewerFeedbackRepository
from app.schemas.reviewer_feedback import ReviewerFeedback
from app.services.claim_service import ClaimService
from app.services.claim_workflow import apply_reviewer_decision_to_claim

router = APIRouter(tags=["reviewer-feedback"])
_settings = get_settings()
_claim_service = ClaimService(_settings)
_feedback_repo = ReviewerFeedbackRepository(_settings.FEEDBACK_DATA_PATH)


@router.post("/reviewer-feedback", response_model=ReviewerFeedback, status_code=201)
def submit_reviewer_feedback(
    request: ReviewerFeedbackCreateRequest,
    user: Annotated[CurrentUser, Depends(require_permissions("claims:review"))],
) -> ReviewerFeedback:
    del user
    claim_id = request.claim_id.strip()
    try:
        _claim_service.get_claim(claim_id)
    except ClaimNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    now = datetime.now(timezone.utc)
    updated_status = apply_reviewer_decision_to_claim(
        _claim_service,
        claim_id,
        request.reviewer_decision,
    )
    feedback = ReviewerFeedback(
        claim_id=claim_id,
        system_recommendation=request.system_recommendation,
        reviewer_decision=request.reviewer_decision,
        reviewer_comments=request.reviewer_comments.strip(),
        overridden_recommendation=request.overridden_recommendation,
        override_reason=(request.override_reason or "").strip() or None,
        additional_information_requested=[
            s.strip() for s in request.additional_information_requested if s.strip()
        ],
        reviewed_at=now,
        created_at=now,
        updated_claim_status=updated_status,
    )
    return _feedback_repo.add(feedback)


@router.get("/reviewer-feedback/{claim_id}", response_model=list[ReviewerFeedback])
def list_reviewer_feedback(
    claim_id: str,
    user: Annotated[CurrentUser, Depends(require_permissions("claims:read"))],
) -> list[ReviewerFeedback]:
    del user
    try:
        _claim_service.get_claim(claim_id)
    except ClaimNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _feedback_repo.list_for_claim(claim_id)
