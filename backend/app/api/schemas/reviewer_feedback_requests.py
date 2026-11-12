from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.recommendation import OverallRecommendation
from app.schemas.reviewer_feedback import ReviewerDecision


class ReviewerFeedbackCreateRequest(BaseModel):
    """Reviewer submission. The server assigns reviewed_at."""

    model_config = ConfigDict(extra="forbid")

    claim_id: str = Field(min_length=1)
    system_recommendation: OverallRecommendation
    reviewer_decision: ReviewerDecision
    reviewer_comments: str = Field(default="", max_length=4000)
    overridden_recommendation: Optional[OverallRecommendation] = None
    override_reason: Optional[str] = Field(default=None, max_length=2000)
    additional_information_requested: list[str] = Field(default_factory=list, max_length=20)

    @model_validator(mode="after")
    def validate_consistency(self) -> "ReviewerFeedbackCreateRequest":
        if self.reviewer_decision == ReviewerDecision.PENDING:
            raise ValueError("reviewer_decision must not be PENDING when submitting feedback")
        if self.overridden_recommendation is not None:
            if self.overridden_recommendation == self.system_recommendation:
                raise ValueError("overridden_recommendation must differ from system_recommendation")
            if not (self.override_reason and self.override_reason.strip()):
                raise ValueError("override_reason is required when overriding the recommendation")
        if self.reviewer_decision == ReviewerDecision.REQUESTED_INFO and not any(
            s.strip() for s in self.additional_information_requested
        ):
            raise ValueError(
                "additional_information_requested is required when reviewer_decision is REQUESTED_INFO"
            )
        return self
