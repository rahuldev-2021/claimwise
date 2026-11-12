from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.claim import ClaimInput


class FinancialPredictRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    claim_id: Optional[str] = None
    claim: Optional[ClaimInput] = None

    def resolved_claim_id(self) -> Optional[str]:
        if self.claim_id and self.claim_id.strip():
            return self.claim_id.strip()
        if self.claim:
            return self.claim.claim_id
        return None


class FinancialAnalyzeRequest(FinancialPredictRequest):
    """Same inputs as predict; returns full FinancialValidationResult."""
