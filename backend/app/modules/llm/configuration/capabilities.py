"""Provider capability model."""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ProviderCapabilities(BaseModel):
    model_config = ConfigDict(extra="forbid")

    structured_json: bool = False
    json_schema: bool = False
    tool_calling: bool = False
    streaming: bool = False
    max_context_tokens: Optional[int] = None
    vision: bool = False

    def supports_structured_output(self) -> bool:
        return self.structured_json or self.json_schema
