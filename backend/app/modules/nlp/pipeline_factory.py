"""Construct NLPPipeline with optional LLM contextual provider."""

from app.core.config import Settings
from app.modules.nlp.llm_contextual_provider import LLMContextualExtractionProvider
from app.modules.nlp.pipeline import NLPPipeline


def build_nlp_pipeline(settings: Settings) -> NLPPipeline:
    """Always attach contextual provider for fallback decision metadata; LLM call is gated internally."""
    return NLPPipeline(contextual=LLMContextualExtractionProvider(settings))
