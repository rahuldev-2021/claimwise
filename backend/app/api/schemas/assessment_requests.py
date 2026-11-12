from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.modules.rag.schemas import RetrievalMode
from app.schemas.claim import ClaimInput


class AssessmentAnalyzeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    claim_id: Optional[str] = None
    claim: Optional[ClaimInput] = None
    top_k: int = Field(default=5, ge=1, le=50)
    retrieval_mode: Optional[RetrievalMode] = None
    auto_ingest: bool = False
    llm_enabled: Optional[bool] = None
    financial_enabled: Optional[bool] = None
    force_refresh: bool = False

    @model_validator(mode="after")
    def exactly_one_source(self) -> "AssessmentAnalyzeRequest":
        has_id = bool(self.claim_id and self.claim_id.strip())
        has_claim = self.claim is not None
        if has_id == has_claim:
            raise ValueError("Provide exactly one of claim_id or claim")
        return self
