import pytest
from fastapi.testclient import TestClient

from app.api.routes import technical_validation as tv_routes
from app.services.technical_validation_service import TechnicalValidationService
from tests.conftest import SAMPLE_DATA_DIR


@pytest.fixture()
def tv_api_service(settings, monkeypatch):
    from app.services.rag_service import RAGService

    rag = RAGService.for_tests(settings.model_copy(update={"SAMPLE_DATA_DIR": str(SAMPLE_DATA_DIR)}))
    rag.ingest(force_reindex=True)
    tv = TechnicalValidationService.for_tests(settings)
    tv._rag = rag
    monkeypatch.setattr(tv_routes, "_tv_service", tv)
    return tv


def test_tv_analyze_requires_auth():
    from main import app

    bare = TestClient(app)
    response = bare.post(
        "/api/v1/technical-validation/analyze",
        json={"claim_id": "CLM-002", "auto_ingest": False},
    )
    assert response.status_code == 401


def test_tv_analyze_by_claim_id(tv_api_service, client: TestClient):
    response = client.post(
        "/api/v1/technical-validation/analyze",
        json={"claim_id": "CLM-002", "top_k": 5, "auto_ingest": False},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["claim_id"] == "CLM-002"
    assert body["technical_status"]
    assert body["triggered_rules"]


def test_tv_missing_claim_404(tv_api_service, client: TestClient):
    response = client.post(
        "/api/v1/technical-validation/analyze",
        json={"claim_id": "CLM-MISSING", "auto_ingest": False},
    )
    assert response.status_code == 404


def test_tv_rag_not_ready_503(settings, monkeypatch, client: TestClient):
    tv = TechnicalValidationService.for_tests(settings)
    monkeypatch.setattr(tv_routes, "_tv_service", tv)
    response = client.post(
        "/api/v1/technical-validation/analyze",
        json={"claim_id": "CLM-002", "auto_ingest": False},
    )
    assert response.status_code == 503
