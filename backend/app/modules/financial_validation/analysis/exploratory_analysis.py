"""EDA CLI — writes provisional summary JSON (requires optional ml extra)."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from app.modules.financial_validation.config.loader import load_financial_config
from app.modules.financial_validation.data.ingestion import load_csv_records
from app.modules.financial_validation.exceptions import FinancialDependencyError


def run_eda(data_path: Path, config_dir: Path, output_dir: Path) -> Path:
    try:
        import pandas as pd
    except ImportError as exc:
        raise FinancialDependencyError("Install optional ml extra: pip install -e '.[ml]'") from exc

    bundle = load_financial_config(config_dir)
    _, rows = load_csv_records(data_path)
    frame = pd.DataFrame(rows)

    summary = {
        "provisional": True,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "row_count": len(frame),
        "columns": list(frame.columns),
        "parts_cost_describe": {},
        "labour_hours_describe": {},
        "repair_category_counts": {},
    }

    targets = bundle.data_dictionary.targets or {}
    parts_col = (targets.get("parts_cost") or {}).get("column", "parts_cost")
    labour_col = (targets.get("labour_hours") or {}).get("column", "labour_hours")

    if parts_col in frame.columns:
        summary["parts_cost_describe"] = frame[parts_col].astype(float).describe().to_dict()
    if labour_col in frame.columns:
        summary["labour_hours_describe"] = frame[labour_col].astype(float).describe().to_dict()
    if "repair_category" in frame.columns:
        summary["repair_category_counts"] = frame["repair_category"].value_counts().to_dict()

    output_dir.mkdir(parents=True, exist_ok=True)
    out = output_dir / f"eda_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    out.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Financial training data EDA (provisional)")
    parser.add_argument("--data-path", required=True)
    parser.add_argument("--config-dir", default="config/financial")
    parser.add_argument("--output-dir", default="data/reports/financial/eda")
    args = parser.parse_args()
    path = run_eda(Path(args.data_path), Path(args.config_dir), Path(args.output_dir))
    print(f"Wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
