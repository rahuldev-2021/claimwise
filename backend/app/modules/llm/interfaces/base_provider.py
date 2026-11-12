"""Abstract LLM provider contract."""

from abc import ABC, abstractmethod

from app.modules.llm.configuration.capabilities import ProviderCapabilities
from app.modules.llm.interfaces.llm_schemas import LLMRequest, LLMResponse


class BaseLLMProvider(ABC):
    @property
    @abstractmethod
    def provider_id(self) -> str:
        ...

    @property
    @abstractmethod
    def model_name(self) -> str:
        ...

    @abstractmethod
    def capabilities(self) -> ProviderCapabilities:
        ...

    @abstractmethod
    async def generate(self, request: LLMRequest) -> LLMResponse:
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        ...

    def generate_sync(self, request: LLMRequest) -> LLMResponse:
        import asyncio

        return asyncio.run(self.generate(request))

    def health_check_sync(self) -> bool:
        import asyncio

        return asyncio.run(self.health_check())
