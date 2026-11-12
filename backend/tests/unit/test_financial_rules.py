from decimal import Decimal

from app.modules.financial_validation.config.loader import load_financial_config
from app.modules.financial_validation.rules.financial_rules import apply_financial_rules
from app.schemas.financial_validation import FinancialStatus


def test_unavailable_models_never_within_range():
    rules = load_financial_config("config/financial").rules
    status, lines, _, _, triggered = apply_financial_rules(
        rules=rules,
        currency="USD",
        parts_submitted=Decimal("1000"),
        labour_submitted=Decimal("5"),
        parts_predicted=None,
        labour_predicted=None,
        missing_critical_features=[],
        models_available=False,
    )
    assert status == FinancialStatus.INSUFFICIENT_DATA
    assert status != FinancialStatus.WITHIN_EXPECTED_RANGE
    assert "F_MODEL_UNAVAILABLE" in triggered


def test_outside_band_provisional():
    rules = load_financial_config("config/financial").rules
    status, _, parts_pct, _, triggered = apply_financial_rules(
        rules=rules,
        currency="USD",
        parts_submitted=Decimal("2000"),
        labour_submitted=Decimal("5"),
        parts_predicted=Decimal("1000"),
        labour_predicted=Decimal("5"),
        missing_critical_features=[],
        models_available=True,
    )
    assert parts_pct == Decimal("100")
    assert status == FinancialStatus.OUTSIDE_EXPECTED_RANGE
    assert "F_PARTS_OUTSIDE_BAND_PROVISIONAL" in triggered
