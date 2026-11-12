import pytest
from fastapi.testclient import TestClient

from app.api.routes import assessment as assessment_routes
from app.core.config import Settings
from app.services.assessment_service import AssessmentService
from app.services.rag_service import RAGService
from tests.conftest import SAMPLE_DATA_DIR


@pytest.fixture()
def assessment_api_service(settings, monkeypatch):
    rag = RAGService.for_tests(settings.model_copy(update={"SAMPLE_DATA_DIR": str(SAMPLE_DATA_DIR)}))
    rag.ingest(force_reindex=True)
    svc_settings = settings.model_copy(
        update={
            "SAMPLE_DATA_DIR": str(SAMPLE_DATA_DIR),
            "LLM_ENABLED": True,
            "LLM_PROVIDER": "mock",
        }
    )
    service = AssessmentService.for_tests(svc_settings)
    service._pipeline._rag = rag
    monkeypatch.setattr(assessment_routes, "_assessment_service", service)
    return service


def test_assessment_analyze_requires_auth():
    from main import app

    bare = TestClient(app)
    response = bare.post(
        "/api/v1/assessment/analyze",
        json={"claim_id": "CLM-002", "auto_ingest": False},
    )
    assert response.status_code == 401


def test_assessment_analyze_by_claim_id(assessment_api_service, client: TestClient):
    response = client.post(
        "/api/v1/assessment/analyze",
        json={"claim_id": "CLM-002", "top_k": 5, "auto_ingest": False, "llm_enabled": True},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["claim_id"] == "CLM-002"
    assert body["recommendation"]["overall_recommendation"]
    assert body["llm_execution"]["status"] in ("SUCCESS", "DISABLED", "FAILED")


def test_assessment_latest_404_for_sample_claim(client: TestClient):
    response = client.get("/api/v1/claims/CLM-002/assessment/latest")
    assert response.status_code == 404


def test_llm_health_endpoint():
    from main import app

    response = TestClient(app).get("/api/v1/llm/health")
    assert response.status_code == 200
    body = response.json()
    assert "supported_providers" in body
    assert "gemini" in body["supported_providers"]
