"""Deterministic dealer-facing communication hints (no LLM)."""

from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class BenchmarkPosition(str, Enum):
    BELOW_TYPICAL = "BELOW_TYPICAL"
    NEAR_TYPICAL = "NEAR_TYPICAL"
    ABOVE_TYPICAL = "ABOVE_TYPICAL"
    UNKNOWN = "UNKNOWN"


class FinancialDimensionBrief(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dimension: str  # "parts" | "labour"
    position: BenchmarkPosition = BenchmarkPosition.UNKNOWN
    submitted_value: Decimal
    typical_value: Optional[Decimal] = None
    discrepancy_pct: Optional[Decimal] = None
    dealer_note: str = ""


class ClaimResponseVerdict(str, Enum):
    """High-level dealer-facing outcome (advisory only)."""

    IN_LINE = "IN_LINE"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    NEEDS_DOCUMENTS = "NEEDS_DOCUMENTS"
    EXPLAIN_COSTS = "EXPLAIN_COSTS"
    NOT_FULLY_CHECKED = "NOT_FULLY_CHECKED"


class DealerClaimResponse(BaseModel):
    """Plain-language claim response for counter staff."""

    model_config = ConfigDict(extra="forbid")

    verdict: ClaimResponseVerdict
    verdict_label: str = ""
    summary: str = ""
    because: list[str] = Field(default_factory=list)
    what_to_say: str = ""


class DealerCommunicationBrief(BaseModel):
    """Advisory talking points for dealer staff — does not change workflow decisions."""

    model_config = ConfigDict(extra="forbid")

    advisory_only: bool = True
    benchmark_source: str = Field(
        default="model_typical",
        description="model_typical = ML point estimate for similar repair profile (not this VIN's history).",
    )
    overall_financial_position: BenchmarkPosition = BenchmarkPosition.UNKNOWN
    price_discussion_suggested: bool = False
    parts: Optional[FinancialDimensionBrief] = None
    labour: Optional[FinancialDimensionBrief] = None
    dealer_headline: str = ""
    dealer_talking_points: list[str] = Field(default_factory=list)
    customer_talking_points: list[str] = Field(default_factory=list)
    technical_dealer_note: str = ""
    response: Optional[DealerClaimResponse] = None
