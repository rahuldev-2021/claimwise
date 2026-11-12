# Dataset quality report — synthetic_v1.1

**Validated:** `validate_synthetic_dataset.py` (see `validation_results.json` for machine output).

## Record counts (current)

| Split | Rows |
|-------|------|
| historical_repairs.csv | 10,000 |
| train.csv | 7,035 |
| validation.csv | 1,477 |
| test.csv | 1,488 |

## Checks performed (automated)

- Required columns for Phase 6 + repair features  
- Unique `repair_record_id` on primary splits  
- Single currency (USD) on training splits  
- Positive, finite `parts_cost` / `labour_hours`  
- `vehicle_age_years` = year(`price_date`) − `model_year`  
- Consistent `vehicle_id` → make/model/year/category  
- `repair_action` ∈ {Replacement, Repair}; `repair_complexity` ∈ {LOW, MEDIUM, HIGH}  
- Split partition: train+val+test = historical; no vehicle_id overlap; no ID overlap  
- Repair/Replacement mix: ~58% / ~42% (seed 42)  
- Reusable `part_number` SKUs (~26 unique part types)  

## Edge cases

`edge_cases.csv` includes intentional invalid rows + **true duplicate** `repair_record_id` (`EDGE-DUP-001` × 2).

## Limitations (unchanged)

Simulation only: no regional labour rates, inflation, OEM pricing, or supplier realism. See `generation_assumptions.md`.
