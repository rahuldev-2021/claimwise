"""Validate readiness when an approved dataset path is provided (FINANCIAL_TRAINING_DATA_PATH)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.core.config import get_settings
from app.modules.financial_validation.config.loader import load_financial_config
from app.modules.financial_validation.data.validation import validate_training_csv
from app.modules.financial_validation.features.consistency import validate_training_inference_consistency


def run_gate(data_path: Path, config_dir: Path) -> dict:
    bundle = load_financial_config(config_dir)
    report = validate_training_csv(data_path, bundle.data_dictionary)
    feature_issues = validate_training_inference_consistency(bundle.feature_mapping)
    report["feature_mapping_issues"] = feature_issues
    report["approved_training_ready"] = not report.get("issues") and not feature_issues
    report["pending_if_not_ready"] = [
        "Update PROVISIONAL YAML to approved data dictionary and rules",
        "Run exploratory_analysis.py",
        "Select evaluation strategy with documented justification",
        "Train parts_cost and labour_hours models separately",
        "Register artifacts and document metrics on approved data only",
    ]
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Approved dataset compatibility gate")
    parser.add_argument("--data-path", default=None)
    parser.add_argument("--config-dir", default="config/financial")
    args = parser.parse_args()
    settings = get_settings()
    path_str = args.data_path or settings.FINANCIAL_TRAINING_DATA_PATH
    if not path_str:
        print(
            json.dumps(
                {
                    "status": "pending",
                    "message": "Set FINANCIAL_TRAINING_DATA_PATH or pass --data-path",
                },
                indent=2,
            )
        )
        return 0
    report = run_gate(Path(path_str), Path(args.config_dir))
    print(json.dumps(report, indent=2))
    return 0 if report.get("approved_training_ready") else 1


if __name__ == "__main__":
    raise SystemExit(main())
