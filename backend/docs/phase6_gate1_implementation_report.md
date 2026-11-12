# Phase 6B Gate 1 — Implementation report

**Date:** 2026-11-12  
**Scope:** Training/evaluation extensions only — **no full synthetic_v1 training run**, no production registry writes.

## Implemented

1. **Train / validation / test paths** in `train_common.load_task_split_frames`, `train_regressor`, and `compare_regressor_candidates`.
2. **Preprocessor** fitted on training rows only; validation/test transformed with the train-fitted artifact.
3. **Metrics:** MAE, RMSE, R², median absolute error (`training/evaluation.regression_metrics`).
4. **Candidate comparison and selection** (`compare_regressor_candidates`, `select_best_candidate`, CLI `compare_models`).
5. **Regressor factory** (`models/regressor_factory.py`) with optional XGBoost skip when not installed.
6. **Registry lifecycle** fields: `lifecycle`, `synthetic_data`, `production_ready`, `algorithm`; `experimental` synthetic models excluded from production inference.
7. **`vehicle_age` training parity** via `vehicle_age_years` column mapping; fallback derivation from `price_date` and `model_year` when years column absent.
8. **`component` feature decision:** excluded — `app.schemas.repair.Repair` has no component field at claim submission.

## Gate 2 commands (planned; not executed in Gate 1)

From `backend/`:

```bash
python -m app.modules.financial_validation.training.compare_models ^
  --task parts_cost ^
  --train-path data/financial_models/synthetic_v1/train.csv ^
  --validation-path data/financial_models/synthetic_v1/validation.csv ^
  --test-path data/financial_models/synthetic_v1/test.csv

python -m app.modules.financial_validation.training.compare_models ^
  --task labour_hours ^
  --train-path data/financial_models/synthetic_v1/train.csv ^
  --validation-path data/financial_models/synthetic_v1/validation.csv ^
  --test-path data/financial_models/synthetic_v1/test.csv
```

To register winners into an isolated experimental registry (Gate 2, after approval):

```bash
python -m app.modules.financial_validation.training.compare_models ^
  --task parts_cost ^
  --train-path data/financial_models/synthetic_v1/train.csv ^
  --validation-path data/financial_models/synthetic_v1/validation.csv ^
  --test-path data/financial_models/synthetic_v1/test.csv ^
  --registry-dir data/financial_models/synthetic_v1/experimental_registry ^
  --register-winner
```

## Status

**Gate 1:** **READY** for Gate 2 execution pending user approval.
