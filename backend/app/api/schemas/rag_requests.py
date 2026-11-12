from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.modules.rag.schemas import RetrievalMode
from app.schemas.claim import ClaimInput


class RAGIngestRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    force_reindex: bool = False
    document_ids: Optional[list[str]] = None


class RAGSearchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=50)
    mode: RetrievalMode = RetrievalMode.ADVANCED
    metadata_filters: dict[str, object] = Field(default_factory=dict)
    expand: bool = True
    rerank: bool = False


class RAGRetrieveForClaimRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    claim_id: Optional[str] = None
    claim: Optional[ClaimInput] = None
    top_k: int = Field(default=5, ge=1, le=50)
    mode: Optional[RetrievalMode] = None
    filter_fields: list[str] = Field(default_factory=lambda: ["repair_category"])
    expand: bool = True
    rerank: bool = False

    @model_validator(mode="after")
    def exactly_one_source(self) -> "RAGRetrieveForClaimRequest":
        has_id = bool(self.claim_id and self.claim_id.strip())
        has_claim = self.claim is not None
        if has_id == has_claim:
            raise ValueError("Provide exactly one of claim_id or claim")
        return self
