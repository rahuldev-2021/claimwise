from datetime import datetime, timezone
from decimal import Decimal

from app.modules.dealer_communication.brief_builder import build_dealer_communication_brief
from app.schemas.claim import ClaimInput
from app.schemas.dealer_communication import BenchmarkPosition, ClaimResponseVerdict
from app.schemas.financial_validation import FinancialStatus, FinancialValidationResult
from app.schemas.repair import Repair
from app.schemas.technical_validation import TechnicalStatus, TechnicalValidationResult
from app.schemas.vehicle import Vehicle


def _claim() -> ClaimInput:
    return ClaimInput(
        claim_id="CLM-1",
        submission_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
        vehicle=Vehicle(
            vehicle_id="VH-1",
            make="Ford",
            model="F-150",
            model_year=2023,
            engine_type="3.5L",
            mileage=1000,
        ),
        customer_complaint="noise",
        technician_diagnosis="worn pads",
        recommended_repair=Repair(
            repair_category="BRAKING",
            part_number="X",
            part_description="pads",
            recommended_action="replace pads",
        ),
        currency="USD",
        submitted_parts_cost=Decimal("1200"),
        submitted_labour_hours=Decimal("3"),
    )


def _tv(status: TechnicalStatus = TechnicalStatus.SUPPORTED) -> TechnicalValidationResult:
    return TechnicalValidationResult(
        claim_id="CLM-1",
        technical_status=status,
        diagnosis_summary="d",
        repair_assessment="r",
        explanation="ok",
    )


def test_near_typical_suggests_no_extra_price_focus():
    fin = FinancialValidationResult(
        claim_id="CLM-1",
        submitted_parts_cost=Decimal("1000"),
        submitted_labour_hours=Decimal("5"),
        predicted_parts_cost=Decimal("1050"),
        predicted_labour_hours=Decimal("5.2"),
        parts_discrepancy_pct=Decimal("-4.76"),
        labour_discrepancy_pct=Decimal("-3.85"),
        financial_status=FinancialStatus.WITHIN_EXPECTED_RANGE,
        explanation="within",
    )
    brief = build_dealer_communication_brief(_claim(), fin, _tv())
    assert brief.overall_financial_position == BenchmarkPosition.NEAR_TYPICAL
    assert brief.price_discussion_suggested is False
    assert brief.response is not None
    assert brief.response.verdict == ClaimResponseVerdict.IN_LINE
    assert "in line" in brief.response.summary.lower()


def test_above_typical_flags_price_discussion():
    fin = FinancialValidationResult(
        claim_id="CLM-1",
        submitted_parts_cost=Decimal("2000"),
        submitted_labour_hours=Decimal("5"),
        predicted_parts_cost=Decimal("1000"),
        predicted_labour_hours=Decimal("5"),
        parts_discrepancy_pct=Decimal("100"),
        labour_discrepancy_pct=Decimal("0"),
        financial_status=FinancialStatus.OUTSIDE_EXPECTED_RANGE,
        explanation="high parts",
    )
    brief = build_dealer_communication_brief(_claim(), fin, _tv())
    assert brief.overall_financial_position == BenchmarkPosition.ABOVE_TYPICAL
    assert brief.price_discussion_suggested is True
    assert brief.parts is not None
    assert brief.parts.position == BenchmarkPosition.ABOVE_TYPICAL
    assert brief.response is not None
    assert brief.response.verdict == ClaimResponseVerdict.EXPLAIN_COSTS
    assert any("higher" in b.lower() for b in brief.response.because)


def test_missing_financial_still_has_technical_note():
    brief = build_dealer_communication_brief(_claim(), None, _tv())
    assert "supports" in brief.technical_dealer_note.lower()
    assert brief.overall_financial_position == BenchmarkPosition.UNKNOWN
