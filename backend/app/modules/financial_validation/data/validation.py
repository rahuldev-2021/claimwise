"""Dataset validation against data dictionary (csv module only)."""

import csv
from collections import Counter
from pathlib import Path
from typing import Any

from app.modules.financial_validation.config.models import DataDictionaryConfig
from app.modules.financial_validation.exceptions import FinancialDataError


def read_csv_headers(path: Path) -> list[str]:
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        row = next(reader, None)
        if not row:
            raise FinancialDataError(f"Empty CSV: {path}")
        return [h.strip() for h in row]


def validate_currency_consistency(rows: list[dict[str, str]], currency_col: str) -> list[str]:
    issues: list[str] = []
    codes = [r.get(currency_col, "").strip().upper() for r in rows if r.get(currency_col)]
    if not codes:
        issues.append("No currency values found")
        return issues
    counts = Counter(codes)
    if len(counts) > 1:
        issues.append(
            f"Mixed currencies in training data: {dict(counts)} — "
            "parts cost training blocked without approved normalization"
        )
    return issues


def validate_training_csv(path: Path, dictionary: DataDictionaryConfig) -> dict[str, Any]:
    """Validate a training CSV; returns a quality report dict."""
    if not path.is_file():
        raise FinancialDataError(f"Training file not found: {path}")

    headers = read_csv_headers(path)
    report: dict[str, Any] = {
        "path": str(path),
        "row_count": 0,
        "issues": [],
        "warnings": [],
        "provisional": True,
    }

    required_fields = [f["name"] for f in dictionary.fields if f.get("required")]
    training_map = {f["name"]: f["name"] for f in dictionary.fields}
    missing_headers = [h for h in required_fields if h not in headers and h in training_map]
    if missing_headers:
        report["issues"].append(f"Missing required columns: {missing_headers}")

    for forbidden in dictionary.leakage_forbidden_columns:
        if forbidden in headers:
            report["issues"].append(f"Forbidden leakage column present: {forbidden}")

    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    report["row_count"] = len(rows)

    currency_col = (dictionary.currency or {}).get("allowed_codes")  # type: ignore[assignment]
    currency_field = "currency"
    if dictionary.currency and dictionary.currency.get("require_single_currency_for_parts_training"):
        report["issues"].extend(validate_currency_consistency(rows, currency_field))

    unique_keys = {r.get("vehicle_make", "") + "|" + r.get("repair_category", "") for r in rows}
    if len(rows) - len(unique_keys) > 0 and len(rows) > 0:
        report["warnings"].append(
            f"Possible duplicate vehicle/repair combinations: {len(rows) - len(unique_keys)}"
        )

    return report
