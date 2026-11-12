"""Internal recommendation context."""

from dataclasses import dataclass, field

from app.modules.llm.schemas.llm_assessment import LLMContextualAssessment
from app.modules.nlp.schemas import NLPAnalysisResult
from app.schemas.claim import ClaimInput
from app.schemas.llm_execution import LLMExecutionRecord, LLMExecutionStatus
from app.schemas.financial_validation import FinancialValidationResult
from app.schemas.technical_validation import TechnicalValidationResult


@dataclass
class RecommendationContext:
    claim: ClaimInput
    nlp: NLPAnalysisResult
    technical: TechnicalValidationResult
    llm_assessment: LLMContextualAssessment | None
    llm_execution: LLMExecutionRecord
    retrieval_passage_count: int = 0
    financial: FinancialValidationResult | None = None
    financial_available: bool = False
    financial_enabled: bool = True
    triggered_rules: list[str] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)
    llm_disagreement: bool = False

    @property
    def llm_available(self) -> bool:
        return self.llm_execution.status in (
            LLMExecutionStatus.SUCCESS,
            LLMExecutionStatus.FALLBACK,
        )
