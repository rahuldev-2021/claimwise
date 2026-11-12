"""Independent validation for synthetic_v1 repair CSVs."""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

REQUIRED_TRAINING = {
    "vehicle_make",
    "vehicle_model",
    "model_year",
    "repair_category",
    "currency",
    "parts_cost",
    "labour_hours",
    "part",
    "repair_action",
    "repair_complexity",
    "vehicle_category",
}

FORBIDDEN_LEAKAGE = {
    "submitted_parts_cost",
    "submitted_labour_hours",
    "claim_id",
    "total_repair_amount",
    "total_labour_charge",
}

ALLOWED_CURRENCY = {"USD", "CAD"}

VALID_ACTIONS = {"Replacement", "Repair"}
VALID_COMPLEXITY = {"LOW", "MEDIUM", "HIGH"}


def load_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise ValueError(f"No header: {path}")
        headers = [h.strip() for h in reader.fieldnames]
        rows = [{k: (v or "").strip() for k, v in row.items()} for row in reader]
    return headers, rows


def _parse_date(s: str) -> datetime | None:
    try:
        return datetime.strptime(s[:10], "%Y-%m-%d")
    except ValueError:
        return None


def validate_primary_file(path: Path) -> dict:
    report: dict = {"path": str(path), "issues": [], "warnings": []}
    if not path.is_file():
        report["issues"].append("file not found")
        return report

    headers, rows = load_rows(path)
    report["row_count"] = len(rows)

    missing = REQUIRED_TRAINING - set(headers)
    if missing:
        report["issues"].append(f"missing required columns: {sorted(missing)}")

    for col in FORBIDDEN_LEAKAGE:
        if col in headers:
            report["issues"].append(f"leakage column present: {col}")

    ids = [r.get("repair_record_id", "") for r in rows]
    if len(ids) != len(set(ids)):
        report["issues"].append("duplicate repair_record_id values")

    currencies = {r.get("currency", "").upper() for r in rows if r.get("currency")}
    if currencies - ALLOWED_CURRENCY:
        report["issues"].append(f"unsupported currency codes: {currencies - ALLOWED_CURRENCY}")
    if len(currencies) > 1:
        report["issues"].append(f"mixed currencies: {currencies}")

    vehicle_attrs: dict[str, dict[str, str]] = {}
    age_mismatches = 0
    mileage_warnings = 0
    consistency_errors = 0
    non_finite = 0

    for r in rows:
        try:
            pc = float(r.get("parts_cost", ""))
            lh = float(r.get("labour_hours", ""))
        except ValueError:
            report["issues"].append(f"non-numeric financials in {r.get('repair_record_id')}")
            continue
        if not (math.isfinite(pc) and math.isfinite(lh)):
            non_finite += 1
            continue
        if pc <= 0 or lh <= 0:
            report["issues"].append(f"non-positive financials in {r.get('repair_record_id')}")

        action = r.get("repair_action", "")
        if action and action not in VALID_ACTIONS:
            consistency_errors += 1
        cx = r.get("repair_complexity", "")
        if cx and cx not in VALID_COMPLEXITY:
            consistency_errors += 1

        pdate = _parse_date(r.get("price_date", ""))
        try:
            model_year = int(r.get("model_year", ""))
            age_declared = int(r.get("vehicle_age_years", ""))
        except ValueError:
            report["issues"].append(f"invalid year/age in {r.get('repair_record_id')}")
            continue
        if pdate and age_declared != pdate.year - model_year:
            age_mismatches += 1

        try:
            mileage = int(r.get("mileage", ""))
        except ValueError:
            mileage = -1
        if mileage < 500 or mileage > 400_000:
            mileage_warnings += 1
        elif age_declared > 0 and mileage < age_declared * 2000:
            mileage_warnings += 1

        vid = r.get("vehicle_id", "")
        if vid:
            snap = {
                "vehicle_make": r.get("vehicle_make", ""),
                "vehicle_model": r.get("vehicle_model", ""),
                "model_year": r.get("model_year", ""),
                "vehicle_category": r.get("vehicle_category", ""),
            }
            if vid in vehicle_attrs and vehicle_attrs[vid] != snap:
                report["issues"].append(f"vehicle_id {vid} has inconsistent attributes")
            vehicle_attrs[vid] = snap

    if age_mismatches:
        report["issues"].append(f"vehicle_age_years mismatch vs price_date/model_year: {age_mismatches}")
    if consistency_errors:
        report["issues"].append(f"invalid repair_action/complexity values: {consistency_errors}")
    if non_finite:
        report["issues"].append(f"non-finite financial values: {non_finite}")
    if mileage_warnings:
        report["warnings"].append(f"mileage plausibility warnings: {mileage_warnings}")

    if rows:
        cats = Counter(r.get("repair_category", "") for r in rows)
        dominant = cats.most_common(1)[0]
        if dominant[1] / len(rows) > 0.4:
            report["warnings"].append(
                f"category imbalance: {dominant[0]} has {dominant[1]/len(rows):.1%}"
            )
        actions = Counter(r.get("repair_action", "") for r in rows)
        report["repair_action_distribution"] = dict(actions)

    for r in rows:
        if r.get("is_synthetic", "").lower() != "true":
            report["warnings"].append("record missing is_synthetic=true flag")
            break

    sku_counts = Counter(r.get("part_number", "") for r in rows)
    if rows and len(sku_counts) > len(rows) * 0.9:
        report["warnings"].append(
            "part_number cardinality very high; confirm catalog IDs are reused"
        )

    return report


def validate_splits(train: Path, val: Path, test: Path, historical: Path) -> list[str]:
    issues: list[str] = []
    _, train_rows = load_rows(train)
    _, val_rows = load_rows(val)
    _, test_rows = load_rows(test)
    _, hist_rows = load_rows(historical)

    if len(train_rows) + len(val_rows) + len(test_rows) != len(hist_rows):
        issues.append("train+val+test row count does not equal historical_repairs")

    hist_ids = {r["repair_record_id"] for r in hist_rows}
    split_ids = (
        {r["repair_record_id"] for r in train_rows}
        | {r["repair_record_id"] for r in val_rows}
        | {r["repair_record_id"] for r in test_rows}
    )
    if hist_ids != split_ids:
        issues.append("split IDs do not partition historical_repairs exactly")

    train_v = {r["vehicle_id"] for r in train_rows}
    val_v = {r["vehicle_id"] for r in val_rows}
    test_v = {r["vehicle_id"] for r in test_rows}
    if train_v & val_v:
        issues.append("vehicle_id overlap train/validation")
    if train_v & test_v:
        issues.append("vehicle_id overlap train/test")
    if val_v & test_v:
        issues.append("vehicle_id overlap validation/test")
    return issues


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    root = args.dir

    reports = {
        name: validate_primary_file(root / name)
        for name in ("historical_repairs.csv", "train.csv", "validation.csv", "test.csv")
    }
    split_issues = validate_splits(
        root / "train.csv",
        root / "validation.csv",
        root / "test.csv",
        root / "historical_repairs.csv",
    )
    edge_report = validate_primary_file(root / "edge_cases.csv")
    edge_dup = 0
    if edge_report.get("row_count"):
        _, edge_rows = load_rows(root / "edge_cases.csv")
        edge_ids = [r.get("repair_record_id") for r in edge_rows]
        edge_dup = len(edge_ids) - len(set(edge_ids))
        if edge_dup == 0:
            edge_report["warnings"].append("duplicate_id edge case did not produce duplicate IDs")

    all_issues: list[str] = []
    for r in reports.values():
        all_issues.extend(r["issues"])
    all_issues.extend(split_issues)

    payload = {
        "validated_at": datetime.utcnow().isoformat() + "Z",
        "dataset_version": "synthetic_v1.1",
        "files": list(reports.values()),
        "split_issues": split_issues,
        "split_counts": {
            "train": reports["train.csv"]["row_count"],
            "validation": reports["validation.csv"]["row_count"],
            "test": reports["test.csv"]["row_count"],
            "historical": reports["historical_repairs.csv"]["row_count"],
        },
        "edge_cases": edge_report,
        "edge_duplicate_id_count": edge_dup,
        "critical_pass": not all_issues,
        "status": "passed" if not all_issues else "failed",
    }
    (root / "validation_results.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

    summary_path = root / "dataset_summary.json"
    if summary_path.is_file():
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        summary["validation"] = payload
        summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(json.dumps(payload, indent=2))
    return 1 if all_issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
