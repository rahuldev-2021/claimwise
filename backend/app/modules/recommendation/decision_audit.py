"""Structured assessment audit logging (no secrets or full PII)."""

import logging
from typing import Any

from app.schemas.claim_assessment import ClaimAssessmentResponse

logger = logging.getLogger("claimwise.audit")


def record_assessment(
    result: ClaimAssessmentResponse,
    *,
    phase5_fingerprint: str = "",
    schema_version: str = "",
    validation_error_count: int = 0,
) -> None:
    payload: dict[str, Any] = {
        "event": "claim_assessment",
        "assessment_id": result.execution_metadata.assessment_id,
        "claim_id": result.claim_id,
        "technical_status": result.technical_validation.technical_status.value,
        "recommendation": result.recommendation.overall_recommendation.value,
        "triggered_business_rules": result.recommendation.triggered_business_rules,
        "llm_status": result.llm_execution.status.value,
        "llm_provider": result.llm_execution.actual_provider
        or result.llm_execution.configured_provider,
        "llm_model": result.llm_execution.actual_model,
        "prompt_version": result.llm_execution.prompt_version,
        "schema_version": schema_version
        or (
            result.llm_contextual_assessment.schema_version
            if result.llm_contextual_assessment
            else ""
        ),
        "phase5_input_fingerprint": phase5_fingerprint,
        "llm_validation_error_count": validation_error_count,
        "latency_ms": result.llm_execution.latency_ms,
        "duration_ms": result.execution_metadata.duration_ms,
    }
    logger.info("assessment_completed %s", result.claim_id, extra=payload)


def record_recommendation_run(result) -> None:
    from app.schemas.recommendation_analyze import RecommendationAnalyzeResponse

    if not isinstance(result, RecommendationAnalyzeResponse):
        return
    meta = result.execution_metadata
    payload: dict[str, Any] = {
        "event": "recommendation_analyze",
        "recommendation_run_id": meta.recommendation_run_id,
        "claim_id": result.claim_id,
        "technical_status": result.technical_validation.technical_status.value,
        "recommendation": result.recommendation.overall_recommendation.value,
        "llm_status": result.llm_execution.status.value,
        "prompt_version": result.llm_execution.prompt_version,
        "schema_version": (
            result.llm_contextual_assessment.schema_version
            if result.llm_contextual_assessment
            else ""
        ),
        "phase5_input_fingerprint": meta.phase5_input_fingerprint,
        "processing_status": (
            result.llm_recommendation_record.processing_status.value
            if result.llm_recommendation_record
            else ""
        ),
        "duration_ms": meta.duration_ms,
    }
    logger.info("recommendation_completed %s", result.claim_id, extra=payload)
