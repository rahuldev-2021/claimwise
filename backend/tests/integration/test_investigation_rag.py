"""Investigation worker RAG + TV wiring (test env)."""

import sys
from datetime import datetime, timezone
from unittest.mock import MagicMock

if "pypdf" not in sys.modules:
    sys.modules["pypdf"] = MagicMock()
from decimal import Decimal
import pytest

from app.core.config import Settings
from app.jobs.schemas import JobRecord
from app.modules.nlp.schemas import NLPAnalysisResult
from app.repositories.mongo_claim_repository import MongoClaimRepository
from app.repositories.mongo_repair_document_repository import MongoRepairDocumentRepository
from app.schemas.claim import ClaimInput, ClaimStatus
from app.schemas.persisted_claim import PersistedClaim
from app.schemas.processing_status import StageStatus
from app.schemas.repair import Repair
from app.schemas.vehicle import Vehicle
from app.services.investigation_handler import InvestigationHandler


@pytest.fixture
def settings():
    return Settings(
        APP_ENV="test",
        RAG_INVESTIGATION_ENABLED=True,
        RAG_WORKER_AUTO_INGEST_SAMPLE=True,
        INVESTIGATION_RUN_TECHNICAL_VALIDATION=True,
        INVESTIGATION_SKIP_TV_IF_PRESENT=False,
        LLM_NLP_ENABLED=False,
    )


def _claim() -> ClaimInput:
    return ClaimInput(
        claim_id="CLM-INV-1",
        submission_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
        vehicle=Vehicle(vehicle_id="V1", make="Ford", model="F-150", model_year=2023),
        customer_complaint="Squealing noise when braking at low speed.",
        technician_diagnosis="Front pads below minimum thickness.",
        recommended_repair=Repair(
            repair_category="BRAKING",
            part_description="Replace pads",
            recommended_action="Replace front brake pads",
        ),
        submitted_parts_cost=Decimal("0"),
        submitted_labour_hours=Decimal("1"),
        claim_status=ClaimStatus.SUBMITTED,
    )


def test_investigation_rag_and_tv_without_uploads(settings, monkeypatch):
    record = PersistedClaim(org_id="org_test", claim=_claim())
    claims = MagicMock(spec=MongoClaimRepository)
    claims.get_by_claim_id.return_value = record
    captured: dict = {}

    def _update(claim_id, org_id, patch):
        captured.update(patch)

    claims.update.side_effect = _update

    docs = MagicMock(spec=MongoRepairDocumentRepository)
    blobs = MagicMock()

    handler = InvestigationHandler(settings, claims, docs, blobs)
    job = JobRecord(job_id="j1", claim_id="CLM-INV-1", org_id="org_test", job_type="CLAIM_INVESTIGATION")

    handler.run(job)

    ps = captured["processing_status"]
    assert ps["nlp"]["status"] == StageStatus.COMPLETED.value
    assert ps["rag"]["status"] == StageStatus.COMPLETED.value
    assert ps["technical_validation"]["status"] == StageStatus.COMPLETED.value
    assert ps["overall"] == "READY"
    assert "rag_retrieval" in captured
    assert "technical_validation" in captured
