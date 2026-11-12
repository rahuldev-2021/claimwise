"""Reviewer feedback (Phase 7 integration)."""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.claim import ClaimStatus
from app.schemas.recommendation import OverallRecommendation


class ReviewerDecision(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    REQUESTED_INFO = "REQUESTED_INFO"
    ESCALATED = "ESCALATED"


class ReviewerFeedback(BaseModel):
    model_config = ConfigDict(extra="forbid")

    claim_id: str
    system_recommendation: OverallRecommendation
    reviewer_decision: ReviewerDecision = ReviewerDecision.PENDING
    reviewer_comments: str = ""
    overridden_recommendation: Optional[OverallRecommendation] = None
    override_reason: Optional[str] = None
    additional_information_requested: list[str] = Field(default_factory=list)
    reviewed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_claim_status: Optional[ClaimStatus] = Field(
        default=None,
        description="Claim workflow status after this decision was saved (Mongo claims only).",
    )
