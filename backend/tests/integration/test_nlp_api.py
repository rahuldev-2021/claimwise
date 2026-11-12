from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_nlp_analyze_by_claim_id():
    response = client.post("/api/v1/nlp/analyze", json={"claim_id": "CLM-001"})
    assert response.status_code == 200
    body = response.json()
    assert body["claim_id"] == "CLM-001"
    assert body["structured_extraction"]["symptom"] == "abnormal_noise"
    assert body["processing_metadata"]["pipeline_version"] == "0.2.1"
    assert body["original_complaint"]


def test_nlp_analyze_missing_claim():
    response = client.post("/api/v1/nlp/analyze", json={"claim_id": "NO-SUCH"})
    assert response.status_code == 404


def test_nlp_analyze_requires_xor_body():
    response = client.post("/api/v1/nlp/analyze", json={})
    assert response.status_code == 422
