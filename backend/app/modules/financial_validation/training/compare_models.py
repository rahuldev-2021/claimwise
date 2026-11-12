"""CLI: compare regressor candidates on train/validation (+ optional test) splits."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from app.modules.financial_validation.training.train_common import TaskName, compare_regressor_candidates


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare financial ML candidates (Phase 6B)")
    parser.add_argument("--task", required=True, choices=["parts_cost", "labour_hours"])
    parser.add_argument("--train-path", required=True, type=Path)
    parser.add_argument("--validation-path", required=True, type=Path)
    parser.add_argument("--test-path", type=Path, default=None)
    parser.add_argument("--config-dir", default="config/financial")
    parser.add_argument("--registry-dir", default=None, type=Path)
    parser.add_argument(
        "--allow-synthetic-test",
        action="store_true",
        help="Allow tests/fixtures paths (SYNTHETIC_TEST_ONLY)",
    )
    parser.add_argument(
        "--candidates",
        default=None,
        help="Comma-separated candidate keys (default: config training_defaults.model_candidates)",
    )
    args = parser.parse_args()

    candidates = [c.strip() for c in args.candidates.split(",")] if args.candidates else None
    result = compare_regressor_candidates(
        args.task,  # type: ignore[arg-type]
        train_path=args.train_path,
        validation_path=args.validation_path,
        test_path=args.test_path,
        config_dir=Path(args.config_dir),
        candidates=candidates,
        allow_synthetic_test=args.allow_synthetic_test,
        registry_dir=args.registry_dir,
    )
    print(json.dumps(result, indent=2), file=sys.stderr)
    print("PROVISIONAL: comparison on synthetic data is not production approval.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
