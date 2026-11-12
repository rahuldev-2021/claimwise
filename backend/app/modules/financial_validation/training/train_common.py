"""Shared offline training for parts cost and labour hours (independent targets)."""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from app.modules.financial_validation.config.loader import load_financial_config
from app.modules.financial_validation.data.ingestion import load_csv_records
from app.modules.financial_validation.data.preprocessing import (
    FinancialFeaturePreprocessor,
    build_feature_frame,
)
from app.modules.financial_validation.data.quality_report import write_quality_report
from app.modules.financial_validation.data.validation import validate_training_csv
from app.modules.financial_validation.exceptions import FinancialDataError, FinancialDependencyError
from app.modules.financial_validation.models.model_registry import (
    ModelRegistry,
    ModelRegistryEntry,
    feature_schema_hash,
)
from app.modules.financial_validation.models.regressor_factory import resolve_runnable_candidates
from app.modules.financial_validation.training.artifact_verify import verify_trained_artifacts
from app.modules.financial_validation.training.candidate_fit_isolated import (
    candidates_requiring_isolated_fit,
    fit_regressor_in_subprocess,
)
from app.modules.financial_validation.training.evaluation import (
    SelectionCriteria,
    classify_selection_outcome,
    regression_metrics,
    resolve_evaluation_strategy,
    select_best_candidate,
)

TaskName = Literal["parts_cost", "labour_hours"]

_SYNTHETIC_FIXTURE_PATTERN = re.compile(r"fixtures[/\\]financial|tiny_training", re.I)
_SYNTHETIC_DATASET_PATTERN = re.compile(r"synthetic_v1|synthetic[/\\]", re.I)


def _require_ml() -> None:
    try:
        import joblib  # noqa: F401
        import pandas  # noqa: F401
        import sklearn  # noqa: F401
    except ImportError as exc:
        raise FinancialDependencyError("Install optional ml extra: pip install -e '.[ml]'") from exc


def _dataframe_from_csv(path: Path, column_map: dict[str, str]):
    import pandas as pd

    _, rows = load_csv_records(path)
    frame = pd.DataFrame(rows)
    csv_to_feature = {csv_col: feature_id for feature_id, csv_col in column_map.items()}
    renamed = frame.rename(columns=csv_to_feature)
    if "price_date" in frame.columns:
        renamed["price_year"] = pd.to_datetime(frame["price_date"], errors="coerce").dt.year
    elif "price_year" in renamed.columns:
        renamed["price_year"] = pd.to_numeric(renamed["price_year"], errors="coerce")
    if "vehicle_age" not in renamed.columns or renamed["vehicle_age"].isna().all():
        if "vehicle_age_years" in frame.columns:
            renamed["vehicle_age"] = pd.to_numeric(frame["vehicle_age_years"], errors="coerce")
        elif "price_date" in frame.columns and "model_year" in renamed.columns:
            price_years = pd.to_datetime(frame["price_date"], errors="coerce").dt.year
            renamed["vehicle_age"] = price_years - pd.to_numeric(renamed["model_year"], errors="coerce")
    for col in ("model_year", "mileage", "vehicle_age"):
        if col in renamed.columns:
            renamed[col] = pd.to_numeric(renamed[col], errors="coerce")
    return renamed


def _feature_columns(bundle) -> list[str]:
    train_features = set(bundle.feature_mapping.training_columns().keys())
    return [c for c in bundle.feature_mapping.feature_ids if c in train_features]


def _target_column(task: TaskName, bundle) -> str:
    targets = bundle.data_dictionary.targets or {}
    spec = targets.get(task) or {}
    col = spec.get("column")
    if not col:
        raise FinancialDataError(f"No target column configured for task {task}")
    return col


def _assert_training_path_allowed(data_path: Path, allow_synthetic_test: bool) -> None:
    if _SYNTHETIC_FIXTURE_PATTERN.search(str(data_path)) and not allow_synthetic_test:
        raise FinancialDataError(
            "Refusing to train on synthetic fixture path without --allow-synthetic-test"
        )


def _dataset_metadata_flags(paths: list[Path]) -> tuple[bool, str, str]:
    """Return synthetic_data flag, status (stub|trained), lifecycle."""
    if any(_SYNTHETIC_DATASET_PATTERN.search(str(p)) for p in paths):
        return True, "trained", "experimental"
    if any(_SYNTHETIC_FIXTURE_PATTERN.search(str(p)) for p in paths):
        return True, "trained", "validation"
    return False, "trained", "production"


@dataclass
class TaskSplitFrames:
    feature_cols: list[str]
    target_col: str
    x_train: Any
    y_train: Any
    x_val: Any | None
    y_val: Any | None
    x_test: Any | None
    y_test: Any | None


def load_task_split_frames(
    *,
    bundle,
    train_path: Path,
    validation_path: Path | None,
    test_path: Path | None,
    task: TaskName,
) -> TaskSplitFrames:
    column_map = bundle.feature_mapping.training_columns()
    feature_cols = _feature_columns(bundle)
    target_col = _target_column(task, bundle)

    train_frame = _dataframe_from_csv(train_path, column_map)
    if target_col not in train_frame.columns:
        raise FinancialDataError(f"Target column {target_col} missing from training data")

    x_train = build_feature_frame(train_frame.to_dict(orient="records"), feature_cols)
    y_train = train_frame[target_col].astype(float)

    x_val = y_val = None
    if validation_path is not None:
        val_frame = _dataframe_from_csv(validation_path, column_map)
        if target_col not in val_frame.columns:
            raise FinancialDataError(f"Target column {target_col} missing from validation data")
        x_val = build_feature_frame(val_frame.to_dict(orient="records"), feature_cols)
        y_val = val_frame[target_col].astype(float)

    x_test = y_test = None
    if test_path is not None:
        test_frame = _dataframe_from_csv(test_path, column_map)
        if target_col not in test_frame.columns:
            raise FinancialDataError(f"Target column {target_col} missing from test data")
        x_test = build_feature_frame(test_frame.to_dict(orient="records"), feature_cols)
        y_test = test_frame[target_col].astype(float)

    return TaskSplitFrames(
        feature_cols=feature_cols,
        target_col=target_col,
        x_train=x_train,
        y_train=y_train,
        x_val=x_val,
        y_val=y_val,
        x_test=x_test,
        y_test=y_test,
    )


def _fit_preprocessor_on_train(
    feature_cols: list[str],
    x_train,
    x_val,
    x_test,
) -> tuple[FinancialFeaturePreprocessor, Any, Any | None, Any | None]:
    preprocessor = FinancialFeaturePreprocessor(feature_cols)
    x_train_m = preprocessor.fit(x_train).transform(x_train)
    x_val_m = preprocessor.transform(x_val) if x_val is not None else None
    x_test_m = preprocessor.transform(x_test) if x_test is not None else None
    return preprocessor, x_train_m, x_val_m, x_test_m


def _create_task_estimator(task: TaskName, candidate: str, random_seed: int):
    if task == "parts_cost":
        from app.modules.financial_validation.models.parts_cost_model import create_estimator

        return create_estimator(candidate, random_seed)
    from app.modules.financial_validation.models.labour_hours_model import create_estimator

    return create_estimator(candidate, random_seed)


def _evaluate_model(model, matrices: dict[str, Any | None], targets: dict[str, Any | None]) -> dict[str, dict[str, float]]:
    out: dict[str, dict[str, float]] = {}
    for split in ("train", "validation", "test"):
        x_m = matrices.get(split)
        y = targets.get(split)
        if x_m is None or y is None:
            continue
        preds = model.predict(x_m)
        out[split] = regression_metrics(y, preds)
    return out


def _fit_candidate_model(
    task: TaskName,
    candidate: str,
    *,
    random_seed: int,
    x_train_m,
    y_train,
    work_root: Path | None,
    candidate_max_seconds: float | None,
):
    if candidate in candidates_requiring_isolated_fit() and work_root is not None:
        iso_dir = work_root / f"fit_{candidate}"
        return fit_regressor_in_subprocess(
            candidate,
            random_seed=random_seed,
            x_matrix=x_train_m,
            y_vector=y_train,
            work_dir=iso_dir,
            timeout_seconds=candidate_max_seconds,
        )
    model = _create_task_estimator(task, candidate, random_seed)
    model.fit(x_train_m, y_train)
    return model, {"status": "ok", "isolated_fit": False}


def compare_regressor_candidates(
    task: TaskName,
    *,
    train_path: Path,
    validation_path: Path,
    test_path: Path | None = None,
    config_dir: Path,
    candidates: list[str] | None = None,
    allow_synthetic_test: bool = False,
    register_winner: bool = False,
    registry_dir: Path | None = None,
    candidate_max_seconds: float | None = None,
    selection_criteria: SelectionCriteria | None = None,
    fit_work_dir: Path | None = None,
) -> dict[str, Any]:
    """Train each candidate on train; compare on validation only (test held out)."""
    _require_ml()

    _assert_training_path_allowed(train_path, allow_synthetic_test)
    bundle = load_financial_config(config_dir)
    quality = validate_training_csv(train_path, bundle.data_dictionary)
    if quality.get("issues"):
        raise FinancialDataError(f"Dataset validation failed: {quality['issues']}")

    if register_winner:
        raise FinancialDataError(
            "register_winner is deprecated; use finalize_selected_winner after test evaluation"
        )

    if candidates is None:
        candidates = (bundle.training_defaults.model_candidates or {}).get(task) or ["dummy_mean"]
    runnable, skipped = resolve_runnable_candidates(candidates)

    splits = load_task_split_frames(
        bundle=bundle,
        train_path=train_path,
        validation_path=validation_path,
        test_path=None,
        task=task,
    )
    if splits.x_val is None or splits.y_val is None:
        raise FinancialDataError("validation_path is required for candidate comparison")

    train_frame_cols = set(_dataframe_from_csv(train_path, bundle.feature_mapping.training_columns()).columns)
    strategy, strategy_note = resolve_evaluation_strategy(
        bundle.training_defaults.evaluation,
        train_frame_cols,
    )

    comparison: list[dict[str, Any]] = []
    for skip in skipped:
        comparison.append({**skip, "metrics": {}})

    for candidate in runnable:
        row: dict[str, Any] = {"candidate": candidate, "status": "RUN"}
        t0 = time.perf_counter()
        try:
            preprocessor, x_train_m, x_val_m, _x_ignored = _fit_preprocessor_on_train(
                splits.feature_cols,
                splits.x_train,
                splits.x_val,
                None,
            )
            model, fit_meta = _fit_candidate_model(
                task,
                candidate,
                random_seed=bundle.training_defaults.random_seed,
                x_train_m=x_train_m,
                y_train=splits.y_train,
                work_root=fit_work_dir,
                candidate_max_seconds=candidate_max_seconds,
            )
            row.update({k: v for k, v in fit_meta.items() if k != "status"})
            if fit_meta.get("status") == "NOT COMPLETED":
                row["status"] = "NOT COMPLETED"
                row["reason"] = fit_meta.get("reason", "timeout")
                row["metrics"] = {}
                row["train_seconds"] = round(time.perf_counter() - t0, 3)
                comparison.append(row)
                continue
            if model is None:
                row["status"] = "FAIL"
                row["error"] = fit_meta.get("reason", "fit failed")
                row["metrics"] = {}
                comparison.append(row)
                continue

            metrics = _evaluate_model(
                model,
                {"train": x_train_m, "validation": x_val_m},
                {"train": splits.y_train, "validation": splits.y_val},
            )
            row["metrics"] = metrics
            row["train_seconds"] = round(time.perf_counter() - t0, 3)
            comparison.append(row)
        except Exception as exc:
            row["status"] = "FAIL"
            row["error"] = str(exc)
            row["metrics"] = {}
            comparison.append(row)

    selected = select_best_candidate(comparison, split="validation")
    outcome, outcome_details = classify_selection_outcome(
        comparison, selected, split="validation", criteria=selection_criteria
    )
    return {
        "task": task,
        "evaluation_strategy": strategy,
        "evaluation_note": strategy_note,
        "candidates": comparison,
        "selected": selected,
        "selection_outcome": outcome,
        "selection_details": outcome_details,
        "synthetic_data_evaluation": any(
            _SYNTHETIC_DATASET_PATTERN.search(str(p)) for p in (train_path, validation_path, test_path or Path())
        ),
        "test_path_reserved": str(test_path) if test_path else None,
    }


def finalize_selected_winner(
    task: TaskName,
    *,
    compare_result: dict[str, Any],
    train_path: Path,
    validation_path: Path,
    test_path: Path,
    config_dir: Path,
    registry_dir: Path | None,
    diagnostics_dir: Path | None,
    candidate_max_seconds: float | None = None,
    fit_work_dir: Path | None = None,
) -> dict[str, Any]:
    """Retrain winner, evaluate on test once, verify artifacts, register if allowed."""
    _require_ml()
    import joblib
    import sklearn

    bundle = load_financial_config(config_dir)
    selected = compare_result.get("selected")
    outcome = compare_result.get("selection_outcome")
    result: dict[str, Any] = {
        "task": task,
        "selection_outcome": outcome,
        "registered": False,
    }
    if not selected or outcome == "NO ACCEPTABLE CANDIDATE":
        result["status"] = "skipped"
        result["reason"] = "no acceptable candidate for registration"
        return result

    algo = selected["candidate"]
    splits = load_task_split_frames(
        bundle=bundle,
        train_path=train_path,
        validation_path=validation_path,
        test_path=test_path,
        task=task,
    )

    preprocessor, x_train_m, x_val_m, x_test_m = _fit_preprocessor_on_train(
        splits.feature_cols,
        splits.x_train,
        splits.x_val,
        splits.x_test,
    )
    model, fit_meta = _fit_candidate_model(
        task,
        algo,
        random_seed=bundle.training_defaults.random_seed,
        x_train_m=x_train_m,
        y_train=splits.y_train,
        work_root=fit_work_dir,
        candidate_max_seconds=candidate_max_seconds,
    )
    if model is None:
        result["status"] = "failed"
        result["reason"] = fit_meta.get("reason", "winner refit failed")
        return result

    t_pred = time.perf_counter()
    metrics = _evaluate_model(
        model,
        {"train": x_train_m, "validation": x_val_m, "test": x_test_m},
        {"train": splits.y_train, "validation": splits.y_val, "test": splits.y_test},
    )
    result["validation_predict_seconds"] = round(time.perf_counter() - t_pred, 4)
    metrics["selection_outcome"] = outcome
    metrics["selection_details"] = compare_result.get("selection_details")
    result["metrics"] = metrics

    train_rows = splits.x_train.to_dict(orient="records")
    sample_row = train_rows[0] if train_rows else {}
    version = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    task_dir = None
    if registry_dir is not None and outcome in ("SELECTED", "EXPERIMENTAL — WEAK PERFORMANCE"):
        task_dir = registry_dir / task / version
        task_dir.mkdir(parents=True, exist_ok=True)
        model_rel = f"{task}/{version}/model.joblib"
        pre_rel = f"{task}/{version}/preprocessor.joblib"
        joblib.dump(model, registry_dir / model_rel)
        preprocessor.save(registry_dir / pre_rel)
        try:
            verify_trained_artifacts(
                registry_root=registry_dir,
                model_rel=model_rel,
                preprocessor_rel=pre_rel,
                feature_ids=bundle.feature_mapping.feature_ids,
                feature_cols=splits.feature_cols,
                sample_feature_row=sample_row,
            )
        except Exception as exc:
            if task_dir and task_dir.is_dir():
                import shutil

                shutil.rmtree(task_dir, ignore_errors=True)
            result["status"] = "failed"
            result["reason"] = f"artifact verification failed: {exc}"
            return result

        strategy_note = compare_result.get("evaluation_note", "holdout")
        reg_info = _register_trained_model(
            task=task,
            bundle=bundle,
            registry_dir=registry_dir,
            model=model,
            preprocessor=preprocessor,
            algorithm=algo,
            metrics=metrics,
            data_paths=[train_path, validation_path, test_path],
            strategy_note=f"holdout_validation: {strategy_note}",
            sklearn_version=sklearn.__version__,
            version=version,
            model_rel=model_rel,
            pre_rel=pre_rel,
            write_artifacts=False,
        )
        result["registration"] = reg_info
        result["registered"] = True
        manifest = {
            "task": task,
            "algorithm": algo,
            "version": version,
            "selection_outcome": outcome,
            "dataset_paths": [str(train_path), str(validation_path), str(test_path)],
            "metrics": metrics,
            "sklearn_version": sklearn.__version__,
        }
        (task_dir / "manifest.json").write_text(
            json.dumps(manifest, indent=2),
            encoding="utf-8",
        )
        result["manifest"] = str(task_dir / "manifest.json")
    elif diagnostics_dir is not None:
        diag_dir = diagnostics_dir / task / version
        diag_dir.mkdir(parents=True, exist_ok=True)
        joblib.dump(model, diag_dir / "model.joblib")
        preprocessor.save(diag_dir / "preprocessor.joblib")
        result["diagnostics_dir"] = str(diag_dir)

    result["status"] = "ok"
    result["algorithm"] = algo
    return result


def _register_trained_model(
    *,
    task: TaskName,
    bundle,
    registry_dir: Path,
    model,
    preprocessor: FinancialFeaturePreprocessor,
    algorithm: str,
    metrics: dict[str, Any],
    data_paths: list[Path],
    strategy_note: str,
    sklearn_version: str,
    version: str | None = None,
    model_rel: str | None = None,
    pre_rel: str | None = None,
    write_artifacts: bool = True,
) -> dict[str, Any]:
    import joblib

    synthetic_data, status, lifecycle = _dataset_metadata_flags(data_paths)
    production_ready = lifecycle == "production" and not synthetic_data

    version = version or datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    task_dir = registry_dir / task / version
    task_dir.mkdir(parents=True, exist_ok=True)
    model_rel = model_rel or f"{task}/{version}/model.joblib"
    pre_rel = pre_rel or f"{task}/{version}/preprocessor.joblib"
    if write_artifacts:
        joblib.dump(model, registry_dir / model_rel)
        preprocessor.save(registry_dir / pre_rel)

    schema_hash = feature_schema_hash(bundle.feature_mapping.feature_ids)
    entry = ModelRegistryEntry(
        task=task,
        version=version,
        model_path=model_rel,
        preprocessor_path=pre_rel,
        feature_schema_hash=schema_hash,
        sklearn_version=sklearn_version,
        training_data_version=" | ".join(str(p) for p in data_paths),
        evaluation_strategy=strategy_note,
        metrics={**metrics, "provisional": True, "synthetic_data_evaluation": synthetic_data},
        status=status,  # type: ignore[arg-type]
        lifecycle=lifecycle,  # type: ignore[arg-type]
        synthetic_data=synthetic_data,
        production_ready=production_ready,
        algorithm=algorithm,
    )

    registry = ModelRegistry(registry_dir)
    entries = registry.load()
    entries = [e for e in entries if not (e.task == task and e.version == version)] + [entry]
    registry.save(entries)

    return {
        "task": task,
        "version": version,
        "registry_dir": str(registry_dir),
        "status": status,
        "lifecycle": lifecycle,
        "synthetic_data": synthetic_data,
        "production_ready": production_ready,
        "algorithm": algorithm,
    }


def train_regressor(
    task: TaskName,
    *,
    data_path: Path,
    registry_dir: Path,
    config_dir: Path,
    allow_synthetic_test: bool = False,
    model_candidate: str | None = None,
    validation_path: Path | None = None,
    test_path: Path | None = None,
    register: bool = True,
) -> dict[str, Any]:
    """Train a single task model; optional validation/test metrics; register artifacts when enabled."""
    _require_ml()
    import sklearn

    _assert_training_path_allowed(data_path, allow_synthetic_test)

    bundle = load_financial_config(config_dir)
    quality = validate_training_csv(data_path, bundle.data_dictionary)
    if quality.get("issues"):
        raise FinancialDataError(f"Dataset validation failed: {quality['issues']}")

    report_path = write_quality_report(quality, Path("data/reports/financial"))

    splits = load_task_split_frames(
        bundle=bundle,
        train_path=data_path,
        validation_path=validation_path,
        test_path=test_path,
        task=task,
    )

    available_cols = set(_dataframe_from_csv(data_path, bundle.feature_mapping.training_columns()).columns)
    strategy, strategy_note = resolve_evaluation_strategy(
        bundle.training_defaults.evaluation,
        available_cols,
    )

    candidate = model_candidate
    if not candidate:
        candidates = (bundle.training_defaults.model_candidates or {}).get(task) or ["dummy_mean"]
        candidate = candidates[0]

    preprocessor, x_train_m, x_val_m, x_test_m = _fit_preprocessor_on_train(
        splits.feature_cols,
        splits.x_train,
        splits.x_val,
        splits.x_test,
    )
    model = _create_task_estimator(task, candidate, bundle.training_defaults.random_seed)
    model.fit(x_train_m, splits.y_train)

    metrics = _evaluate_model(
        model,
        {"train": x_train_m, "validation": x_val_m, "test": x_test_m},
        {"train": splits.y_train, "validation": splits.y_val, "test": splits.y_test},
    )
    if "train" in metrics:
        metrics["in_sample_mae"] = metrics["train"]["mae"]

    reg_info: dict[str, Any] | None = None
    if register:
        reg_info = _register_trained_model(
            task=task,
            bundle=bundle,
            registry_dir=registry_dir,
            model=model,
            preprocessor=preprocessor,
            algorithm=candidate,
            metrics=metrics,
            data_paths=[data_path]
            + ([validation_path] if validation_path else [])
            + ([test_path] if test_path else []),
            strategy_note=f"{strategy}: {strategy_note}",
            sklearn_version=sklearn.__version__,
        )

    synthetic_data, status, lifecycle = _dataset_metadata_flags(
        [data_path] + ([validation_path] if validation_path else []) + ([test_path] if test_path else [])
    )

    return {
        "task": task,
        "version": reg_info["version"] if reg_info else None,
        "registry_dir": str(registry_dir),
        "quality_report": str(report_path),
        "evaluation_strategy": strategy,
        "evaluation_note": strategy_note,
        "model_candidate": candidate,
        "metrics": metrics,
        "provisional": True,
        "registered": register,
        "lifecycle": lifecycle,
        "synthetic_data": synthetic_data,
        "status": status,
    }
