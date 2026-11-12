"""MongoDB claim record (ClaimInput + tenancy and pipeline metadata)."""

from datetime import datetime, timezone
from typing import Any, Optional

from pydantic import BaseModel, Field

from app.modules.nlp.schemas import NLPAnalysisResult
from app.modules.rag.schemas import RetrievalResult
from app.schemas.llm_recommendation import LLMRecommendationRecord
from app.schemas.technical_validation import TechnicalValidationResult
from app.schemas.claim import ClaimInput, ClaimStatus
from app.schemas.claim_assessment import ClaimAssessmentResponse
from app.schemas.processing_status import ProcessingStatus


class ClaimMetadata(BaseModel):
    repair_order: str = ""
    submitted_by_user_id: str = ""
    submitted_by_email: str = ""


class ClaimOutboxEvent(BaseModel):
    event: str
    job_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    processed: bool = False


class PersistedClaim(BaseModel):
    org_id: str
    source: str = "mongo"
    claim: ClaimInput
    metadata: ClaimMetadata = Field(default_factory=ClaimMetadata)
    processing_status: ProcessingStatus = Field(default_factory=ProcessingStatus)
    nlp_analysis: Optional[NLPAnalysisResult] = None
    rag_retrieval: Optional[RetrievalResult] = None
    technical_validation: Optional[TechnicalValidationResult] = None
    latest_assessment: Optional[ClaimAssessmentResponse] = None
    latest_assessment_at: Optional[datetime] = None
    latest_assessment_fingerprint: Optional[str] = None
    latest_llm_recommendation_id: Optional[str] = None
    llm_recommendation_executions: list[LLMRecommendationRecord] = Field(default_factory=list)
    extracted_findings: Optional[dict[str, Any]] = None
    pending_uploads: list[dict[str, Any]] = Field(default_factory=list)
    file_index: dict[str, str] = Field(default_factory=dict)
    outbox: list[ClaimOutboxEvent] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def claim_id(self) -> str:
        return self.claim.claim_id
