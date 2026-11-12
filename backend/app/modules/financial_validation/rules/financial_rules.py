"""Config-driven financial business rules (PROVISIONAL thresholds)."""

from decimal import Decimal, InvalidOperation
from typing import Optional

from app.modules.financial_validation.config.models import RulesConfig
from app.schemas.financial_validation import FinancialStatus


def _decimal_pct(submitted: Decimal, predicted: Decimal) -> Optional[Decimal]:
    if predicted <= 0:
        return None
    try:
        return ((submitted - predicted) / predicted) * Decimal("100")
    except (InvalidOperation, ZeroDivisionError):
        return None


def apply_financial_rules(
    *,
    rules: RulesConfig,
    currency: str,
    parts_submitted: Decimal,
    labour_submitted: Decimal,
    parts_predicted: Optional[Decimal],
    labour_predicted: Optional[Decimal],
    missing_critical_features: list[str],
    models_available: bool,
) -> tuple[FinancialStatus, list[str], Optional[Decimal], Optional[Decimal], list[str]]:
    """Return status, explanation lines, discrepancy pcts, triggered rule ids."""
    triggered: list[str] = []
    lines: list[str] = []

    allowed = rules.currency.get("allowed_inference_currencies") or ["USD"]
    if currency.upper() not in [c.upper() for c in allowed]:
        triggered.append("F_CURRENCY_UNSUPPORTED")
        lines.append(f"Currency {currency} is not supported for financial estimation.")
        return FinancialStatus.NEEDS_REVIEW, lines, None, None, triggered

    if missing_critical_features:
        triggered.append("F_MISSING_CRITICAL_FEATURE")
        lines.append(
            "Missing required features for estimation: " + ", ".join(missing_critical_features)
        )
        abstain = rules.abstain.get("missing_critical_features_status", "INSUFFICIENT_DATA")
        return FinancialStatus(abstain), lines, None, None, triggered

    if not models_available or parts_predicted is None or labour_predicted is None:
        triggered.append("F_MODEL_UNAVAILABLE")
        if parts_predicted is None:
            triggered.append("F_PREDICTION_MISSING")
        if labour_predicted is None:
            triggered.append("F_PREDICTION_MISSING")
        lines.append("Financial ML models are unavailable; no prediction was generated.")
        abstain = rules.abstain.get("model_unavailable_status", "INSUFFICIENT_DATA")
        status = FinancialStatus(abstain)
        parts_pct = _decimal_pct(parts_submitted, parts_predicted) if parts_predicted else None
        labour_pct = _decimal_pct(labour_submitted, labour_predicted) if labour_predicted else None
        return status, lines, parts_pct, labour_pct, triggered

    parts_pct = _decimal_pct(parts_submitted, parts_predicted)
    labour_pct = _decimal_pct(labour_submitted, labour_predicted)

    bands = rules.discrepancy_bands
    parts_band = bands.get("parts_cost_pct") or {}
    labour_band = bands.get("labour_hours_pct") or {}

    parts_within = True
    labour_within = True
    if parts_pct is not None:
        lines.append(
            f"Submitted parts cost {parts_submitted}; predicted {parts_predicted} "
            f"(provisional; discrepancy {parts_pct:.2f}%)."
        )
        if parts_pct < Decimal(str(parts_band.get("within_min", -25))) or parts_pct > Decimal(
            str(parts_band.get("within_max", 25))
        ):
            parts_within = False
            triggered.append("F_PARTS_OUTSIDE_BAND_PROVISIONAL")
    else:
        triggered.append("F_PREDICTION_MISSING")
        lines.append("Parts discrepancy could not be calculated (invalid predicted value).")

    if labour_pct is not None:
        lines.append(
            f"Submitted labour hours {labour_submitted}; predicted {labour_predicted} "
            f"(provisional; discrepancy {labour_pct:.2f}%)."
        )
        if labour_pct < Decimal(str(labour_band.get("within_min", -20))) or labour_pct > Decimal(
            str(labour_band.get("within_max", 20))
        ):
            labour_within = False
            triggered.append("F_LABOUR_OUTSIDE_BAND_PROVISIONAL")
    else:
        triggered.append("F_PREDICTION_MISSING")
        lines.append("Labour discrepancy could not be calculated (invalid predicted value).")

    if not parts_within or not labour_within:
        lines.append(
            "Financial values are outside PROVISIONAL expected bands — human review recommended "
            "(not evidence of fraud)."
        )
        return FinancialStatus.OUTSIDE_EXPECTED_RANGE, lines, parts_pct, labour_pct, triggered

    lines.append("Submitted financial values are within PROVISIONAL expected bands.")
    return FinancialStatus.WITHIN_EXPECTED_RANGE, lines, parts_pct, labour_pct, triggered
