from fastapi.testclient import TestClient


def test_list_claims_requires_auth():
    from main import app

    bare = TestClient(app)
    response = bare.get("/api/v1/claims")
    assert response.status_code == 401


def test_list_claims_returns_sample_claims(client: TestClient):
    response = client.get("/api/v1/claims")
    assert response.status_code == 200
    body = response.json()
    assert len(body) >= 2
    dates = [c["submission_date"] for c in body]
    assert dates == sorted(dates, reverse=True)


def test_list_claims_sort_ascending(client: TestClient):
    response = client.get("/api/v1/claims", params={"sort": "submission_date_asc"})
    dates = [c["submission_date"] for c in response.json()]
    assert dates == sorted(dates)


def test_list_claims_search_by_id(client: TestClient):
    response = client.get("/api/v1/claims", params={"q": "clm-002"})
    assert [c["claim_id"] for c in response.json()] == ["CLM-002"]


def test_list_claims_filter_by_category(client: TestClient):
    response = client.get("/api/v1/claims", params={"repair_category": "braking"})
    body = response.json()
    assert body
    assert all(c["recommended_repair"]["repair_category"] == "BRAKING" for c in body)


def test_list_claims_filter_by_status(client: TestClient):
    response = client.get("/api/v1/claims", params={"status": "UNDER_REVIEW"})
    assert response.status_code == 200
    assert all(c["claim_status"] == "UNDER_REVIEW" for c in response.json())


def test_list_claims_invalid_status_rejected(client: TestClient):
    response = client.get("/api/v1/claims", params={"status": "NOT_A_STATUS"})
    assert response.status_code == 422


def test_search_no_match_returns_empty_list(client: TestClient):
    response = client.get("/api/v1/claims", params={"q": "ZZZ-999"})
    assert response.status_code == 200
    assert response.json() == []


def test_get_claim(client: TestClient):
    response = client.get("/api/v1/claims/CLM-002")
    assert response.status_code == 200
    assert response.json()["claim_id"] == "CLM-002"


def test_get_claim_not_found(client: TestClient):
    response = client.get("/api/v1/claims/NO-SUCH")
    assert response.status_code == 404


def test_cors_allows_configured_origin(client: TestClient):
    response = client.get("/api/v1/claims", headers={"Origin": "http://localhost:5173"})
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"
