"""Shared NLP → RAG → TV → LLM → recommendation pipeline (Phase 5)."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Optional

from app.auth.dependencies import CurrentUser
from app.core.config import Settings
from app.modules.llm.fingerprint import build_phase5_input_fingerprint, default_prompt_version
from app.modules.llm.orchestration.llm_orchestrator import LLMOrchestrator
from app.modules.llm.schemas.llm_assessment import LLMContextualAssessment
from app.modules.llm.versions import LLM_SCHEMA_VERSION
from app.modules.nlp.schemas import NLPAnalysisResult
from app.modules.rag.retrieval_access import RetrievalAccessContext
from app.modules.rag.schemas import RetrievalMode, RetrievalResult
from app.modules.recommendation.recommendation_engine import RecommendationEngine
from app.modules.recommendation.schemas.context import RecommendationContext
from app.modules.technical_validation.fingerprint import build_input_fingerprint
from app.modules.technical_validation.technical_validation_pipeline import validate_technical
from app.schemas.claim import ClaimInput
from app.schemas.claim_assessment import AssessmentExecutionMetadata
from app.schemas.llm_execution import LLMExecutionRecord, LLMExecutionStatus
from app.schemas.llm_recommendation import LLMRecommendationProcessingStatus, LLMRecommendationRecord
from app.schemas.persisted_claim import PersistedClaim
from app.schemas.recommendation import ClaimRecommendation, FinancialAssessmentStatus
from app.schemas.technical_validation import TechnicalValidationResult
from app.services.nlp_analysis_service import NLPAnalysisService
from app.services.rag_service import RAGNotReadyError, RAGService
from app.services.rag_service_provider import get_rag_service

logger = logging.getLogger(__name__)


@dataclass
class ReasoningPipelineOptions:
    top_k: int | None = None
    retrieval_mode: RetrievalMode | None = None
    auto_ingest: bool | None = None
    llm_enabled: bool | None = None
    financial_enabled: bool | None = None
    force_refresh: bool = False
    llm_provider: str | None = None
    run_financial: bool = True


@dataclass
class ReasoningPipelineResult:
    claim: ClaimInput
    nlp: NLPAnalysisResult
    retrieval: RetrievalResult
    technical: TechnicalValidationResult
    llm_assessment: LLMContextualAssessment | None
    llm_execution: LLMExecutionRecord
    recommendation: ClaimRecommendation
    phase5_fingerprint: str
    llm_record: LLMRecommendationRecord | None
    duration_ms: float
    rag_mode: str
    financial_assessment_status: FinancialAssessmentStatus


class ReasoningPipeline:
    def __init__(self, settings: Settings, *, rag: RAGService | None = None) -> None:
        self._settings = settings
        self._nlp = NLPAnalysisService(settings)
        self._rag = rag or get_rag_service(settings)
        self._recommendation = RecommendationEngine()

    def run(
        self,
        claim: ClaimInput,
        *,
        options: ReasoningPipelineOptions,
        access: RetrievalAccessContext | None,
        persisted: PersistedClaim | None = None,
    ) -> ReasoningPipelineResult:
        started = time.perf_counter()
        effective_settings = self._settings
        if options.llm_enabled is not None:
            effective_settings = effective_settings.model_copy(
                update={"LLM_ENABLED": options.llm_enabled}
            )

        k = options.top_k if options.top_k is not None else self._settings.TV_DEFAULT_TOP_K
        nlp, retrieval, technical = self._resolve_stages(
            claim, options=options, access=access, persisted=persisted, top_k=k
        )

        prompt_version = default_prompt_version(effective_settings)
        provider_name = options.llm_provider or effective_settings.LLM_PROVIDER
        model_name = effective_settings.LLM_MODEL or "default"

        phase5_fp = build_phase5_input_fingerprint(
            claim,
            nlp,
            retrieval,
            technical,
            settings=effective_settings,
            top_k=k,
            prompt_version=prompt_version,
            schema_version=LLM_SCHEMA_VERSION,
            provider=provider_name,
            model=model_name,
        )

        llm_assessment, llm_execution, llm_record = self._resolve_llm(
            claim,
            nlp,
            retrieval,
            technical,
            effective_settings=effective_settings,
            options=options,
            persisted=persisted,
            phase5_fp=phase5_fp,
            provider_name=provider_name,
        )

        fin_enabled = False
        financial_result = None
        financial_status = FinancialAssessmentStatus.PENDING
        if options.run_financial:
            fin_enabled = (
                options.financial_enabled
                if options.financial_enabled is not None
                else None
            )
            if fin_enabled is None:
                from app.modules.financial_validation.services.financial_validation_service import (
                    financial_validation_enabled,
                )

                fin_enabled = financial_validation_enabled(self._settings)
            if fin_enabled:
                financial_status, financial_result = self._run_financial(claim)

        rec_ctx = RecommendationContext(
            claim=claim,
            nlp=nlp,
            technical=technical,
            llm_assessment=llm_assessment,
            llm_execution=llm_execution,
            retrieval_passage_count=len(retrieval.passages),
            financial=financial_result,
            financial_available=financial_result is not None,
            financial_enabled=bool(fin_enabled),
        )
        recommendation = self._recommendation.recommend(rec_ctx)

        duration_ms = (time.perf_counter() - started) * 1000
        mode = (
            options.retrieval_mode.value
            if options.retrieval_mode
            else self._settings.TV_RETRIEVAL_MODE
        )

        return ReasoningPipelineResult(
            claim=claim,
            nlp=nlp,
            retrieval=retrieval,
            technical=technical,
            llm_assessment=llm_assessment,
            llm_execution=llm_execution,
            recommendation=recommendation,
            phase5_fingerprint=phase5_fp,
            llm_record=llm_record,
            duration_ms=duration_ms,
            rag_mode=mode,
            financial_assessment_status=financial_status,
        )

    def _resolve_stages(
        self,
        claim: ClaimInput,
        *,
        options: ReasoningPipelineOptions,
        access: RetrievalAccessContext | None,
        persisted: PersistedClaim | None,
        top_k: int,
    ) -> tuple[NLPAnalysisResult, RetrievalResult, TechnicalValidationResult]:
        reuse = (
            not options.force_refresh
            and self._settings.PHASE5_REUSE_CACHED_STAGES
            and persisted is not None
        )
        if reuse and persisted.nlp_analysis and persisted.rag_retrieval and persisted.technical_validation:
            fp = build_input_fingerprint(
                claim, persisted.nlp_analysis, persisted.rag_retrieval, top_k=top_k
            )
            if fp == persisted.technical_validation.input_fingerprint:
                return (
                    persisted.nlp_analysis,
                    persisted.rag_retrieval,
                    persisted.technical_validation,
                )

        nlp = self._nlp.analyze_claim(claim)
        retrieval = self._retrieve(
            claim,
            top_k=top_k,
            retrieval_mode=options.retrieval_mode,
            auto_ingest=options.auto_ingest,
            access=access,
            nlp=nlp,
        )
        technical = validate_technical(claim, nlp, retrieval, top_k=top_k)
        return nlp, retrieval, technical

    def _resolve_llm(
        self,
        claim: ClaimInput,
        nlp: NLPAnalysisResult,
        retrieval: RetrievalResult,
        technical: TechnicalValidationResult,
        *,
        effective_settings: Settings,
        options: ReasoningPipelineOptions,
        persisted: PersistedClaim | None,
        phase5_fp: str,
        provider_name: str,
    ) -> tuple[LLMContextualAssessment | None, LLMExecutionRecord, LLMRecommendationRecord | None]:
        if (
            not options.force_refresh
            and self._settings.PHASE5_REUSE_LLM_IF_FINGERPRINT_MATCH
            and persisted
            and persisted.latest_llm_recommendation_id
        ):
            for entry in reversed(persisted.llm_recommendation_executions or []):
                if (
                    entry.recommendation_id == persisted.latest_llm_recommendation_id
                    and entry.input_fingerprint == phase5_fp
                    and entry.processing_status
                    in (
                        LLMRecommendationProcessingStatus.SUCCESS,
                        LLMRecommendationProcessingStatus.REUSED,
                    )
                    and entry.assessment is not None
                ):
                    assessment = LLMContextualAssessment(
                        assessment=entry.assessment,
                        prompt_version=entry.prompt_version,
                        schema_version=entry.schema_version,
                    )
                    execution = LLMExecutionRecord(
                        status=LLMExecutionStatus.SUCCESS,
                        configured_provider=provider_name,
                        actual_provider=entry.provider,
                        actual_model=entry.model,
                        prompt_version=entry.prompt_version,
                    )
                    record = entry.model_copy(
                        update={"processing_status": LLMRecommendationProcessingStatus.REUSED}
                    )
                    return assessment, execution, record

        orchestrator = LLMOrchestrator(effective_settings)
        llm_assessment, llm_execution = orchestrator.run_contextual_assessment(
            claim,
            nlp,
            retrieval,
            technical,
            provider=options.llm_provider,
        )

        status = LLMRecommendationProcessingStatus.FAILED
        if llm_execution.status == LLMExecutionStatus.DISABLED:
            status = LLMRecommendationProcessingStatus.DISABLED
        elif llm_execution.status in (LLMExecutionStatus.SUCCESS, LLMExecutionStatus.FALLBACK):
            status = LLMRecommendationProcessingStatus.SUCCESS

        evidence_refs: list[str] = []
        assessment_body = None
        workflow = None
        if llm_assessment:
            assessment_body = llm_assessment.assessment
            workflow = llm_assessment.assessment.workflow_recommendation
            evidence_refs = list(
                dict.fromkeys(c.document_id for c in llm_assessment.assessment.cited_evidence)
            )

        record = LLMRecommendationRecord(
            claim_id=claim.claim_id,
            provider=llm_execution.actual_provider or provider_name,
            model=llm_execution.actual_model or effective_settings.LLM_MODEL,
            prompt_version=llm_execution.prompt_version or default_prompt_version(effective_settings),
            schema_version=LLM_SCHEMA_VERSION,
            input_fingerprint=phase5_fp,
            assessment=assessment_body,
            workflow_recommendation=workflow,
            evidence_references=evidence_refs,
            processing_status=status,
            error_message=llm_execution.error_message,
        )
        return llm_assessment, llm_execution, record

    def _run_financial(self, claim: ClaimInput):
        from app.modules.financial_validation.services.financial_validation_service import (
            FinancialValidationService,
        )

        try:
            financial_result = FinancialValidationService(self._settings).validate(claim)
            financial_status = (
                FinancialAssessmentStatus.AVAILABLE
                if financial_result.predicted_parts_cost is not None
                and financial_result.predicted_labour_hours is not None
                else FinancialAssessmentStatus.UNAVAILABLE
            )
            return financial_status, financial_result
        except Exception:
            logger.exception("Financial validation failed for claim %s", claim.claim_id)
            return FinancialAssessmentStatus.UNAVAILABLE, None

    def _retrieve(
        self,
        claim: ClaimInput,
        *,
        top_k: int,
        retrieval_mode: RetrievalMode | None,
        auto_ingest: bool | None,
        access: RetrievalAccessContext | None,
        nlp: NLPAnalysisResult,
    ) -> RetrievalResult:
        mode_str = (
            retrieval_mode.value if retrieval_mode else self._settings.TV_RETRIEVAL_MODE.lower()
        )
        mode = RetrievalMode.BASIC if mode_str == "basic" else RetrievalMode.ADVANCED
        use_ingest = auto_ingest if auto_ingest is not None else self._settings.TV_AUTO_INGEST
        try:
            return self._rag.retrieve_for_claim(
                claim,
                top_k=top_k,
                mode=mode,
                run_nlp=False,
                nlp_result=nlp,
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
                    nlp_result=nlp,
                    access=access,
                )
            raise
