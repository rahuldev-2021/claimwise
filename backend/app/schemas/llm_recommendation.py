"""Persisted Phase 5 LLM recommendation execution record."""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from app.modules.llm.schemas.llm_assessment import LLMAssessmentResponse, WorkflowRecommendation


class LLMRecommendationProcessingStatus(str, Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    DISABLED = "DISABLED"
    REUSED = "REUSED"


class LLMRecommendationRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    recommendation_id: str = Field(default_factory=lambda: str(uuid4()))
    claim_id: str
    provider: str = ""
    model: str = ""
    prompt_version: str = ""
    schema_version: str = ""
    input_fingerprint: str = ""
    assessment: Optional[LLMAssessmentResponse] = None
    workflow_recommendation: Optional[WorkflowRecommendation] = None
    evidence_references: list[str] = Field(default_factory=list)
    human_review_required: bool = True
    processing_status: LLMRecommendationProcessingStatus = LLMRecommendationProcessingStatus.SUCCESS
    error_message: Optional[str] = None
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
