"""Claim submission DTO from dealer UI."""

from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, field_validator

import re

_VIN_PATTERN = re.compile(r"^[A-HJ-NPR-Z0-9]{17}$")


class ClaimCreateRequest(BaseModel):
    repair_order: str = ""
    vin: Optional[str] = None
    year: str
    make: str
    model: str
    category: str
    customer_complaint: str
    technician_diagnosis: str
    recommended_repair: str
    parts_cost: str
    labour_hours: str
    currency: str = "USD"
    mileage: Optional[str] = None
    engine_type: Optional[str] = None

    @field_validator("customer_complaint", "technician_diagnosis", "recommended_repair")
    @classmethod
    def non_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Field must not be blank")
        return v

    @field_validator("vin")
    @classmethod
    def optional_vin(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        v = v.strip().upper()
        if not v:
            return None
        if not _VIN_PATTERN.match(v):
            raise ValueError("VIN must be 17 characters (excluding I, O, Q)")
        return v

    @field_validator("year")
    @classmethod
    def year_int(cls, v: str) -> str:
        v = v.strip()
        if not v.isdigit():
            raise ValueError("Year must be numeric")
        return v

    def parts_cost_decimal(self) -> Decimal:
        return Decimal(self.parts_cost.strip())

    def labour_hours_decimal(self) -> Decimal:
        return Decimal(self.labour_hours.strip())
