from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator


class Repair(BaseModel):
    """Technician's recommended repair details."""

    model_config = ConfigDict(extra="forbid")

    repair_category: str
    part_number: Optional[str] = None
    part_description: str
    recommended_action: str

    @field_validator("repair_category")
    @classmethod
    def normalize_category(cls, v: str) -> str:
        v = v.strip().upper()
        if not v:
            raise ValueError("Repair category must not be blank")
        return v

    @field_validator("part_description", "recommended_action")
    @classmethod
    def strip_and_reject_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Field must not be blank")
        return v

    @field_validator("part_number")
    @classmethod
    def strip_part_number(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if not v:
                return None
        return v
