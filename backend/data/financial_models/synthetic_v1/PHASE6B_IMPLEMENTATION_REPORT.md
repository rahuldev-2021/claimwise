# Phase 6B implementation report — synthetic historical repairs

## A. Existing implementation audit

**Inspected files:**

- `config/financial/feature_mapping.yaml`, `data_dictionary.yaml`, `training_defaults.yaml`
- `app/modules/financial_validation/training/train_common.py`, `dataset_gate.py`
- `app/modules/financial_validation/data/validation.py`, `preprocessing.py`, `ingestion.py`
- `app/modules/financial_validation/features/feature_engineering.py`
- `tests/fixtures/financial/tiny_training.csv`

**ML feature inputs (see `config/financial/feature_mapping.yaml`):** `vehicle_make`, `vehicle_model`, `model_year`, `vehicle_age` (CSV `vehicle_age_years`), `mileage`, `engine_type`, `vehicle_category`, `repair_category`, `part_description` (CSV `part`), `repair_action`, `repair_complexity`, `currency`, `price_year` (CSV `price_date`). **`part_number` is metadata only — not an ML feature.** CSV `component` is not mapped (no claim submission field).  
**Targets:** `parts_cost`, `labour_hours` (independent tasks).

**Compatible:** Yes — `dataset_gate` on `train.csv` returned `approved_training_ready: true`.

## B. Dataset summary

| Metric | Value |
|--------|-------|
| Total records | 10,000 |
| Unique vehicles | 2,714 |
| Currency | USD |
| Date range | 2018-01-01 — 2024-12-31 |
| Train / val / test | 7,035 / 1,477 / 1,488 |
| Random seed | 42 |

Category coverage: 12 repair categories (`BRAKES` … `BODY`) with weighted sampling.

## C. Data quality

- **Missing values:** None on required fields in primary splits.
- **Duplicates:** No duplicate `repair_record_id` in main files.
- **Invalid values:** Only in `edge_cases.csv` (by design).
- **Leakage:** No forbidden columns; targets not duplicated as features.
- **Validator:** `validate_synthetic_dataset.py` exit code **0**.

## D. Split methodology

Group split by `vehicle_id` 70/15/15 (seed 42 for vehicle assignment). Prevents same-vehicle records in multiple splits.

## E. Generated artifacts

All under `backend/data/financial_models/synthetic_v1/`:

- CSVs: `historical_repairs.csv`, `train.csv`, `validation.csv`, `test.csv`, `edge_cases.csv`
- Scripts: `generate_synthetic_repairs.py`, `validate_synthetic_dataset.py`
- Docs: `data_dictionary.md`, `field_compatibility_report.md`, `generation_assumptions.md`, `dataset_quality_report.md`, `dataset_generation_README.md`, this report
- Metadata: `dataset_metadata.json`, `dataset_summary.json`
- Charts: `chart_*.png` (7 files)
- Smoke registry: `registry_smoke/` (not production)

## F. Test results (executed)

| Step | Result |
|------|--------|
| `generate_synthetic_repairs.py` | **Pass** — 10,000 rows |
| `validate_synthetic_dataset.py` | **Pass** (exit 0) |
| `dataset_gate` on `train.csv` | **Pass** — `approved_training_ready: true` |
| `train_parts_model` (dummy_mean, smoke registry) | **Pass** — in_sample_mae ≈ 379.89 (provisional) |
| `train_labour_model` (dummy_mean, smoke registry) | **Pass** — completed (provisional metrics in registry) |

No application code or Phase 6 architecture was modified.

## G. Limitations

- Synthetic USD distributions only; **not** real warranty economics.
- Default training candidate in smoke run was `dummy_mean` (first in PROVISIONAL YAML); use `hist_gradient_boosting` after approved calibration.
- INR not used in training set (config allows USD/CAD only).

## I. Stakeholder correction pass (2026-11-12)

| Issue | Resolution |
|-------|------------|
| ML feature mismatch | Added `vehicle_category`, `part_description`, `repair_action`, `repair_complexity` to training + inference; removed `part_number` from features |
| Unique part_number | Replaced with reusable `SKU-*` catalog IDs (metadata only) |
| Repair vs replacement | 8 templates switched to Repair; ~42% Repair rows |
| Stale validation_results.json | Regenerated from validator v2 |
| Duplicate ID edge case | Two rows share `EDGE-DUP-001` |
| Validator gaps | Age/mileage/vehicle consistency, finite numerics, split coverage, action mix |
| Train/infer CSV mapping bug | Fixed `train_common` rename + consistency check on feature **keys** |

Dataset version: **synthetic_v1.1**, generator **1.1.0**.

## H. Next recommended step (Phase 6B+)

1. Run EDA on `validation.csv` / `test.csv` and document held-out metrics.
2. Train `hist_gradient_boosting` on `train.csv`; evaluate MAE on `test.csv`.
3. Update PROVISIONAL `rules.yaml` bands from quantiles on validation data.
4. Request stakeholder approval before updating `config/financial/data_dictionary.yaml` from PROVISIONAL to approved.
