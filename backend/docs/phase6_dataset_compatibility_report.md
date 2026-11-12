# Phase 6B — Dataset compatibility report (synthetic_v1)

**Scope:** Gate 0 read-only validation of `backend/data/financial_models/synthetic_v1/` against CLAIMWISE financial config and Phase 6B spec §3.  
**Date:** 2026-11-12  
**Dataset version:** `synthetic_v1.1` (generator 1.1.0, seed 42, USD)

---

## Executive summary

| Check | Result |
|-------|--------|
| Required columns / targets | **PASS** |
| Split integrity (vehicle groups) | **PASS** |
| Synthetic provenance | **PASS** |
| Currency consistency (main splits) | **PASS** |
| Target validity / finiteness | **PASS** (main splits) |
| Feature mapping alignment | **PASS** (`dataset_gate` feature_mapping_issues: []) |
| `part_number` excluded from ML features | **PASS** |
| `dataset_gate` approved_training_ready | **PASS** |
| Repair actions diversity | **PASS** (~42% Repair / ~58% Replacement) — models must not be described as replacement-only |
| Config `data_dictionary.yaml` version | **WARN** — still marked `0.0-provisional`; CSV matches template fields |
| Training vs inference feature parity (`vehicle_age`) | **WARN** — see §Critical checks |
| Unused CSV signal (`component`) | **INFO** — not in feature map; may explain residual variance |

**Overall:** **PASS** — training may proceed on pre-split files **after Gate 1** implements hold-out evaluation. No dataset regeneration required.

---

## 1. Dataset location and counts

| File | Rows | Repair | Replacement | Validator issues |
|------|------|--------|---------------|------------------|
| `historical_repairs.csv` | 10,000 | 4,218 | 5,782 | [] |
| `train.csv` | 7,035 | 2,978 | 4,057 | [] |
| `validation.csv` | 1,477 | 626 | 851 | [] |
| `test.csv` | 1,488 | 614 | 874 | [] |
| `edge_cases.csv` | 12 | 0 | 12 | **By design** (see §Edge cases) |

Counts match `validation_results.json` (`validated_at`: 2026-11-12T05:15:56Z) and `split_counts` in that file.

**Proportion:** ~70.35% / 14.77% / 14.88% train / val / test (target 70/15/15 by vehicle groups).

---

## 2. Gate executions (this audit)

```text
python -m app.modules.financial_validation.training.dataset_gate --data-path data/financial_models/synthetic_v1/train.csv
→ approved_training_ready: true
→ issues: []
→ warnings: ["Possible duplicate vehicle/repair combinations: 6975"]

python data/financial_models/synthetic_v1/validate_synthetic_dataset.py
→ exit 0, critical_pass: true, status: passed, split_issues: []
```

The duplicate vehicle/repair warning reflects **multiple repairs per vehicle** in training data (expected for fleet history), not duplicate `repair_record_id` values.

---

## 3. Schema vs data dictionary

**Targets (independent):** `parts_cost`, `labour_hours` — present, positive in main splits.

**Required training fields (dictionary):** present on CSV header including `vehicle_make`, `vehicle_model`, `model_year`, `repair_category`, `currency`, targets, `price_date`.

**Additional CSV columns (not all used as ML features):**

- `repair_record_id`, `vehicle_id` — identifiers; not in `feature_mapping.feature_ids`
- `vehicle_category`, `repair_action`, `repair_complexity` — mapped for ML
- `component` — **not** in current feature mapping
- `part_number` — catalog metadata; **excluded** from `feature_ids`
- `vehicle_age_years` — not mapped; inference uses derived `vehicle_age`
- `fuel_type`, `transmission_type`, `number_of_parts`, `is_synthetic`, `dataset_version` — metadata / unused by current map

**Leakage columns:** `leakage_forbidden_columns` in YAML do not intersect training feature ids (unit test `test_financial_leakage.py`).

---

## 4. Split and leakage checks

| Check | Result |
|-------|--------|
| `repair_record_id` unique (main files) | **PASS** |
| Split rows partition historical | **PASS** (`split_issues: []`) |
| `vehicle_id` disjoint train / val / test | **PASS** |
| Same vehicle in multiple splits | **PASS** (prevented by design) |
| Targets as input features | **PASS** (not in feature map) |
| `part_number` as ML feature | **PASS** (excluded) |

Split strategy documented in generator metadata: group by `vehicle_id`, seed 42+1 for assignment.

---

## 5. Data quality (main splits)

- **Missing required fields:** none reported by validators on train/val/test/historical.
- **Currency:** USD only on main splits (`require_single_currency_for_parts_training` satisfied).
- **Numeric finiteness:** enforced by synthetic validator; no issues on main files.
- **Plausibility:** labour hours and parts costs positive on main splits; edge file intentionally violates rules.

---

## 6. Critical checks (spec §3)

### 6.1 `part_number` as feature

**PASS.** Removed from `feature_mapping.feature_ids`. Preprocessor categoricals do not include `part_number`. Values are reusable `SKU-*` strings, not used as predictors.

### 6.2 Targets vs missing predictors

**WARN / document for modeling:**

- CSV `component` (component system name) is **not** in the feature map; only `repair_category` and `part` (`part_description`) are used. Subgroup errors by component may be elevated.
- `vehicle_age` at inference ≠ `model_year` used at training unless mapping is extended to `vehicle_age_years` or derived age at train time.

### 6.3 Silent new features

**PASS** for Gate 0 — no new features added in this gate. Any future use of `component` or `vehicle_age_years` requires YAML + inference availability + tests.

### 6.4 Repair vs replacement only

**PASS (diversity).** Main data includes both `Repair` and `Replacement`. Documentation and model cards must state that both actions are in training distribution (not replacement-only).

### 6.5 Stale reports

**PASS after refresh.** `validation_results.json` matches current row counts and split checks.  
**NOTE:** `data/financial_models/synthetic_v1/PHASE6B_IMPLEMENTATION_REPORT.md` still lists `part_number` among required training inputs — **stale**; superseded by `feature_mapping.yaml` v0.1-synthetic_v1.

### 6.6 Edge-case fixtures

**PASS (intentional failures).** `edge_cases.csv` validator reports duplicate `repair_record_id`, INR currency, inconsistent `VH-EDGE-001`, non-positive financials — consistent with negative testing, not used for training.

---

## 7. Compatibility with training pipeline

| Requirement | Status |
|-------------|--------|
| `train.csv` passes `validate_training_csv` | **PASS** |
| Column rename map (`part` → `part_description`, `price_date` → `price_year`) | **PASS** |
| Train CLI synthetic path guard | **NOT APPLICABLE** — guard targets `tests/fixtures` / `tiny_training`, not `synthetic_v1` |
| Fit preprocessor on train only | **PASS** if CLI uses **`train.csv` only** (manual discipline until Gate 1 enforces val/test paths) |
| Use `validation.csv` / `test.csv` in code | **FAIL** — not wired (Gate 1) |

---

## 8. Synthetic-data labeling

All metrics from this dataset must be labeled **synthetic-data evaluation** (spec §10). Models must not be promoted to production-ready in registry without real-data calibration.

---

## 9. Issues blocking training

**None critical.** Training data is compatible with current config and gates.

**Non-blocking recommendations before Gate 2:**

1. Refresh `PHASE6B_IMPLEMENTATION_REPORT.md` §A feature list (remove `part_number` as ML input).
2. Document evaluation strategy: **pre-split vehicle hold-out** (use existing files) rather than re-splitting inside `train_regressor`.
3. Decide on `vehicle_age` training parity (map `vehicle_age_years` or derive from `price_date` − `model_year` at train time).
4. Optionally promote `data_dictionary.yaml` from provisional template to `synthetic_v1`-pinned version after stakeholder sign-off.

---

## 10. Gate 0 dataset verdict

**READY** — dataset validation **PASS**; proceed to **Gate 1** (implementation) with no dataset regeneration.

**Algorithms trained in Gate 0:** **NOT RUN** (read-only audit).  
**Algorithms not run:** All (by design).
