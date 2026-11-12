# Phase 6 — Financial validation (in progress)

## Status

| Component | State |
|-----------|--------|
| PROVISIONAL YAML config | Implemented |
| Config loader (no ML deps) | Implemented |
| Feature train/inference maps | Implemented |
| Train/serve consistency tests | Implemented |
| Financial rules (PROVISIONAL bands) | Implemented |
| Prediction service | Implemented (requires optional `ml` extra + registry artifacts) |
| APIs | Implemented |
| Phase 5 assessment wiring | Implemented |
| Hold-out train/val/test training | **Executed** (Gate 2 synthetic_v1) |
| Experimental inference (Gate 3) | **Implemented** — `FINANCIAL_EXPERIMENTAL_MODELS_ENABLED` |
| Production inference | **Unchanged** — no production registry artifacts |
| Production thresholds | **Pending** calibration |

## PROVISIONAL configuration

All files under [`config/financial/`](../config/financial/) are marked **PROVISIONAL**. They must not be used as approved production decision rules until calibrated on the approved dataset.

## APIs

- `GET /api/v1/financial-validation/health`
- `GET /api/v1/financial-validation/models`
- `POST /api/v1/financial-validation/predict`
- `POST /api/v1/financial-validation/analyze`

Assessment: `POST /api/v1/assessment/analyze` accepts optional `financial_enabled`.

## Experimental model inference (Gate 3)

Gate 2 models live under `data/financial_models/synthetic_v1/experimental_artifacts/`.

```bash
# Enable experimental synthetic HistGB models (NOT production)
set FINANCIAL_EXPERIMENTAL_MODELS_ENABLED=true
set FINANCIAL_EXPERIMENTAL_REGISTRY_DIR=data/financial_models/synthetic_v1/experimental_artifacts
```

With the flag **off** (default), APIs abstain when the production registry has no eligible models.

Responses label **SYNTHETIC DATA — EXPERIMENTAL EVALUATION** in `limitations` and set `human_review_required=true`.

## Dependencies

- **Core:** `pyyaml` (configuration)
- **Optional:** `pip install -e ".[ml]"` for pandas, scikit-learn, joblib (training/inference)

## Training (pending approved dataset)

Do not report accuracy from `tests/fixtures/financial/tiny_training.csv` (SYNTHETIC_TEST_ONLY).

### CLIs

```bash
# Compatibility gate (set FINANCIAL_TRAINING_DATA_PATH or --data-path)
python -m app.modules.financial_validation.training.dataset_gate --data-path <approved.csv>

# EDA (optional ml extra)
python -m app.modules.financial_validation.analysis.exploratory_analysis --data-path <approved.csv>

# Train single candidate (fit preprocessor on --data-path only; optional hold-out metrics)
python -m app.modules.financial_validation.training.train_parts_model --data-path <train.csv> --validation-path <validation.csv> --test-path <test.csv> --no-register

python -m app.modules.financial_validation.training.train_labour_model --data-path <train.csv> --validation-path <validation.csv> --test-path <test.csv> --no-register

# Compare all configured candidates (validation required; test optional; default does not register)
python -m app.modules.financial_validation.training.compare_models --task parts_cost --train-path <train.csv> --validation-path <validation.csv> --test-path <test.csv>

python -m app.modules.financial_validation.training.compare_models --task labour_hours --train-path <train.csv> --validation-path <validation.csv> --test-path <test.csv>
```

Supported regressor keys: `dummy_mean`, `linear_regression`, `ridge`, `random_forest`, `gradient_boosting`, `hist_gradient_boosting`, `xgboost` (optional; **NOT RUN** if `ml-xgb` not installed). CatBoost is intentionally omitted.

Registry lifecycle: `synthetic_v1` registrations use `status=experimental`, `lifecycle=experimental`, `synthetic_data=true`, and are **not** used for production inference. Test fixtures register as `lifecycle=validation`. Production models require `lifecycle=production` and `production_ready=true`.

**Feature notes (Gate 1):** `vehicle_age` is trained from CSV `vehicle_age_years` (aligned with inference `vehicle_age_from_submission`). CSV `component` is excluded because `Repair` claims do not expose a component field at submission.

When the approved dataset is available:

1. Run `dataset_gate` and fix mapping/rules issues
2. Run EDA and document split justification
3. Train parts and labour models separately (preprocessor fitted on training data only)
4. Register artifacts under `data/financial_models/`
5. Document **real** metrics in this file (replace PROVISIONAL thresholds)

## Semantics

- **PENDING:** Financial disabled on assessment request
- **UNAVAILABLE:** Enabled but models missing or predictions not produced
- **INSUFFICIENT_DATA / NEEDS_REVIEW:** Rules abstain — never treated as fraud
- Missing models **never** yield `WITHIN_EXPECTED_RANGE`
