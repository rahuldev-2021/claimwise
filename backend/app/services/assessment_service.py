"""Full claim assessment workflow (NLP, RAG, TV, LLM, recommendation)."""

import logging
from datetime import datetime, timezone

from app.auth.dependencies import CurrentUser
from app.core.config import Settings
from app.modules.rag.retrieval_access import RetrievalAccessContext
from app.modules.rag.schemas import RetrievalMode
from app.modules.recommendation.decision_audit import record_assessment
from app.schemas.claim import ClaimInput
from app.modules.dealer_communication.brief_builder import build_dealer_communication_brief
from app.schemas.claim_assessment import AssessmentExecutionMetadata, ClaimAssessmentResponse
from app.services.assessment_snapshot_status import mark_assessment_pipeline_complete
from app.services.claim_service import ClaimService
from app.services.rag_service import RAGService
from app.services.reasoning_pipeline import ReasoningPipeline, ReasoningPipelineOptions, ReasoningPipelineResult

logger = logging.getLogger(__name__)


class AssessmentService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._claims = ClaimService(settings)
        self._pipeline = ReasoningPipeline(settings)

    @classmethod
    def for_tests(cls, settings: Settings) -> "AssessmentService":
        service = cls(settings)
        service._pipeline = ReasoningPipeline(settings, rag=RAGService.for_tests(settings))
        return service

    def get_latest_for_user(self, claim_id: str, user: CurrentUser) -> ClaimAssessmentResponse | None:
        resp = self._claims.get_latest_assessment_for_user(claim_id, user)
        if resp is None:
            return None
        if resp.dealer_communication is not None:
            return resp
        try:
            claim = self._claims.get_claim_for_user(claim_id, user)
        except Exception:
            return resp
        brief = build_dealer_communication_brief(
            claim,
            resp.recommendation.financial_validation,
            resp.technical_validation,
            settings=self._settings,
        )
        return resp.model_copy(update={"dealer_communication": brief})

    def analyze_by_claim_id_for_user(
        self,
        claim_id: str,
        user: CurrentUser,
        *,
        top_k: int | None = None,
        retrieval_mode: RetrievalMode | None = None,
        auto_ingest: bool | None = None,
        llm_enabled: bool | None = None,
        financial_enabled: bool | None = None,
        force_refresh: bool = False,
        llm_provider: str | None = None,
    ) -> ClaimAssessmentResponse:
        claim = self._claims.get_claim_for_user(claim_id, user)
        return self.analyze_claim_for_user(
            claim,
            user,
            top_k=top_k,
            retrieval_mode=retrieval_mode,
            auto_ingest=auto_ingest,
            llm_enabled=llm_enabled,
            financial_enabled=financial_enabled,
            force_refresh=force_refresh,
            llm_provider=llm_provider,
        )

    def analyze_by_claim_id(
        self,
        claim_id: str,
        *,
        top_k: int | None = None,
        retrieval_mode: RetrievalMode | None = None,
        auto_ingest: bool | None = None,
        llm_enabled: bool | None = None,
        financial_enabled: bool | None = None,
        force_refresh: bool = False,
        llm_provider: str | None = None,
    ) -> ClaimAssessmentResponse:
        claim = self._claims.get_claim(claim_id)
        return self.analyze_claim(
            claim,
            top_k=top_k,
            retrieval_mode=retrieval_mode,
            auto_ingest=auto_ingest,
            llm_enabled=llm_enabled,
            financial_enabled=financial_enabled,
            force_refresh=force_refresh,
            llm_provider=llm_provider,
        )

    def analyze_claim_for_user(
        self,
        claim: ClaimInput,
        user: CurrentUser,
        *,
        top_k: int | None = None,
        retrieval_mode: RetrievalMode | None = None,
        auto_ingest: bool | None = None,
        llm_enabled: bool | None = None,
        financial_enabled: bool | None = None,
        force_refresh: bool = False,
        llm_provider: str | None = None,
    ) -> ClaimAssessmentResponse:
        org = self._claims.get_persisted_org_id(claim.claim_id) or user.org_id or ""
        access = RetrievalAccessContext(org_id=org, claim_id=claim.claim_id)
        persisted = self._claims.get_persisted_for_user(claim.claim_id, user)
        return self._run_assessment(
            claim,
            top_k=top_k,
            retrieval_mode=retrieval_mode,
            auto_ingest=auto_ingest,
            llm_enabled=llm_enabled,
            financial_enabled=financial_enabled,
            access=access,
            persisted=persisted,
            org_id=org,
            force_refresh=force_refresh,
            llm_provider=llm_provider,
            run_financial=True,
        )

    def analyze_claim(
        self,
        claim: ClaimInput,
        *,
        top_k: int | None = None,
        retrieval_mode: RetrievalMode | None = None,
        auto_ingest: bool | None = None,
        llm_enabled: bool | None = None,
        financial_enabled: bool | None = None,
        force_refresh: bool = False,
        llm_provider: str | None = None,
    ) -> ClaimAssessmentResponse:
        org = self._claims.get_persisted_org_id(claim.claim_id) or ""
        access = RetrievalAccessContext(org_id=org, claim_id=claim.claim_id) if org else None
        persisted = self._claims.get_persisted(claim.claim_id, org_id=org or None)
        return self._run_assessment(
            claim,
            top_k=top_k,
            retrieval_mode=retrieval_mode,
            auto_ingest=auto_ingest,
            llm_enabled=llm_enabled,
            financial_enabled=financial_enabled,
            access=access,
            persisted=persisted,
            org_id=org,
            force_refresh=force_refresh,
            llm_provider=llm_provider,
            run_financial=True,
        )

    def _run_assessment(
        self,
        claim: ClaimInput,
        *,
        top_k: int | None,
        retrieval_mode: RetrievalMode | None,
        auto_ingest: bool | None,
        llm_enabled: bool | None,
        financial_enabled: bool | None,
        access: RetrievalAccessContext | None,
        persisted,
        org_id: str,
        force_refresh: bool,
        llm_provider: str | None,
        run_financial: bool,
    ) -> ClaimAssessmentResponse:
        options = ReasoningPipelineOptions(
            top_k=top_k,
            retrieval_mode=retrieval_mode,
            auto_ingest=auto_ingest,
            llm_enabled=llm_enabled,
            financial_enabled=financial_enabled,
            force_refresh=force_refresh,
            llm_provider=llm_provider,
            run_financial=run_financial,
        )
        result = self._pipeline.run(
            claim, options=options, access=access, persisted=persisted
        )
        self._persist_llm_record(org_id, result)

        dealer_brief = build_dealer_communication_brief(
            claim,
            result.recommendation.financial_validation,
            result.technical,
            settings=self._settings,
        )
        response = ClaimAssessmentResponse(
            claim_id=claim.claim_id,
            nlp_analysis=result.nlp,
            retrieval=result.retrieval,
            technical_validation=result.technical,
            llm_contextual_assessment=result.llm_assessment,
            llm_execution=result.llm_execution,
            recommendation=result.recommendation,
            execution_metadata=AssessmentExecutionMetadata(
                duration_ms=result.duration_ms,
                rag_mode=result.rag_mode,
                financial_assessment_status=result.financial_assessment_status,
            ),
            dealer_communication=dealer_brief,
        )
        record_assessment(response, phase5_fingerprint=result.phase5_fingerprint)
        self._persist_snapshot(org_id, response, result, persisted)
        return response

    def _persist_snapshot(
        self,
        org_id: str,
        response: ClaimAssessmentResponse,
        result: ReasoningPipelineResult,
        persisted,
    ) -> None:
        if not org_id:
            return
        ps = mark_assessment_pipeline_complete(persisted.processing_status if persisted else None)
        patch = {
            "latest_assessment": response.model_dump(mode="json"),
            "latest_assessment_at": datetime.now(timezone.utc).isoformat(),
            "latest_assessment_fingerprint": result.phase5_fingerprint,
            "nlp_analysis": result.nlp.model_dump(mode="json"),
            "rag_retrieval": result.retrieval.model_dump(mode="json"),
            "technical_validation": result.technical.model_dump(mode="json"),
            "processing_status": ps.model_dump(mode="json"),
        }
        self._claims.update_persisted(response.claim_id, org_id, patch)

    def _persist_llm_record(self, org_id: str, result) -> None:
        if not org_id or not result.llm_record:
            return
        self._claims.append_llm_recommendation(
            result.claim.claim_id,
            org_id,
            result.llm_record.model_dump(mode="json"),
            history_max=self._settings.LLM_RECOMMENDATION_HISTORY_MAX,
        )
