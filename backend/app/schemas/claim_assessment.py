"""Full claim assessment response (Phase 5)."""

from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from app.modules.llm.schemas.llm_assessment import LLMContextualAssessment
from app.modules.nlp.schemas import NLPAnalysisResult
from app.modules.rag.schemas import RetrievalResult
from app.schemas.llm_execution import LLMExecutionRecord
from app.schemas.dealer_communication import DealerCommunicationBrief
from app.schemas.recommendation import ClaimRecommendation, FinancialAssessmentStatus
from app.schemas.technical_validation import TechnicalValidationResult


class AssessmentExecutionMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    assessment_id: str = Field(default_factory=lambda: str(uuid4()))
    duration_ms: float = 0.0
    rag_mode: str = ""
    financial_assessment_status: FinancialAssessmentStatus = FinancialAssessmentStatus.PENDING
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ClaimAssessmentResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    claim_id: str
    nlp_analysis: NLPAnalysisResult
    retrieval: RetrievalResult
    technical_validation: TechnicalValidationResult
    llm_contextual_assessment: Optional[LLMContextualAssessment] = None
    llm_execution: LLMExecutionRecord
    recommendation: ClaimRecommendation
    execution_metadata: AssessmentExecutionMetadata
    dealer_communication: Optional[DealerCommunicationBrief] = None
