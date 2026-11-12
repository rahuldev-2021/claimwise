from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Vehicle(BaseModel):
    """Vehicle information associated with a warranty claim."""

    model_config = ConfigDict(extra="forbid")

    vehicle_id: str
    vin: Optional[str] = None
    make: str
    model: str
    model_year: int
    engine_type: Optional[str] = None
    vehicle_category: Optional[str] = None
    mileage: Optional[int] = Field(default=None, ge=0)

    @field_validator("vehicle_id", "make", "model")
    @classmethod
    def strip_and_reject_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Field must not be blank")
        return v

    @field_validator("vin")
    @classmethod
    def strip_vin(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if not v:
                return None
        return v

    @field_validator("engine_type")
    @classmethod
    def strip_engine_type(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if not v:
                return None
        return v

    @field_validator("model_year")
    @classmethod
    def validate_model_year(cls, v: int) -> int:
        current_year = datetime.now(timezone.utc).year
        if v < 1980 or v > current_year + 1:
            raise ValueError(f"Model year must be between 1980 and {current_year + 1}")
        return v
