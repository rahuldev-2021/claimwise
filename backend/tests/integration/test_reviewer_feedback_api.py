import pytest

from app.api.routes import reviewer_feedback as feedback_routes
from app.repositories.reviewer_feedback_repository import ReviewerFeedbackRepository


@pytest.fixture()
def feedback_repo(tmp_path, monkeypatch):
    repo = ReviewerFeedbackRepository(tmp_path / "feedback.json")
    monkeypatch.setattr(feedback_routes, "_feedback_repo", repo)
    return repo


def _payload(**overrides):
    body = {
        "claim_id": "CLM-002",
        "system_recommendation": "FLAG_FOR_REVIEW",
        "reviewer_decision": "ESCALATED",
        "reviewer_comments": "Needs senior review.",
    }
    body.update(overrides)
    return body


def test_submit_and_retrieve_feedback(feedback_repo, client):
    response = client.post("/api/v1/reviewer-feedback", json=_payload())
    assert response.status_code == 201
    created = response.json()
    assert created["claim_id"] == "CLM-002"
    assert created["system_recommendation"] == "FLAG_FOR_REVIEW"
    assert created["reviewed_at"] is not None

    listed = client.get("/api/v1/reviewer-feedback/CLM-002")
    assert listed.status_code == 200
    assert len(listed.json()) == 1
    assert listed.json()[0]["reviewer_comments"] == "Needs senior review."


def test_feedback_persisted_to_file(feedback_repo, tmp_path, client):
    client.post("/api/v1/reviewer-feedback", json=_payload())
    reloaded = ReviewerFeedbackRepository(tmp_path / "feedback.json")
    assert len(reloaded.list_for_claim("CLM-002")) == 1


def test_override_requires_reason(feedback_repo, client):
    response = client.post(
        "/api/v1/reviewer-feedback",
        json=_payload(overridden_recommendation="REQUEST_MORE_EVIDENCE"),
    )
    assert response.status_code == 422


def test_override_with_reason_accepted(feedback_repo, client):
    response = client.post(
        "/api/v1/reviewer-feedback",
        json=_payload(
            overridden_recommendation="REQUEST_MORE_EVIDENCE",
            override_reason="Measurements missing from report.",
        ),
    )
    assert response.status_code == 201
    assert response.json()["override_reason"] == "Measurements missing from report."


def test_override_equal_to_system_rejected(feedback_repo, client):
    response = client.post(
        "/api/v1/reviewer-feedback",
        json=_payload(overridden_recommendation="FLAG_FOR_REVIEW", override_reason="x"),
    )
    assert response.status_code == 422


def test_requested_info_needs_items(feedback_repo, client):
    response = client.post(
        "/api/v1/reviewer-feedback",
        json=_payload(reviewer_decision="REQUESTED_INFO"),
    )
    assert response.status_code == 422


def test_pending_decision_rejected(feedback_repo, client):
    response = client.post(
        "/api/v1/reviewer-feedback",
        json=_payload(reviewer_decision="PENDING"),
    )
    assert response.status_code == 422


def test_unknown_claim_404(feedback_repo, client):
    response = client.post("/api/v1/reviewer-feedback", json=_payload(claim_id="NO-SUCH"))
    assert response.status_code == 404
    assert client.get("/api/v1/reviewer-feedback/NO-SUCH").status_code == 404


def test_empty_history_returns_empty_list(feedback_repo, client):
    response = client.get("/api/v1/reviewer-feedback/CLM-001")
    assert response.status_code == 200
    assert response.json() == []
