"""API-oriented prediction schemas."""

from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class FinancialPredictionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    claim_id: str
    predicted_parts_cost: Optional[Decimal] = None
    predicted_labour_hours: Optional[Decimal] = None
    parts_model_version: Optional[str] = None
    labour_model_version: Optional[str] = None
    models_available: bool = False
    missing_critical_features: list[str] = Field(default_factory=list)
    parts_model_algorithm: Optional[str] = None
    labour_model_algorithm: Optional[str] = None
    model_lifecycle: Optional[str] = None
    experimental_prediction: bool = False
    synthetic_data_prediction: bool = False
    human_review_required: bool = True
    limitations: str = ""
    inference_mode: str = "production"
