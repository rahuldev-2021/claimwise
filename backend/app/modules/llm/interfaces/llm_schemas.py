"""Provider-independent LLM request/response schemas."""

from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T", bound=BaseModel)


class LLMRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    system_instruction: str
    user_prompt: str
    temperature: float = Field(default=0.2, ge=0.0, le=2.0)
    max_output_tokens: int = Field(default=0, ge=0, le=65536)
    timeout_seconds: float = Field(default=30.0, gt=0)
    prompt_version: str = "assessment_v1"


class LLMResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    raw_text: str
    provider: str
    model: str
    prompt_version: str = ""
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    latency_ms: float = 0.0
    request_id: Optional[str] = None
    finish_reason: Optional[str] = None
    success: bool = True


class LLMErrorDetail(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider: str
    error_type: str
    error_message: str
    retryable: bool = False
    request_id: Optional[str] = None


class StructuredLLMResult(BaseModel, Generic[T]):
    model_config = ConfigDict(extra="forbid")

    parsed: Optional[T] = None
    response: Optional[LLMResponse] = None
    error: Optional[LLMErrorDetail] = None
    validation_errors: list[str] = Field(default_factory=list)
