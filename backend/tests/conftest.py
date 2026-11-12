"""Shared test fixtures for CLAIMWISE."""

from pathlib import Path

import pytest

_SPACY_OPTIONAL_MODULE = "tests.unit.test_spacy_optional"


@pytest.fixture(autouse=True)
def nlp_disable_spacy_for_deterministic_unit_tests(request, monkeypatch):
    """Keep unit tests stable on machines with spaCy installed; spaCy has its own module."""
    if request.module.__name__ == _SPACY_OPTIONAL_MODULE:
        return
    from app.core.config import Settings
    import app.modules.nlp.entity_extractor as entity_extractor

    disabled = Settings(NLP_ENABLE_SPACY=False)
    monkeypatch.setattr(entity_extractor, "get_settings", lambda: disabled)
from fastapi.testclient import TestClient

from app.auth.dependencies import CurrentUser, get_current_user
from main import app

SAMPLE_DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "sample"


@pytest.fixture()
def settings():
    from app.core.config import Settings

    return Settings(SAMPLE_DATA_DIR=str(SAMPLE_DATA_DIR), APP_ENV="test")


@pytest.fixture()
def repository():
    from app.repositories.sample_claim_repository import SampleClaimRepository

    return SampleClaimRepository(data_dir=SAMPLE_DATA_DIR)


@pytest.fixture()
def rag_service(settings):
    from app.services.rag_service import RAGService

    return RAGService.for_tests(settings)


@pytest.fixture()
def indexed_rag(rag_service):
    rag_service.ingest(force_reindex=True)
    return rag_service


@pytest.fixture()
def test_user() -> CurrentUser:
    return CurrentUser(
        user_id="test-user",
        email="reviewer@example.com",
        org_id="org-demo",
        roles=["warranty_agent"],
        permissions=["claims:read", "claims:submit", "claims:assess", "claims:review"],
        session_id="test-session",
    )


@pytest.fixture()
def client(test_user: CurrentUser):
    def _override() -> CurrentUser:
        return test_user

    app.dependency_overrides[get_current_user] = _override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
