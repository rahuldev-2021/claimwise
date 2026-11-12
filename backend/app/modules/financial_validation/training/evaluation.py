"""Model evaluation helpers — metrics, split strategy, candidate selection."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

import numpy as np

SelectionOutcome = Literal[
    "SELECTED",
    "EXPERIMENTAL — WEAK PERFORMANCE",
    "NO ACCEPTABLE CANDIDATE",
]


@dataclass
class SelectionCriteria:
    """Validation-only selection rules (configurable for Gate 2)."""

    min_relative_mae_improvement_vs_dummy: float = 0.02
    weak_r2_threshold: float = 0.0
    rationale: str = (
        "Candidate must improve validation MAE by at least "
        "min_relative_mae_improvement_vs_dummy (default 2%) versus dummy_mean; "
        "validation R² at or below weak_r2_threshold yields weak performance."
    )

SplitStrategy = Literal["group_kfold", "time_holdout", "kfold"]


def resolve_evaluation_strategy(
    config: dict[str, Any],
    available_columns: set[str],
) -> tuple[SplitStrategy, str]:
    """Pick CV strategy; do not blindly use kfold when group/time metadata exists."""
    requested = (config.get("strategy") or "auto").lower()
    group_cols = config.get("group_columns") or []
    time_col = config.get("time_column")

    has_group = all(c in available_columns for c in group_cols)
    has_time = time_col in available_columns if time_col else False

    if requested == "kfold" and (has_group or has_time):
        raise ValueError(
            "Refusing plain kfold: group or temporal columns are present; "
            "select group_kfold or time_holdout after dataset inspection"
        )

    if requested in ("group_kfold",) or (requested == "auto" and has_group):
        return "group_kfold", (
            f"group_kfold on {group_cols} (provisional until approved dataset EDA confirms)"
        )

    if requested in ("time_holdout",) or (requested == "auto" and has_time):
        return "time_holdout", f"time holdout using {time_col} (provisional)"

    if requested == "auto" and not has_group and not has_time:
        raise ValueError(
            "Cannot select split strategy automatically: inspect approved dataset before training"
        )

    return "kfold", "kfold only when explicitly configured and no group/time columns present"


def regression_metrics(y_true: Any, y_pred: Any) -> dict[str, float]:
    """MAE, RMSE, R², and median absolute error."""
    y_t = np.asarray(y_true, dtype=float)
    y_p = np.asarray(y_pred, dtype=float)
    err = y_p - y_t
    mae = float(np.mean(np.abs(err)))
    rmse = float(np.sqrt(np.mean(err**2)))
    medae = float(np.median(np.abs(err)))
    ss_res = float(np.sum(err**2))
    ss_tot = float(np.sum((y_t - np.mean(y_t)) ** 2))
    r2 = float(1.0 - ss_res / ss_tot) if ss_tot > 0 else float("nan")
    return {
        "mae": mae,
        "rmse": rmse,
        "r2": r2,
        "median_absolute_error": medae,
    }


def classify_selection_outcome(
    results: list[dict[str, Any]],
    selected: dict[str, Any] | None,
    *,
    split: str = "validation",
    criteria: SelectionCriteria | None = None,
) -> tuple[SelectionOutcome, dict[str, Any]]:
    crit = criteria or SelectionCriteria()
    details: dict[str, Any] = {
        "criteria": {
            "min_relative_mae_improvement_vs_dummy": crit.min_relative_mae_improvement_vs_dummy,
            "weak_r2_threshold": crit.weak_r2_threshold,
            "rationale": crit.rationale,
        }
    }
    runnable = [r for r in results if r.get("status") == "RUN" and (r.get("metrics") or {}).get(split)]
    if not selected or not runnable:
        details["reason"] = "no successful candidate on validation split"
        return "NO ACCEPTABLE CANDIDATE", details

    dummy = next((r for r in runnable if r.get("candidate") == "dummy_mean"), None)
    sel_metrics = (selected.get("metrics") or {}).get(split) or {}
    sel_mae = float(sel_metrics.get("mae", float("inf")))
    sel_r2 = float(sel_metrics.get("r2", float("-inf")))

    details["selected_candidate"] = selected.get("candidate")
    details["validation_mae"] = sel_mae
    details["validation_r2"] = sel_r2

    if dummy:
        d_metrics = (dummy.get("metrics") or {}).get(split) or {}
        d_mae = float(d_metrics.get("mae", float("inf")))
        details["dummy_validation_mae"] = d_mae
        rel_improvement = (d_mae - sel_mae) / d_mae if d_mae > 0 else (0.0 if sel_mae >= d_mae else 1.0)
        details["relative_mae_improvement_vs_dummy"] = rel_improvement
        if sel_mae >= d_mae or rel_improvement < crit.min_relative_mae_improvement_vs_dummy:
            details["reason"] = (
                "insufficient validation MAE improvement versus dummy_mean "
                f"(required >= {crit.min_relative_mae_improvement_vs_dummy:.0%})"
            )
            return "NO ACCEPTABLE CANDIDATE", details

    if np.isnan(sel_r2) or sel_r2 <= crit.weak_r2_threshold:
        details["reason"] = f"validation R² at or below weak threshold ({crit.weak_r2_threshold})"
        return "EXPERIMENTAL — WEAK PERFORMANCE", details

    details["reason"] = "meets validation improvement and R² criteria"
    return "SELECTED", details


def select_best_candidate(
    results: list[dict[str, Any]],
    *,
    split: str = "validation",
) -> dict[str, Any] | None:
    """Pick best candidate by validation MAE, then RMSE, then R² (independent per target)."""
    scored: list[tuple[tuple[float, float, float], dict[str, Any]]] = []
    for row in results:
        if row.get("status") != "RUN":
            continue
        metrics = (row.get("metrics") or {}).get(split)
        if not metrics:
            continue
        mae = metrics.get("mae", float("inf"))
        rmse = metrics.get("rmse", float("inf"))
        r2 = metrics.get("r2", float("-inf"))
        if np.isnan(r2):
            r2 = float("-inf")
        scored.append(((mae, rmse, -r2), row))
    if not scored:
        return None
    scored.sort(key=lambda item: item[0])
    return scored[0][1]
