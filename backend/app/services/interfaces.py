"""Module interface contracts for CLAIMWISE.

Each Protocol defines the inputs and outputs a future module must satisfy.
Implementations will live in app/modules/<module_name>/.
Phase 1 provides no concrete implementations.
"""

from typing import Protocol, runtime_checkable

from app.modules.llm.schemas.llm_assessment import LLMContextualAssessment
from app.modules.nlp.schemas import NLPAnalysisResult
from app.modules.rag.schemas import RetrievalMode, RetrievalResult
from app.schemas.claim import ClaimInput
from app.schemas.financial_validation import FinancialValidationResult
from app.schemas.recommendation import ClaimRecommendation
from app.schemas.repair_document import RepairDocument
from app.schemas.technical_validation import TechnicalValidationResult


# ── NLP Module ────────────────────────────────────────────────────────────────


@runtime_checkable
class NLPModule(Protocol):
    """Extracts structured information from free-text claim fields."""

    def extract(self, claim: ClaimInput) -> NLPAnalysisResult:
        """Parse customer complaint and technician diagnosis into
        structured entities using the shared extraction schema."""
        ...


@runtime_checkable
class ContextualExtractionModule(Protocol):
    """Future contextual extraction (e.g. LLM) layered on deterministic NLP."""

    def enrich(self, claim: ClaimInput, deterministic: NLPAnalysisResult) -> NLPAnalysisResult:
        """Enrich or merge structured fields after deterministic extraction."""
        ...


# ── RAG Module ────────────────────────────────────────────────────────────────


@runtime_checkable
class RAGModule(Protocol):
    """Retrieves similar historical repair cases."""

    def retrieve_for_claim(
        self,
        claim: ClaimInput,
        *,
        top_k: int = 5,
        mode: RetrievalMode = RetrievalMode.ADVANCED,
    ) -> RetrievalResult:
        """Search the historical case index and return ranked evidence
        with source document IDs and relevance scores."""
        ...


# ── Technical Validation Module ───────────────────────────────────────────────


@runtime_checkable
class TechnicalValidationModule(Protocol):
    """Determines whether the complaint and diagnosis support the repair."""

    def validate(
        self,
        claim: ClaimInput,
        *,
        nlp: NLPAnalysisResult,
        retrieval: RetrievalResult,
    ) -> TechnicalValidationResult:
        """Compare the recommended repair against retrieved evidence
        and return a technical verdict with citations."""
        ...


@runtime_checkable
class ContextualTechnicalReasoner(Protocol):
    """Deprecated Phase 4 stub; use ContextualAssessmentProvider instead."""

    def enrich(
        self,
        claim: ClaimInput,
        deterministic: TechnicalValidationResult,
    ) -> TechnicalValidationResult:
        ...


@runtime_checkable
class ContextualAssessmentProvider(Protocol):
    """Advisory LLM contextual assessment (does not mutate technical validation)."""

    def assess(
        self,
        claim: ClaimInput,
        *,
        nlp: NLPAnalysisResult,
        retrieval: RetrievalResult,
        technical: TechnicalValidationResult,
    ) -> LLMContextualAssessment | None:
        ...


# ── Financial Validation Module ───────────────────────────────────────────────


@runtime_checkable
class FinancialValidationModule(Protocol):
    """Estimates expected parts cost and labour hours for the submitted repair."""

    def validate(
        self,
        claim: ClaimInput,
    ) -> FinancialValidationResult:
        """Return predicted cost and hours for the candidate repair,
        comparing with catalogue baselines and the ML model range."""
        ...


# ── Recommendation Module ────────────────────────────────────────────────────


@runtime_checkable
class RecommendationModule(Protocol):
    """Combines technical and financial results into one assessment."""

    def recommend(
        self,
        technical: TechnicalValidationResult,
        financial: FinancialValidationResult | None,
    ) -> ClaimRecommendation:
        """Apply business rules and generate the overall recommendation
        with an evidence-based explanation."""
        ...
