"""Phase 5 recommendations API — shared reasoning pipeline, no financial ML."""

from app.auth.dependencies import CurrentUser
from app.core.config import Settings
from app.modules.rag.retrieval_access import RetrievalAccessContext
from app.modules.recommendation.decision_audit import record_recommendation_run
from app.schemas.recommendation_analyze import RecommendationAnalyzeResponse, RecommendationExecutionMetadata
from app.services.claim_service import ClaimService
from app.services.reasoning_pipeline import ReasoningPipeline, ReasoningPipelineOptions


class RecommendationService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._claims = ClaimService(settings)
        self._pipeline = ReasoningPipeline(settings)

    @classmethod
    def for_tests(cls, settings: Settings) -> "RecommendationService":
        from app.services.rag_service import RAGService

        service = cls(settings)
        service._pipeline = ReasoningPipeline(settings, rag=RAGService.for_tests(settings))
        return service

    def analyze_for_user(
        self,
        claim_id: str,
        user: CurrentUser,
        *,
        force_refresh: bool = False,
        llm_enabled: bool | None = None,
        llm_provider: str | None = None,
        top_k: int | None = None,
        auto_ingest: bool | None = None,
    ) -> RecommendationAnalyzeResponse:
        claim = self._claims.get_claim_for_user(claim_id.strip(), user)
        org = self._claims.get_persisted_org_id(claim.claim_id) or user.org_id or ""
        access = RetrievalAccessContext(org_id=org, claim_id=claim.claim_id)
        persisted = self._claims.get_persisted_for_user(claim.claim_id, user)

        options = ReasoningPipelineOptions(
            top_k=top_k,
            auto_ingest=auto_ingest,
            llm_enabled=llm_enabled,
            force_refresh=force_refresh,
            llm_provider=llm_provider,
            run_financial=False,
            financial_enabled=False,
        )
        result = self._pipeline.run(claim, options=options, access=access, persisted=persisted)

        if org and result.llm_record:
            self._claims.append_llm_recommendation(
                claim.claim_id,
                org,
                result.llm_record.model_dump(mode="json"),
                history_max=self._settings.LLM_RECOMMENDATION_HISTORY_MAX,
            )

        response = RecommendationAnalyzeResponse(
            claim_id=claim.claim_id,
            technical_validation=result.technical,
            llm_contextual_assessment=result.llm_assessment,
            llm_execution=result.llm_execution,
            recommendation=result.recommendation,
            llm_recommendation_record=result.llm_record,
            execution_metadata=RecommendationExecutionMetadata(
                duration_ms=result.duration_ms,
                phase5_input_fingerprint=result.phase5_fingerprint,
            ),
        )
        record_recommendation_run(response)
        return response
