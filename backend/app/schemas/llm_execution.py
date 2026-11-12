"""LLM execution metadata for assessments."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class LLMExecutionStatus(str, Enum):
    DISABLED = "DISABLED"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    FALLBACK = "FALLBACK"


class LLMExecutionRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: LLMExecutionStatus
    configured_provider: str = ""
    actual_provider: Optional[str] = None
    actual_model: Optional[str] = None
    prompt_version: str = ""
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    latency_ms: Optional[float] = None
    attempt_notes: list[str] = Field(default_factory=list)
    validation_errors: list[str] = Field(default_factory=list)
    raw_output_preview: Optional[str] = None
    json_repair_attempted: bool = False
    error_message: Optional[str] = None
