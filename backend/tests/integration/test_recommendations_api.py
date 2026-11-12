import pytest
from fastapi.testclient import TestClient

from app.api.routes import recommendations as recommendation_routes
from app.services.recommendation_service import RecommendationService
from app.services.rag_service import RAGService
from tests.conftest import SAMPLE_DATA_DIR


@pytest.fixture()
def recommendation_api_service(settings, monkeypatch):
    rag = RAGService.for_tests(settings.model_copy(update={"SAMPLE_DATA_DIR": str(SAMPLE_DATA_DIR)}))
    rag.ingest(force_reindex=True)
    svc_settings = settings.model_copy(
        update={
            "SAMPLE_DATA_DIR": str(SAMPLE_DATA_DIR),
            "LLM_ENABLED": True,
            "LLM_PROVIDER": "mock",
        }
    )
    service = RecommendationService.for_tests(svc_settings)
    service._pipeline._rag = rag
    monkeypatch.setattr(recommendation_routes, "_recommendation_service", service)
    return service


def test_recommendations_analyze_requires_auth():
    from main import app

    bare = TestClient(app)
    res = bare.post(
        "/api/v1/recommendations/analyze",
        json={"claim_id": "CLM-002"},
    )
    assert res.status_code == 401


def test_recommendations_analyze_e2e(recommendation_api_service, client: TestClient):
    res = client.post(
        "/api/v1/recommendations/analyze",
        json={"claim_id": "CLM-002", "top_k": 3},
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["recommendation"]["human_review_required"] is True
    assert body["execution_metadata"]["phase5_input_fingerprint"]
    assert body["recommendation"].get("financial_validation") is None
