import pytest
from fastapi.testclient import TestClient

from app.api.routes import rag as rag_routes
from app.main import app
from app.services.rag_service import RAGService
from tests.conftest import SAMPLE_DATA_DIR

client = TestClient(app)


@pytest.fixture()
def rag_api_service(settings, monkeypatch):
    service = RAGService.for_tests(settings.model_copy(update={"SAMPLE_DATA_DIR": str(SAMPLE_DATA_DIR)}))
    service.ingest(force_reindex=True)
    monkeypatch.setattr(rag_routes, "_rag_service", service)
    return service


def test_rag_health(rag_api_service):
    response = client.get("/api/v1/rag/health")
    assert response.status_code == 200
    body = response.json()
    assert body["indexed"] is True
    assert body["chunk_count"] > 0


def test_rag_search_after_ingest(rag_api_service):
    response = client.post(
        "/api/v1/rag/search",
        json={"query": "brake pad squeal", "top_k": 3, "mode": "advanced"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["passages"]


def test_rag_retrieve_for_claim(rag_api_service):
    response = client.post(
        "/api/v1/rag/retrieve-for-claim",
        json={"claim_id": "CLM-002", "top_k": 5},
    )
    assert response.status_code == 200
    assert response.json()["passages"]


def test_rag_search_before_ingest_returns_503(settings, monkeypatch):
    empty = RAGService.for_tests(settings)
    monkeypatch.setattr(rag_routes, "_rag_service", empty)
    response = client.post(
        "/api/v1/rag/search",
        json={"query": "brake noise", "top_k": 3},
    )
    assert response.status_code == 503
