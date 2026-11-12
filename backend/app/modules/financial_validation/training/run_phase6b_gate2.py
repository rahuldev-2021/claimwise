"""Phase 6B Gate 2 orchestrator: compare, select, test-once, register."""

from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path

from app.modules.financial_validation.models.regressor_factory import xgboost_available
from app.modules.financial_validation.training.evaluation import SelectionCriteria
from app.modules.financial_validation.training.gate2_reporting import (
    dataset_fingerprint,
    subgroup_metrics_test,
    try_write_plots,
    write_gate2_reports,
)
from app.modules.financial_validation.training.train_common import (
    _create_task_estimator,
    _dataframe_from_csv,
    _evaluate_model,
    _fit_candidate_model,
    _fit_preprocessor_on_train,
    compare_regressor_candidates,
    finalize_selected_winner,
    load_task_split_frames,
)
from app.modules.financial_validation.config.loader import load_financial_config


GATE2_CANDIDATES = [
    "dummy_mean",
    "linear_regression",
    "ridge",
    "random_forest",
    "gradient_boosting",
    "hist_gradient_boosting",
    "xgboost",
]


def _retrain_and_predict_test(task, train_path, val_path, test_path, config_dir, algorithm, work_dir, max_sec):
    bundle = load_financial_config(config_dir)
    splits = load_task_split_frames(
        bundle=bundle,
        train_path=train_path,
        validation_path=val_path,
        test_path=test_path,
        task=task,
    )
    pre, x_tr, x_va, x_te = _fit_preprocessor_on_train(
        splits.feature_cols, splits.x_train, splits.x_val, splits.x_test
    )
    model, _ = _fit_candidate_model(
        task,
        algorithm,
        random_seed=bundle.training_defaults.random_seed,
        x_train_m=x_tr,
        y_train=splits.y_train,
        work_root=work_dir,
        candidate_max_seconds=max_sec,
    )
    if model is None:
        return None, None, None, None
    import numpy as np

    preds = model.predict(x_te)
    test_frame = _dataframe_from_csv(test_path, bundle.feature_mapping.training_columns())
    raw = test_frame if "component" in test_frame.columns else test_frame
    _, rows = __import__(
        "app.modules.financial_validation.data.ingestion", fromlist=["load_csv_records"]
    ).load_csv_records(test_path)
    import pandas as pd

    raw_df = pd.DataFrame(rows)
    target = splits.target_col
    y_test = splits.y_test
    groups = []
    if "repair_category" in raw_df.columns:
        groups.append(("repair_category", raw_df["repair_category"]))
    if "component" in raw_df.columns:
        groups.append(("component", raw_df["component"]))
    if "repair_action" in raw_df.columns:
        groups.append(("repair_action", raw_df["repair_action"]))
    if "vehicle_age_years" in raw_df.columns:
        bins = pd.cut(pd.to_numeric(raw_df["vehicle_age_years"], errors="coerce"), bins=[0, 3, 7, 12, 25])
        groups.append(("vehicle_age_group", bins.astype(str)))
    sub = subgroup_metrics_test(y_true=y_test, y_pred=preds, frame=raw_df, group_columns=groups)
    return preds, y_test, sub, splits


def main() -> int:
    parser = argparse.ArgumentParser(description="CLAIMWISE Phase 6B Gate 2 runner")
    parser.add_argument("--train-path", type=Path, required=True)
    parser.add_argument("--validation-path", type=Path, required=True)
    parser.add_argument("--test-path", type=Path, required=True)
    parser.add_argument("--config-dir", default="config/financial")
    parser.add_argument(
        "--artifacts-dir",
        default="data/financial_models/synthetic_v1/experimental_artifacts",
    )
    parser.add_argument("--results-dir", default="data/financial_models/synthetic_v1/gate2_results")
    parser.add_argument("--docs-dir", default="docs")
    parser.add_argument("--candidate-max-seconds", type=float, default=None)
    parser.add_argument("--min-mae-improvement", type=float, default=0.02)
    args = parser.parse_args()

    max_sec = args.candidate_max_seconds
    if max_sec is None:
        max_sec = float(os.environ.get("FINANCIAL_CANDIDATE_MAX_SECONDS", "3600"))

    prod_registry = Path("data/financial_models/registry.json")
    prod_before = prod_registry.is_file()
    work_dir = Path(args.results_dir) / "_fit_work"
    work_dir.mkdir(parents=True, exist_ok=True)
    criteria = SelectionCriteria(min_relative_mae_improvement_vs_dummy=args.min_mae_improvement)

    metadata = json.loads(
        (args.train_path.parent / "dataset_metadata.json").read_text(encoding="utf-8")
    )
    dataset_meta = {
        **metadata,
        "fingerprint": dataset_fingerprint(args.train_path, args.validation_path, args.test_path),
        "train_rows": sum(1 for _ in open(args.train_path, encoding="utf-8")) - 1,
        "val_rows": sum(1 for _ in open(args.validation_path, encoding="utf-8")) - 1,
        "test_rows": sum(1 for _ in open(args.test_path, encoding="utf-8")) - 1,
    }

    artifacts_dir = Path(args.artifacts_dir)
    diagnostics_dir = artifacts_dir / "diagnostics"

    t0 = time.perf_counter()
    parts_compare = compare_regressor_candidates(
        "parts_cost",
        train_path=args.train_path,
        validation_path=args.validation_path,
        test_path=args.test_path,
        config_dir=Path(args.config_dir),
        candidates=GATE2_CANDIDATES,
        candidate_max_seconds=max_sec,
        selection_criteria=criteria,
        fit_work_dir=work_dir,
    )
    parts_final = finalize_selected_winner(
        "parts_cost",
        compare_result=parts_compare,
        train_path=args.train_path,
        validation_path=args.validation_path,
        test_path=args.test_path,
        config_dir=Path(args.config_dir),
        registry_dir=artifacts_dir,
        diagnostics_dir=diagnostics_dir,
        candidate_max_seconds=max_sec,
        fit_work_dir=work_dir,
    )
    parts_seconds = round(time.perf_counter() - t0, 1)

    subgroup_parts: list = []
    plot_notes: list = []
    if parts_final.get("status") == "ok" and parts_compare.get("selected"):
        out = _retrain_and_predict_test(
            "parts_cost",
            args.train_path,
            args.validation_path,
            args.test_path,
            args.config_dir,
            parts_compare["selected"]["candidate"],
            work_dir,
            max_sec,
        )
        if out[0] is not None:
            preds, y_test, subgroup_parts, _ = out
            plot_notes.extend(
                try_write_plots("parts_cost", y_test, preds, artifacts_dir / "plots" / "parts_cost")
            )

    t1 = time.perf_counter()
    labour_compare = compare_regressor_candidates(
        "labour_hours",
        train_path=args.train_path,
        validation_path=args.validation_path,
        test_path=args.test_path,
        config_dir=Path(args.config_dir),
        candidates=GATE2_CANDIDATES,
        candidate_max_seconds=max_sec,
        selection_criteria=criteria,
        fit_work_dir=work_dir,
    )
    labour_final = finalize_selected_winner(
        "labour_hours",
        compare_result=labour_compare,
        train_path=args.train_path,
        validation_path=args.validation_path,
        test_path=args.test_path,
        config_dir=Path(args.config_dir),
        registry_dir=artifacts_dir,
        diagnostics_dir=diagnostics_dir,
        candidate_max_seconds=max_sec,
        fit_work_dir=work_dir,
    )
    labour_seconds = round(time.perf_counter() - t1, 1)

    subgroup_labour: list = []
    if labour_final.get("status") == "ok" and labour_compare.get("selected"):
        out = _retrain_and_predict_test(
            "labour_hours",
            args.train_path,
            args.validation_path,
            args.test_path,
            args.config_dir,
            labour_compare["selected"]["candidate"],
            work_dir,
            max_sec,
        )
        if out[0] is not None:
            preds, y_test, subgroup_labour, _ = out
            plot_notes.extend(
                try_write_plots("labour_hours", y_test, preds, artifacts_dir / "plots" / "labour_hours")
            )

    execution_meta = {
        "candidate_max_seconds": max_sec,
        "selection_criteria": criteria.__dict__,
        "xgboost_status": "RUN" if xgboost_available() else "NOT RUN — dependency unavailable",
        "artifacts_dir": str(artifacts_dir),
        "production_registry_unchanged": (not prod_registry.is_file()) if not prod_before else prod_registry.is_file(),
        "parts_seconds": parts_seconds,
        "labour_seconds": labour_seconds,
        "plot_notes": plot_notes,
    }

    write_gate2_reports(
        docs_dir=Path(args.docs_dir),
        results_dir=Path(args.results_dir),
        parts_compare=parts_compare,
        labour_compare=labour_compare,
        parts_final=parts_final,
        labour_final=labour_final,
        dataset_meta=dataset_meta,
        execution_meta=execution_meta,
        subgroup_parts=subgroup_parts,
        subgroup_labour=subgroup_labour,
    )

    print(json.dumps({"status": "gate2_complete", "execution": execution_meta}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
