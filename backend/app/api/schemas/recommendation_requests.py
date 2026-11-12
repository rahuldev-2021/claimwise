from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class RecommendationAnalyzeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    claim_id: str = Field(min_length=1)
    force_refresh: bool = False
    llm_enabled: Optional[bool] = None
    llm_provider: Optional[str] = None
    top_k: Optional[int] = Field(default=None, ge=1, le=50)
    auto_ingest: Optional[bool] = None
