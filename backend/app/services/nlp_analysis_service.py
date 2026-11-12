"""Orchestrates claim loading and NLP pipeline execution."""

import logging

from app.core.config import Settings
from app.core.exceptions import ClaimNotFoundError
from app.modules.nlp.failure_result import build_failure_result
from app.modules.nlp.pipeline_factory import build_nlp_pipeline
from app.modules.nlp.schemas import NLPAnalysisResult
from app.schemas.claim import ClaimInput
from app.services.claim_service import ClaimService

logger = logging.getLogger(__name__)


class NLPAnalysisService:
    def __init__(self, settings: Settings) -> None:
        self._claims = ClaimService(settings)
        self._pipeline = build_nlp_pipeline(settings)

    def analyze_by_claim_id(self, claim_id: str) -> NLPAnalysisResult:
        try:
            claim = self._claims.get_claim(claim_id)
        except ClaimNotFoundError:
            raise
        return self._run(claim)

    def analyze_claim(self, claim: ClaimInput) -> NLPAnalysisResult:
        return self._run(claim)

    def _run(self, claim: ClaimInput) -> NLPAnalysisResult:
        try:
            return self._pipeline.analyze(claim)
        except Exception as exc:
            logger.exception("NLP pipeline failed for claim %s", claim.claim_id)
            return build_failure_result(claim, str(exc))
