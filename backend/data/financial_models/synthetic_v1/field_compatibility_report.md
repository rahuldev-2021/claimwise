# Field compatibility report — synthetic_v1.1 vs Phase 6 pipeline

**Updated:** 2026-11-12 after stakeholder review (feature alignment + part_number exclusion).

## ML training features (keys in `feature_mapping.training.columns`)

| Feature ID | CSV column | Inference source | Notes |
|------------|------------|------------------|-------|
| vehicle_make | vehicle_make | `vehicle.make` | Required |
| vehicle_model | vehicle_model | `vehicle.model` | Required |
| model_year | model_year | `vehicle.model_year` | Required |
| mileage | mileage | `vehicle.mileage` | Optional; abstain if missing |
| engine_type | engine_type | `vehicle.engine_type` | Optional |
| **vehicle_category** | vehicle_category | Derivation `vehicle_category_from_claim_or_lookup` | Optional at inference |
| repair_category | repair_category | `recommended_repair.repair_category` | Required |
| **part_description** | part | `recommended_repair.part_description` | Required |
| **repair_action** | repair_action | `recommended_repair.recommended_action` | Required |
| **repair_complexity** | repair_complexity | Derivation `repair_complexity_from_action` | Optional |
| currency | currency | `currency` | Required |
| price_year | price_date | Derivation `price_year_from_submission` | Training uses historical date |
| vehicle_age | (derived at inference) | `vehicle_age_from_submission` | Not a CSV training column |

## Excluded from ML inputs

| Column | Reason |
|--------|--------|
| **part_number** | Was one-per-record; now **SKU-* catalog IDs** stored for traceability only, **not** in `feature_ids` |
| parts_cost / labour_hours | Targets only |
| component, fuel_type, transmission_type | Metadata / EDA only (unless added to YAML later) |

## Targets

- `parts_cost` — parts cost model  
- `labour_hours` — labour hours model  

## Code fixes (minimal)

- `train_common._dataframe_from_csv`: CSV header → feature id rename (`csv_col: feature_id`).
- `consistency.validate_training_inference_consistency`: iterate training **keys** (feature ids), not CSV column names.

## Gate

`dataset_gate` on `train.csv` → `approved_training_ready: true` (PROVISIONAL config still applies).
