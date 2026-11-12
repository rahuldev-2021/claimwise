"""CLI entrypoint for labour hours model training."""

import argparse
import json
import sys
from pathlib import Path

from app.modules.financial_validation.training.train_common import train_regressor


def main() -> int:
    parser = argparse.ArgumentParser(description="Train labour hours regressor (Phase 6)")
    parser.add_argument("--data-path", required=True, help="Training dataset CSV path")
    parser.add_argument("--config-dir", default="config/financial")
    parser.add_argument("--registry-dir", default="data/financial_models")
    parser.add_argument("--validation-path", default=None, type=Path)
    parser.add_argument("--test-path", default=None, type=Path)
    parser.add_argument("--model-candidate", default=None)
    parser.add_argument("--no-register", action="store_true", help="Train without writing registry artifacts")
    parser.add_argument(
        "--allow-synthetic-test",
        action="store_true",
        help="Allow tests/fixtures paths (SYNTHETIC_TEST_ONLY)",
    )
    args = parser.parse_args()
    result = train_regressor(
        "labour_hours",
        data_path=Path(args.data_path),
        registry_dir=Path(args.registry_dir),
        config_dir=Path(args.config_dir),
        allow_synthetic_test=args.allow_synthetic_test,
        model_candidate=args.model_candidate,
        validation_path=args.validation_path,
        test_path=args.test_path,
        register=not args.no_register,
    )
    print(json.dumps(result, indent=2), file=sys.stderr)
    print("PROVISIONAL: metrics are not production approval.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
