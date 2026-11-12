"""LLM module exceptions."""

from app.core.exceptions import ClaimWiseError


class LLMError(ClaimWiseError):
    """Base LLM error."""


class LLMConfigurationError(LLMError):
    """Invalid or incomplete LLM configuration."""


class LLMProviderError(LLMError):
    """Provider request failed."""

    def __init__(
        self,
        message: str,
        *,
        provider: str = "",
        retryable: bool = False,
    ) -> None:
        self.provider = provider
        self.retryable = retryable
        super().__init__(message)


class LLMCapabilityError(LLMError):
    """Requested capability not supported by provider."""


class LLMValidationError(LLMError):
    """Structured output failed grounding or schema validation."""
