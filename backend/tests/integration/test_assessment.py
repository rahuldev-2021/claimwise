import pytest

from app.core.config import Settings
from app.schemas.llm_execution import LLMExecutionStatus
from app.services.assessment_service import AssessmentService


@pytest.fixture()
def assessment_service(settings, indexed_rag):
    svc_settings = settings.model_copy(
        update={
            "LLM_ENABLED": True,
            "LLM_PROVIDER": "mock",
            "LLM_MODEL": "mock-model",
            "FINANCIAL_EXPERIMENTAL_MODELS_ENABLED": False,
        }
    )
    service = AssessmentService.for_tests(svc_settings)
    service._pipeline._rag = indexed_rag
    return service


def test_full_assessment_with_mock_llm(repository, assessment_service):
    claim = repository.get_claim("CLM-002")
    result = assessment_service.analyze_claim(claim, top_k=3)
    assert result.claim_id == "CLM-002"
    assert result.nlp_analysis.claim_id == "CLM-002"
    assert result.retrieval.passages
    assert result.technical_validation.claim_id == "CLM-002"
    assert result.llm_execution.status == LLMExecutionStatus.SUCCESS
    assert result.llm_contextual_assessment is not None
    assert result.recommendation.human_review_required is True
    assert result.recommendation.financial_assessment_status.value == "UNAVAILABLE"


def test_assessment_financial_disabled_pending(repository, assessment_service):
    claim = repository.get_claim("CLM-002")
    result = assessment_service.analyze_claim(claim, top_k=3, financial_enabled=False)
    assert result.execution_metadata.financial_assessment_status.value == "PENDING"


def test_assessment_llm_disabled(settings, repository, indexed_rag):
    svc_settings = settings.model_copy(update={"LLM_ENABLED": False})
    service = AssessmentService.for_tests(svc_settings)
    service._pipeline._rag = indexed_rag
    claim = repository.get_claim("CLM-002")
    result = service.analyze_claim(claim, top_k=3)
    assert result.llm_execution.status == LLMExecutionStatus.DISABLED
    assert result.llm_contextual_assessment is None
