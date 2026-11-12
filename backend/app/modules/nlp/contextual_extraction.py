"""Extension point for future contextual (e.g. Gemini) extraction."""

from typing import Protocol, runtime_checkable

from app.modules.nlp.schemas import NLPAnalysisResult
from app.schemas.claim import ClaimInput


@runtime_checkable
class ContextualExtractionProvider(Protocol):
    """Optional provider that enriches deterministic NLP output."""

    def enrich(self, claim: ClaimInput, deterministic: NLPAnalysisResult) -> NLPAnalysisResult:
        """Return enriched analysis; may override or merge structured fields."""
        ...
