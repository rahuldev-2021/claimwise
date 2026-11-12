"""Gate 2 markdown/JSON reporting and descriptive subgroup analysis (test only)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.modules.financial_validation.training.evaluation import regression_metrics

SYNTHETIC_BANNER = "**SYNTHETIC DATA — EXPERIMENTAL EVALUATION**"
MIN_SUBGROUP_N = 30


def dataset_fingerprint(train: Path, val: Path, test: Path) -> str:
    import hashlib

    h = hashlib.sha256()
    for p in (train, val, test):
        h.update(p.read_bytes())
    return h.hexdigest()[:16]


def subgroup_metrics_test(
    *,
    y_true,
    y_pred,
    frame,
    group_columns: list[tuple[str, str]],
    min_n: int = MIN_SUBGROUP_N,
) -> list[dict[str, Any]]:
    """Descriptive test-set subgroup metrics only (not for selection)."""
    import numpy as np
    import pandas as pd

    base = pd.DataFrame({"y_true": np.asarray(y_true, dtype=float), "y_pred": np.asarray(y_pred, dtype=float)})
    for col_name, series in group_columns:
        base[col_name] = series.reset_index(drop=True)
    rows: list[dict[str, Any]] = []
    for col_name, _ in group_columns:
        for key, grp in base.groupby(col_name, dropna=False):
            if len(grp) < min_n:
                rows.append({"dimension": col_name, "group": str(key), "n": len(grp), "status": "INSUFFICIENT_N"})
                continue
            m = regression_metrics(grp["y_true"], grp["y_pred"])
            rows.append({"dimension": col_name, "group": str(key), "n": len(grp), "status": "OK", **m})
    return rows


def try_write_plots(task: str, y_true, y_pred, out_dir: Path) -> list[str]:
    notes: list[str] = []
    try:
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError:
        return ["matplotlib not installed — plots skipped"]

    out_dir.mkdir(parents=True, exist_ok=True)
    y_t = np.asarray(y_true, dtype=float)
    y_p = np.asarray(y_pred, dtype=float)
    err = y_p - y_t

    plt.figure(figsize=(6, 6))
    plt.scatter(y_t, y_p, alpha=0.3, s=8)
    mn, mx = float(min(y_t.min(), y_p.min())), float(max(y_t.max(), y_p.max()))
    plt.plot([mn, mx], [mn, mx], "r--", lw=1)
    plt.xlabel("Actual")
    plt.ylabel("Predicted")
    plt.title(f"{task} actual vs predicted (test)")
    p1 = out_dir / f"{task}_actual_vs_predicted.png"
    plt.savefig(p1, dpi=120, bbox_inches="tight")
    plt.close()

    plt.figure(figsize=(6, 4))
    plt.hist(err, bins=50, alpha=0.8)
    plt.title(f"{task} residuals (test)")
    p2 = out_dir / f"{task}_residuals.png"
    plt.savefig(p2, dpi=120, bbox_inches="tight")
    plt.close()

    plt.figure(figsize=(6, 4))
    plt.hist(np.abs(err), bins=50, alpha=0.8)
    plt.title(f"{task} absolute error (test)")
    p3 = out_dir / f"{task}_absolute_error.png"
    plt.savefig(p3, dpi=120, bbox_inches="tight")
    plt.close()
    return [str(p1), str(p2), str(p3)]


def comparison_table_md(task: str, compare: dict[str, Any], unit: str) -> str:
    lines = [
        SYNTHETIC_BANNER,
        "",
        f"# {task} — candidate comparison (validation)",
        "",
        f"| Algorithm | Status | Val MAE ({unit}) | Val RMSE | Val R² | Val MedAE | Train (s) |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in compare.get("candidates") or []:
        m = (row.get("metrics") or {}).get("validation") or {}
        lines.append(
            f"| {row.get('candidate')} | {row.get('status')} | "
            f"{m.get('mae', '')} | {m.get('rmse', '')} | {m.get('r2', '')} | "
            f"{m.get('median_absolute_error', '')} | {row.get('train_seconds', '')} |"
        )
    lines.append("")
    sel = compare.get("selected") or {}
    lines.append(f"**Validation winner (MAE tie-break):** `{sel.get('candidate', 'none')}`")
    lines.append(f"**Selection outcome:** `{compare.get('selection_outcome')}`")
    lines.append(f"**Rationale:** {json.dumps(compare.get('selection_details'), indent=2)}")
    return "\n".join(lines)


def write_gate2_reports(
    *,
    docs_dir: Path,
    results_dir: Path,
    parts_compare: dict[str, Any],
    labour_compare: dict[str, Any],
    parts_final: dict[str, Any],
    labour_final: dict[str, Any],
    dataset_meta: dict[str, Any],
    execution_meta: dict[str, Any],
    subgroup_parts: list[dict[str, Any]],
    subgroup_labour: list[dict[str, Any]],
) -> list[Path]:
    docs_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    (results_dir / "parts_cost_comparison.json").write_text(json.dumps(parts_compare, indent=2), encoding="utf-8")
    (results_dir / "labour_hours_comparison.json").write_text(json.dumps(labour_compare, indent=2), encoding="utf-8")
    summary = {
        "dataset": dataset_meta,
        "execution": execution_meta,
        "parts_cost": {"compare": parts_compare, "finalize": parts_final},
        "labour_hours": {"compare": labour_compare, "finalize": labour_final},
        "subgroup_parts": subgroup_parts,
        "subgroup_labour": subgroup_labour,
    }
    (results_dir / "gate2_summary.json").write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")

    paths = {
        "phase6_parts_cost_model_comparison.md": comparison_table_md(
            "parts_cost", parts_compare, "USD"
        ),
        "phase6_labour_hours_model_comparison.md": comparison_table_md(
            "labour_hours", labour_compare, "hours"
        ),
        "phase6_model_selection_report.md": _selection_report(parts_compare, labour_compare),
        "phase6_final_evaluation_report.md": _final_eval_report(parts_final, labour_final),
        "phase6_training_execution_report.md": _execution_report(dataset_meta, execution_meta),
        "phase6_subgroup_evaluation_report.md": _subgroup_report(subgroup_parts, subgroup_labour),
    }
    for name, body in paths.items():
        p = docs_dir / name
        p.write_text(body, encoding="utf-8")
        written.append(p)
    return written


def _selection_report(parts: dict, labour: dict) -> str:
    return "\n".join(
        [
            SYNTHETIC_BANNER,
            "",
            "# Model selection (validation only)",
            "",
            "## parts_cost",
            f"- Outcome: **{parts.get('selection_outcome')}**",
            f"- Selected algorithm (validation MAE): `{((parts.get('selected') or {}).get('candidate'))}`",
            f"- Details: ```json\n{json.dumps(parts.get('selection_details'), indent=2)}\n```",
            "",
            "## labour_hours",
            f"- Outcome: **{labour.get('selection_outcome')}**",
            f"- Selected algorithm: `{((labour.get('selected') or {}).get('candidate'))}`",
            f"- Details: ```json\n{json.dumps(labour.get('selection_details'), indent=2)}\n```",
        ]
    )


def _final_eval_report(parts_f: dict, labour_f: dict) -> str:
    def block(task: str, fin: dict) -> list[str]:
        m = fin.get("metrics") or {}
        val_m, test_m = m.get("validation") or {}, m.get("test") or {}
        return [
            f"## {task}",
            f"- Finalize status: `{fin.get('status')}` registered={fin.get('registered')}",
            f"- Algorithm: `{fin.get('algorithm', 'n/a')}`",
            "",
            "| Split | MAE | RMSE | R² | Median AE |",
            "|---|---:|---:|---:|---:|",
            f"| validation | {val_m.get('mae')} | {val_m.get('rmse')} | {val_m.get('r2')} | {val_m.get('median_absolute_error')} |",
            f"| test | {test_m.get('mae')} | {test_m.get('rmse')} | {test_m.get('r2')} | {test_m.get('median_absolute_error')} |",
            "",
            _overfit_note(val_m, test_m, m.get("train")),
        ]

    lines = [SYNTHETIC_BANNER, "", "# Final evaluation (selected winners — test evaluated once)", ""]
    lines.extend(block("parts_cost", parts_f))
    lines.append("")
    lines.extend(block("labour_hours", labour_f))
    return "\n".join(lines)


def _overfit_note(val_m: dict, test_m: dict, train_m: dict | None) -> str:
    if not val_m or not test_m:
        return "_Test metrics unavailable._"
    notes = []
    if train_m and val_m.get("mae") and train_m.get("mae"):
        if train_m["mae"] < 0.5 * val_m["mae"]:
            notes.append("Train MAE substantially lower than validation — possible overfitting.")
    if val_m.get("mae") and test_m.get("mae"):
        ratio = test_m["mae"] / val_m["mae"] if val_m["mae"] else None
        if ratio and ratio > 1.15:
            notes.append(f"Test MAE {ratio:.2f}x validation MAE — generalization gap.")
    return ("**Overfitting notes:** " + " ".join(notes)) if notes else "**Overfitting notes:** No major gaps flagged."


def _execution_report(dataset_meta: dict, execution: dict) -> str:
    return "\n".join(
        [
            SYNTHETIC_BANNER,
            "",
            "# Training execution report",
            "",
            f"- Dataset version: `{dataset_meta.get('dataset_version')}`",
            f"- Fingerprint: `{dataset_meta.get('fingerprint')}`",
            f"- Counts: train={dataset_meta.get('train_rows')} val={dataset_meta.get('val_rows')} test={dataset_meta.get('test_rows')}",
            f"- XGBoost: `{execution.get('xgboost_status')}`",
            f"- Candidate max seconds: `{execution.get('candidate_max_seconds')}`",
            f"- Production registry unchanged: `{execution.get('production_registry_unchanged')}`",
            f"- Artifacts: `{execution.get('artifacts_dir')}`",
            f"- Wall clock (s): parts={execution.get('parts_seconds')} labour={execution.get('labour_seconds')}",
        ]
    )


def _subgroup_report(parts: list[dict], labour: list[dict]) -> str:
    def table(rows: list[dict]) -> str:
        lines = ["| Dimension | Group | n | MAE | RMSE | R² |", "|---|---|---:|---:|---:|---:|"]
        for r in rows:
            if r.get("status") != "OK":
                lines.append(f"| {r.get('dimension')} | {r.get('group')} | {r.get('n')} | — | — | INSUFFICIENT |")
            else:
                lines.append(
                    f"| {r.get('dimension')} | {r.get('group')} | {r.get('n')} | {r.get('mae'):.4f} | "
                    f"{r.get('rmse'):.4f} | {r.get('r2'):.4f} |"
                )
        return "\n".join(lines)

    return "\n".join(
        [
            SYNTHETIC_BANNER,
            "",
            "# Subgroup evaluation (test set — descriptive only)",
            "",
            "## parts_cost",
            table(parts),
            "",
            "## labour_hours",
            table(labour),
        ]
    )
