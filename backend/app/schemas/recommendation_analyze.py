"""Response for POST /recommendations/analyze (Phase 5 reasoning without financial ML)."""

from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from app.modules.llm.schemas.llm_assessment import LLMContextualAssessment
from app.schemas.llm_execution import LLMExecutionRecord
from app.schemas.llm_recommendation import LLMRecommendationRecord
from app.schemas.recommendation import ClaimRecommendation
from app.schemas.technical_validation import TechnicalValidationResult


class RecommendationExecutionMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    recommendation_run_id: str = Field(default_factory=lambda: str(uuid4()))
    duration_ms: float = 0.0
    phase5_input_fingerprint: str = ""
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class RecommendationAnalyzeResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    claim_id: str
    technical_validation: TechnicalValidationResult
    llm_contextual_assessment: Optional[LLMContextualAssessment] = None
    llm_execution: LLMExecutionRecord
    recommendation: ClaimRecommendation
    llm_recommendation_record: Optional[LLMRecommendationRecord] = None
    execution_metadata: RecommendationExecutionMetadata
