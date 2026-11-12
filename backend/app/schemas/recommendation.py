from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.modules.llm.schemas.llm_assessment import LLMAssessmentResponse, WorkflowRecommendation
from app.schemas.financial_validation import FinancialValidationResult
from app.schemas.technical_validation import RepairActionAssessment, TechnicalValidationResult


class FinancialAssessmentStatus(str, Enum):
    PENDING = "PENDING"
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"


class OverallRecommendation(str, Enum):
    PROCEED_TO_HUMAN_REVIEW = "PROCEED_TO_HUMAN_REVIEW"
    REQUEST_ADDITIONAL_EVIDENCE = "REQUEST_ADDITIONAL_EVIDENCE"
    REQUEST_MORE_EVIDENCE = "REQUEST_ADDITIONAL_EVIDENCE"
    REQUEST_FURTHER_DIAGNOSIS = "REQUEST_FURTHER_DIAGNOSIS"
    REVIEW_REPAIR_SCOPE = "REVIEW_REPAIR_SCOPE"
    REVIEW_CONTRADICTIONS = "REVIEW_CONTRADICTIONS"
    FLAG_FOR_REVIEW = "FLAG_FOR_REVIEW"
    INSUFFICIENT_INFORMATION = "INSUFFICIENT_INFORMATION"
    PROCEED_TO_REVIEW = PROCEED_TO_HUMAN_REVIEW


class ClaimRecommendation(BaseModel):
    """Final consolidated assessment for a warranty claim."""

    model_config = ConfigDict(extra="forbid")

    claim_id: str
    technical_validation: Optional[TechnicalValidationResult] = None
    financial_validation: Optional[FinancialValidationResult] = None
    overall_recommendation: OverallRecommendation
    recommendation_reasons: list[str] = Field(default_factory=list)
    evidence_document_ids: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    human_review_required: bool = True
    triggered_business_rules: list[str] = Field(default_factory=list)
    financial_assessment_status: FinancialAssessmentStatus = FinancialAssessmentStatus.PENDING
    llm_advisory_summary: Optional[str] = None
    workflow_recommendation: Optional[WorkflowRecommendation] = None
    llm_structured: Optional[LLMAssessmentResponse] = None
    repair_action_assessments: list[RepairActionAssessment] = Field(default_factory=list)
    generated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
