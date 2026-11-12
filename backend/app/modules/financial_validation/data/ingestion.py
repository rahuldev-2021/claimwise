"""Load tabular training data (CSV) without requiring pandas."""

import csv
from pathlib import Path

from app.modules.financial_validation.exceptions import FinancialDataError


def load_csv_records(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    if not path.is_file():
        raise FinancialDataError(f"Dataset not found: {path}")
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise FinancialDataError(f"No headers in CSV: {path}")
        headers = [h.strip() for h in reader.fieldnames]
        rows = [{k: (v or "").strip() for k, v in row.items()} for row in reader]
    return headers, rows
