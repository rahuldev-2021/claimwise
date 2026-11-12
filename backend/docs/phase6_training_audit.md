# Phase 6B — Gate 0: Training architecture audit

**Scope:** Read-only inspection per Phase 6B spec §2 and §20 Gate 0.  
**Date:** 2026-11-12  
**Verdict:** **READY WITH FIXES** — existing pipeline is reusable; significant gaps vs §7–§13 require minimal Gate 1 extensions before full candidate comparison and hold-out evaluation.

---

## 1. Training architecture

| Layer | Location | Role |
|--------|----------|------|
| Config | `config/financial/*.yaml` | Feature map, data dictionary, training defaults, rules (all **PROVISIONAL**) |
| Ingestion / validation | `app/modules/financial_validation/data/ingestion.py`, `validation.py` | CSV load, schema and quality checks |
| Preprocessing | `app/modules/financial_validation/data/preprocessing.py` | `FinancialFeaturePreprocessor` (impute + one-hot / numeric) |
| Training core | `app/modules/financial_validation/training/train_common.py` | Single-candidate fit, artifact save, registry update |
| CLIs | `training/train_parts_model.py`, `training/train_labour_model.py` | `--data-path`, `--registry-dir`, `--model-candidate`, `--allow-synthetic-test` |
| Dataset gate | `training/dataset_gate.py` | Pre-train compatibility on one CSV path |
| Evaluation (partial) | `training/evaluation.py` | **Split strategy resolution only** — no metric computation or CV loops |
| EDA | `analysis/exploratory_analysis.py` | Optional exploratory script |
| Model factories | `models/parts_cost_model.py`, `models/labour_hours_model.py` | `create_estimator(candidate, seed)` |
| Registry | `models/model_registry.py` | `registry.json` + joblib artifacts under registry root |
| Inference | `services/prediction_service.py` | Load latest compatible entry per task; abstain if missing / schema mismatch |
| Product integration | `services/financial_validation_service.py` | Two independent predictions → PROVISIONAL rules |

**Flow today**

1. Load one CSV (`--data-path`).
2. Validate via `validate_training_csv`.
3. Rename CSV columns via `feature_mapping.training.columns`.
4. Build `X` from configured feature ids present in the training map; fit preprocessor on **all rows in that CSV**.
5. Train **one** estimator (`--model-candidate` or first entry in `training_defaults.model_candidates`).
6. Compute **in-sample MAE** on the same `X`.
7. Write `model.joblib`, `preprocessor.joblib`, append `ModelRegistryEntry` (`status: trained`, `metrics.provisional: true`).

**Gaps vs Phase 6B spec**

- No orchestration that uses pre-made `train.csv` / `validation.csv` / `test.csv` together.
- No validation-set metrics, candidate comparison, or test-set final evaluation in code.
- No RMSE / R² / median AE, subgroup metrics, or timing reports in training path.
- No explicit `experimental` / `synthetic` registry lifecycle (only `stub` | `trained`).
- Synthetic v1 path is **not** blocked by `train_common` (guard applies only to `tests/fixtures` and `tiny_training` paths).

---

## 2. Supported algorithms (factories)

Implemented in `create_estimator` (parts and labour mirrors):

| Candidate key | Estimator | In `training_defaults.yaml`? |
|---------------|-----------|--------------------------------|
| `dummy_mean` | `DummyRegressor` | Yes |
| `ridge` | `Ridge` | Yes |
| `random_forest` | `RandomForestRegressor` (50 trees) | **No** (factory only) |
| `hist_gradient_boosting` | `HistGradientBoostingRegressor` | Yes |

**Not implemented in factories (spec §7)**

| Requested | Status |
|-----------|--------|
| Linear Regression | **NOT RUN** — no factory key |
| Ridge Regression | **Supported** |
| Random Forest | **Supported** (not in default candidate list) |
| Gradient Boosting Regressor | **NOT RUN** — only `HistGradientBoostingRegressor` |
| XGBoost | **NOT RUN** — no factory; optional dep `ml-xgb` exists, **not installed** in current venv |
| CatBoost | **NOT RUN** — no factory; **no** optional dependency in `pyproject.toml` |

**Dependencies (`pyproject.toml`)**

- `pip install -e ".[ml]"` → pandas, scikit-learn, joblib (sufficient for current factories).
- `pip install -e ".[ml-xgb]"` → xgboost only (still needs factory + Gate 1 wiring).
- CatBoost would need a new optional extra and factory entry if desired.

---

## 3. Feature mapping

**File:** `config/financial/feature_mapping.yaml` (v0.1-synthetic_v1)

**ML feature ids (training when mapped in `training.columns`):**

- `vehicle_make`, `vehicle_model`, `model_year`, `mileage`, `engine_type`
- `vehicle_category`, `repair_category`, `part_description` (CSV `part`)
- `repair_action`, `repair_complexity`, `currency`, `price_year` (CSV `price_date`)

**Explicitly excluded from ML:** `part_number` (metadata / SKU in CSV only).

**Inference-only or unmapped at train time**

- `vehicle_age` — in `feature_ids` and `NUMERIC_FEATURES`, but **not** in `training.columns`. Training uses `model_year`; inference derives age from submission date. CSV also has `vehicle_age_years` (not wired to training map).
- `region` — in `feature_ids`, not in CSV and not in `training.columns`.

**Train/serve consistency:** `features/consistency.py` + unit tests; `dataset_gate` runs `validate_training_inference_consistency`.

**Preprocessor categoricals:** `part_number` removed from `CATEGORICAL_FEATURES` (aligned with mapping).

---

## 4. Dataset schema compatibility

See **`phase6_dataset_compatibility_report.md`** for full Gate 0 dataset audit.

Summary: `synthetic_v1` train/val/test/historical align with `data_dictionary` required fields; `dataset_gate` on `train.csv` → `approved_training_ready: true`.

---

## 5. Train / validation / test split handling

**Dataset (synthetic_v1):** Pre-split files with **vehicle_id group separation** (70/15/15). Validated by `data/financial_models/synthetic_v1/validate_synthetic_dataset.py` — `split_issues: []`, no vehicle overlap across splits.

**Training code:** Does **not** read `validation.csv` or `test.csv`. Caller must pass `train.csv` only and implement hold-out evaluation separately (Gate 1).

**Config:** `training_defaults.yaml` lists `evaluation.strategy: auto` with `group_columns: [vehicle_make, vehicle_model]` — `resolve_evaluation_strategy` returns `group_kfold` when those columns exist, but **no k-fold training loop** consumes this.

---

## 6. Model evaluation implementation

| Capability | Status |
|------------|--------|
| `resolve_evaluation_strategy` | Implemented |
| MAE on validation / test | **Missing** |
| RMSE, R², median AE | **Missing** |
| Subgroup / residual reports | **Missing** (EDA script may help manually) |
| Candidate comparison tables | **Missing** |
| In-sample MAE in `train_regressor` | Implemented (not suitable for model selection) |

---

## 7. Model registry

- **Path:** default `data/financial_models/` (override `--registry-dir`).
- **Artifacts:** `{task}/{version}/model.joblib`, `preprocessor.joblib`, `registry.json`.
- **Fields:** task, version, paths, `feature_schema_hash`, sklearn version, training data path string, evaluation strategy note, metrics dict, `status`, `trusted`.
- **Selection:** `PredictionService` picks latest entry matching schema hash per task.
- **Gaps:** No `experimental` / `synthetic_only` status enum; metrics do not record val/test splits; overwriting same timestamp version is avoided by new version stamps.

Smoke artifacts may exist under `data/financial_models/synthetic_v1/registry_smoke/` — treat as non-production.

---

## 8. CPU compatibility

- All current estimators are scikit-learn CPU implementations.
- `HistGradientBoostingRegressor` and `RandomForestRegressor` use default threading; suitable for laptop CPU with modest `n_estimators` in factory.
- No CUDA/GPU requirements in code paths inspected.
- Gate 2 should train **one candidate at a time** (spec §7) — not enforced in code yet.

---

## 9. Tests and missing functionality

**Existing tests (financial_ml marker):**

| File | Coverage |
|------|----------|
| `test_financial_config.py` | Config load |
| `test_financial_data.py` | Validation / ingestion |
| `test_financial_features.py` | Feature extraction |
| `test_financial_leakage.py` | Forbidden columns vs training feature ids |
| `test_financial_registry.py` | Registry IO / trust |
| `test_financial_evaluation.py` | Split strategy resolution only |
| `test_financial_training_pipeline.py` | Single-candidate train on tiny fixture + predict |
| `test_financial_rules.py` | Rule bands |
| `integration/test_financial_validation_api.py` | Health / analyze without models |

**Gate 0 execution:** `pytest` on the unit files above — **13 passed** (2026-11-12).

**Missing vs Phase 6B §17**

- Multi-candidate sequential training and comparison
- Preprocessor fit **only** on train split when val present (today: fit on whatever CSV is passed — correct if path is `train.csv` only)
- Val/test metrics and model selection tests
- Extended factory tests (linear, GBR, XGB, CatBoost)
- Registry experimental status and synthetic propagation
- Vehicle-group split enforcement in training CLI

---

## 10. Proposed minimal Gate 1 changes (approval required)

Do **not** create a second pipeline. Extend existing modules:

1. **Metrics module** — e.g. extend `training/evaluation.py` with `regression_metrics(y, pred)` and optional subgroup helpers.
2. **Comparison orchestrator** — e.g. `training/compare_candidates.py` or extend `train_common` with `--train-path`, `--validation-path`, `--test-path`, `--register-winner`, loop candidates from config/spec, fit preprocessor on train only, register with enriched metrics and `status`/synthetic flags.
3. **Factories** — add keys: `linear_regression`, `gradient_boosting` (sklearn `GradientBoostingRegressor`), optional `xgboost` / `catboost` behind import guards; document **NOT RUN** when deps missing.
4. **Registry** — extend `ModelRegistryEntry.status` or metrics flags for `experimental` + `synthetic_data: true` without promoting to production.
5. **Config** — update `training_defaults.yaml` candidate lists and document evaluation strategy justification for vehicle-group **hold-out** (pre-split files) vs `group_kfold`.
6. **Feature mapping (optional, documented)** — decide whether to map `vehicle_age_years` → `vehicle_age` for training parity with inference; do not add `part_number` or `component` without prediction-time availability proof.
7. **Tests** — cover new metrics, compare workflow, and fit-on-train-only with external val CSV.
8. **Reports** — emit spec §16 markdown/JSON from orchestrator runs (Gate 2).

---

## 11. Verified training commands (current codebase)

From repository root `backend/` with venv and `pip install -e ".[ml]"`:

```bash
# Dataset compatibility (Gate 0 — executed)
python -m app.modules.financial_validation.training.dataset_gate --data-path data/financial_models/synthetic_v1/train.csv

python data/financial_models/synthetic_v1/validate_synthetic_dataset.py

# Single-candidate train (provisional in-sample MAE only — not Phase 6B selection)
python -m app.modules.financial_validation.training.train_parts_model --data-path data/financial_models/synthetic_v1/train.csv --registry-dir data/financial_models/synthetic_v1/experimental_registry --model-candidate ridge

python -m app.modules.financial_validation.training.train_labour_model --data-path data/financial_models/synthetic_v1/train.csv --registry-dir data/financial_models/synthetic_v1/experimental_registry --model-candidate hist_gradient_boosting
```

Optional EDA:

```bash
python -m app.modules.financial_validation.analysis.exploratory_analysis --data-path data/financial_models/synthetic_v1/train.csv
```

**Note:** Do not register synthetic runs into default `data/financial_models/` production registry until lifecycle rules are agreed.

---

## 12. Gate 0 status

| Item | Result |
|------|--------|
| Architecture reusable | **PASS** |
| Dataset approved for training path | **PASS** (see compatibility report) |
| Spec-complete training/evaluation | **FAIL** (Gate 1) |
| All spec algorithms | **PARTIAL** (3/6 sklearn-native; XGB/CatBoost **NOT RUN**) |
| Hold-out val/test in trainer | **NOT APPLICABLE** until Gate 1 |

**Gate 0:** **READY WITH FIXES** — proceed to Gate 1 after explicit approval; do not run full candidate training/registration as production until orchestration and metrics exist.
