from datetime import datetime, timezone
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.api.deps.claims import get_claim_service
from app.auth.dependencies import CurrentUser, get_current_user
from app.schemas.claim import ClaimInput, ClaimStatus
from app.schemas.persisted_claim import PersistedClaim
from app.schemas.repair import Repair
from app.schemas.vehicle import Vehicle
from app.services.claim_service import ClaimService
from main import app

OTHER_ORG_CLAIM_ID = "CLM-OTHER-ORG"


def _other_org_claim() -> ClaimInput:
    return ClaimInput(
        claim_id=OTHER_ORG_CLAIM_ID,
        submission_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
        vehicle=Vehicle(vehicle_id="V9", make="Ford", model="F-150", model_year=2023),
        customer_complaint="Other-org claim must not be readable.",
        technician_diagnosis="N/A",
        recommended_repair=Repair(
            repair_category="BRAKING",
            part_description="Pads",
            recommended_action="Inspect",
        ),
        submitted_parts_cost=Decimal("100"),
        submitted_labour_hours=Decimal("1"),
        claim_status=ClaimStatus.SUBMITTED,
    )


@pytest.fixture()
def claim_service_other_org_isolated(settings, monkeypatch) -> ClaimService:
    """Simulate a mongo-only claim owned by org-acme; org-demo user must not see it."""
    service = ClaimService(settings)
    original_get = service._repo._mongo.get_by_claim_id
    record = PersistedClaim(org_id="org-acme", claim=_other_org_claim())

    def _get_by_claim_id(claim_id: str, org_id=None):
        if claim_id == OTHER_ORG_CLAIM_ID:
            if org_id == "org-demo":
                return None
            if org_id in (None, "org-acme"):
                return record
            return None
        return original_get(claim_id, org_id=org_id)

    monkeypatch.setattr(service._repo._mongo, "get_by_claim_id", _get_by_claim_id)
    return service


@pytest.fixture()
def client_other_org_isolated(test_user: CurrentUser, claim_service_other_org_isolated: ClaimService):
    def _user() -> CurrentUser:
        return test_user

    app.dependency_overrides[get_current_user] = _user
    app.dependency_overrides[get_claim_service] = lambda: claim_service_other_org_isolated
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_financial_health_returns_provisional():
    client = TestClient(app)
    response = client.get("/api/v1/financial-validation/health")
    assert response.status_code == 200
    body = response.json()
    assert body["config_loaded"] is True
    assert body["provisional_config"] is True


def test_financial_analyze_requires_auth():
    bare = TestClient(app)
    response = bare.post(
        "/api/v1/financial-validation/analyze",
        json={"claim_id": "CLM-001"},
    )
    assert response.status_code == 401


def test_financial_predict_requires_auth():
    bare = TestClient(app)
    response = bare.post(
        "/api/v1/financial-validation/predict",
        json={"claim_id": "CLM-001"},
    )
    assert response.status_code == 401


def test_financial_analyze_without_models(client: TestClient):
    response = client.post(
        "/api/v1/financial-validation/analyze",
        json={"claim_id": "CLM-001"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["claim_id"] == "CLM-001"
    assert data["predicted_parts_cost"] is None
    assert data["financial_status"] in ("INSUFFICIENT_DATA", "NEEDS_REVIEW")


def test_financial_predict_without_models(client: TestClient):
    response = client.post(
        "/api/v1/financial-validation/predict",
        json={"claim_id": "CLM-001"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["claim_id"] == "CLM-001"
    assert data["predicted_parts_cost"] is None
    assert data["models_available"] is False
    assert data["human_review_required"] is True


def test_financial_analyze_missing_claim_404(client: TestClient):
    response = client.post(
        "/api/v1/financial-validation/analyze",
        json={"claim_id": "CLM-MISSING"},
    )
    assert response.status_code == 404


def test_financial_predict_missing_claim_404(client: TestClient):
    response = client.post(
        "/api/v1/financial-validation/predict",
        json={"claim_id": "CLM-MISSING"},
    )
    assert response.status_code == 404


@pytest.mark.parametrize(
    "path",
    ["/api/v1/financial-validation/analyze", "/api/v1/financial-validation/predict"],
)
def test_financial_other_org_claim_404(client_other_org_isolated: TestClient, path: str):
    response = client_other_org_isolated.post(path, json={"claim_id": OTHER_ORG_CLAIM_ID})
    assert response.status_code == 404


def test_financial_models_requires_auth():
    bare = TestClient(app)
    response = bare.get("/api/v1/financial-validation/models")
    assert response.status_code == 401


def test_financial_models_with_auth(client: TestClient):
    response = client.get("/api/v1/financial-validation/models")
    assert response.status_code == 200
    body = response.json()
    assert "entries" in body
    assert "inference_mode" in body
