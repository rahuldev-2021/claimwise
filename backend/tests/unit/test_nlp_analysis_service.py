from unittest.mock import MagicMock

import pytest

from app.core.config import Settings
from app.core.exceptions import ClaimNotFoundError
from app.services.nlp_analysis_service import NLPAnalysisService
from tests.conftest import SAMPLE_DATA_DIR


def test_missing_claim_raises_not_found():
    settings = Settings(SAMPLE_DATA_DIR=str(SAMPLE_DATA_DIR))
    service = NLPAnalysisService(settings)
    with pytest.raises(ClaimNotFoundError):
        service.analyze_by_claim_id("DOES-NOT-EXIST")


def test_unexpected_pipeline_error_returns_failure_result():
    settings = Settings()
    service = NLPAnalysisService(settings)
    service._pipeline = MagicMock()
    service._pipeline.analyze.side_effect = RuntimeError("unexpected bug")

    from datetime import datetime, timezone
    from decimal import Decimal

    from app.schemas.claim import ClaimInput
    from app.schemas.repair import Repair
    from app.schemas.vehicle import Vehicle

    claim = ClaimInput(
        claim_id="X",
        submission_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
        vehicle=Vehicle(vehicle_id="V", make="A", model="B", model_year=2020),
        customer_complaint="noise",
        technician_diagnosis="noise",
        recommended_repair=Repair(
            repair_category="GEN",
            part_description="n/a",
            recommended_action="inspect",
        ),
        submitted_parts_cost=Decimal("0"),
        submitted_labour_hours=Decimal("0"),
    )

    result = service.analyze_claim(claim)
    assert result.nlp_error and "unexpected bug" in result.nlp_error
    assert result.claim_id == "X"
