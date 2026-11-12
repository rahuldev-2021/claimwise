from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class FinancialStatus(str, Enum):
    WITHIN_EXPECTED_RANGE = "WITHIN_EXPECTED_RANGE"
    OUTSIDE_EXPECTED_RANGE = "OUTSIDE_EXPECTED_RANGE"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    NEEDS_REVIEW = "NEEDS_REVIEW"


class PredictionInterval(BaseModel):
    """Low, typical, and high estimate for a predicted value."""

    model_config = ConfigDict(extra="forbid")

    low: Decimal
    typical: Decimal
    high: Decimal


class FinancialValidationResult(BaseModel):
    """Output of the financial validation module."""

    model_config = ConfigDict(extra="forbid")

    claim_id: str
    submitted_parts_cost: Decimal = Field(ge=0)
    predicted_parts_cost: Optional[Decimal] = None
    submitted_labour_hours: Decimal = Field(ge=0)
    predicted_labour_hours: Optional[Decimal] = None
    parts_discrepancy_pct: Optional[Decimal] = None
    labour_discrepancy_pct: Optional[Decimal] = None
    parts_prediction_interval: Optional[PredictionInterval] = None
    labour_prediction_interval: Optional[PredictionInterval] = None
    financial_status: FinancialStatus = FinancialStatus.INSUFFICIENT_DATA
    explanation: str = ""
    triggered_financial_rules: list[str] = Field(default_factory=list)
    parts_model_version: Optional[str] = None
    labour_model_version: Optional[str] = None
    parts_model_algorithm: Optional[str] = None
    labour_model_algorithm: Optional[str] = None
    model_lifecycle: Optional[str] = None
    experimental_prediction: bool = False
    synthetic_data_prediction: bool = False
    human_review_required: bool = True
    limitations: str = ""
