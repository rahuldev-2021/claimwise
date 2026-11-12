"""Orchestrates NLP, RAG retrieval, and technical validation."""

import logging

from app.auth.dependencies import CurrentUser
from app.core.config import Settings
from app.modules.nlp.schemas import NLPAnalysisResult
from app.modules.rag.retrieval_access import RetrievalAccessContext
from app.modules.rag.schemas import RetrievalMode, RetrievalResult
from app.modules.technical_validation.technical_validation_pipeline import validate_technical
from app.schemas.claim import ClaimInput
from app.schemas.technical_validation import TechnicalValidationResult
from app.services.claim_service import ClaimService
from app.services.nlp_analysis_service import NLPAnalysisService
from app.services.rag_service import RAGNotReadyError, RAGService
from app.services.rag_service_provider import get_rag_service

logger = logging.getLogger(__name__)


class TechnicalValidationService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._claims = ClaimService(settings)
        self._nlp = NLPAnalysisService(settings)
        self._rag = get_rag_service(settings)

    @classmethod
    def for_tests(cls, settings: Settings) -> "TechnicalValidationService":
        service = cls(settings)
        service._rag = RAGService.for_tests(settings)
        return service

    def analyze_by_claim_id_for_user(
        self,
        claim_id: str,
        user: CurrentUser,
        *,
        top_k: int | None = None,
        retrieval_mode: RetrievalMode | None = None,
        auto_ingest: bool | None = None,
    ) -> TechnicalValidationResult:
        claim = self._claims.get_claim_for_user(claim_id, user)
        return self.analyze_claim_for_user(
            claim,
            user,
            top_k=top_k,
            retrieval_mode=retrieval_mode,
            auto_ingest=auto_ingest,
        )

    def analyze_by_claim_id(
        self,
        claim_id: str,
        *,
        top_k: int | None = None,
        retrieval_mode: RetrievalMode | None = None,
        auto_ingest: bool | None = None,
    ) -> TechnicalValidationResult:
        """Unscoped access — tests and worker only when claim resolution is already trusted."""
        claim = self._claims.get_claim(claim_id)
        org = self._claims.get_persisted_org_id(claim_id) or ""
        access = RetrievalAccessContext(org_id=org, claim_id=claim_id) if org else None
        return self._analyze(
            claim,
            top_k=top_k,
            retrieval_mode=retrieval_mode,
            auto_ingest=auto_ingest,
            access=access,
        )

    def analyze_claim_for_user(
        self,
        claim: ClaimInput,
        user: CurrentUser,
        *,
        top_k: int | None = None,
        retrieval_mode: RetrievalMode | None = None,
        auto_ingest: bool | None = None,
        nlp: NLPAnalysisResult | None = None,
        retrieval: RetrievalResult | None = None,
    ) -> TechnicalValidationResult:
        org = self._claims.get_persisted_org_id(claim.claim_id) or user.org_id or ""
        access = RetrievalAccessContext(org_id=org, claim_id=claim.claim_id)
        if nlp is not None and retrieval is not None:
            k = top_k if top_k is not None else self._settings.TV_DEFAULT_TOP_K
            return validate_technical(claim, nlp, retrieval, top_k=k)
        return self._analyze(
            claim,
            top_k=top_k,
            retrieval_mode=retrieval_mode,
            auto_ingest=auto_ingest,
            access=access,
            nlp=nlp,
        )

    def analyze_claim(
        self,
        claim: ClaimInput,
        *,
        top_k: int | None = None,
        retrieval_mode: RetrievalMode | None = None,
        auto_ingest: bool | None = None,
        nlp: NLPAnalysisResult | None = None,
        retrieval: RetrievalResult | None = None,
    ) -> TechnicalValidationResult:
        if nlp is not None and retrieval is not None:
            k = top_k if top_k is not None else self._settings.TV_DEFAULT_TOP_K
            return validate_technical(claim, nlp, retrieval, top_k=k)
        org = self._claims.get_persisted_org_id(claim.claim_id) or ""
        access = RetrievalAccessContext(org_id=org, claim_id=claim.claim_id) if org else None
        return self._analyze(
            claim,
            top_k=top_k,
            retrieval_mode=retrieval_mode,
            auto_ingest=auto_ingest,
            access=access,
            nlp=nlp,
            retrieval=retrieval,
        )

    def analyze_with_context(
        self,
        claim: ClaimInput,
        nlp: NLPAnalysisResult,
        retrieval: RetrievalResult,
        *,
        top_k: int | None = None,
    ) -> TechnicalValidationResult:
        k = top_k if top_k is not None else self._settings.TV_DEFAULT_TOP_K
        return validate_technical(claim, nlp, retrieval, top_k=k)

    def _analyze(
        self,
        claim: ClaimInput,
        *,
        top_k: int | None,
        retrieval_mode: RetrievalMode | None,
        auto_ingest: bool | None,
        access: RetrievalAccessContext | None,
        nlp: NLPAnalysisResult | None = None,
        retrieval: RetrievalResult | None = None,
    ) -> TechnicalValidationResult:
        nlp_result = nlp or self._nlp.analyze_claim(claim)
        k = top_k if top_k is not None else self._settings.TV_DEFAULT_TOP_K
        rag_result = retrieval or self._retrieve(
            claim,
            nlp_result=nlp_result,
            top_k=k,
            retrieval_mode=retrieval_mode,
            auto_ingest=auto_ingest,
            access=access,
        )
        return validate_technical(claim, nlp_result, rag_result, top_k=k)

    def _retrieve(
        self,
        claim: ClaimInput,
        *,
        nlp_result: NLPAnalysisResult | None,
        top_k: int,
        retrieval_mode: RetrievalMode | None,
        auto_ingest: bool | None,
        access: RetrievalAccessContext | None,
    ):
        mode_str = (
            retrieval_mode.value
            if retrieval_mode
            else self._settings.TV_RETRIEVAL_MODE.lower()
        )
        mode = (
            RetrievalMode.BASIC if mode_str == "basic" else RetrievalMode.ADVANCED
        )
        use_ingest = (
            auto_ingest if auto_ingest is not None else self._settings.TV_AUTO_INGEST
        )
        try:
            return self._rag.retrieve_for_claim(
                claim,
                top_k=top_k,
                mode=mode,
                run_nlp=False,
                nlp_result=nlp_result,
                access=access,
            )
        except RAGNotReadyError:
            if use_ingest:
                logger.info("RAG index not ready; running incremental corpus ingest")
                self._rag.ensure_startup_corpus() or self._rag.ingest(force_reindex=False)
                return self._rag.retrieve_for_claim(
                    claim,
                    top_k=top_k,
                    mode=mode,
                    run_nlp=False,
                    nlp_result=nlp_result,
                    access=access,
                )
            raise
