from typing import Optional

from pydantic import BaseModel, ConfigDict, model_validator

from app.schemas.claim import ClaimInput


class NLPAnalyzeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    claim_id: Optional[str] = None
    claim: Optional[ClaimInput] = None

    @model_validator(mode="after")
    def exactly_one_source(self) -> "NLPAnalyzeRequest":
        has_id = bool(self.claim_id and self.claim_id.strip())
        has_claim = self.claim is not None
        if has_id == has_claim:
            raise ValueError("Provide exactly one of claim_id or claim")
        return self
