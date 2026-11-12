# synthetic_v1 data dictionary

**Currency:** USD (simulation). **Synthetic:** all rows `is_synthetic=true`.

| Column | Type | Required | Role | Description |
|--------|------|----------|------|-------------|
| repair_record_id | string | yes | id | Unique synthetic repair row ID |
| vehicle_id | string | yes | group key | Stable synthetic vehicle for split grouping |
| vehicle_make | string | yes | **feature** | Categorical make (fictional labels) |
| vehicle_model | string | yes | **feature** | Categorical model |
| model_year | int | yes | **feature** | Model year 2012–2023 |
| vehicle_category | string | no | metadata | HATCHBACK, SEDAN, SUV, CROSSOVER |
| mileage | int | no | **feature** | Odometer; plausible vs age with noise |
| engine_type | string | no | **feature** | I4, I4-T, V6, V8 |
| fuel_type | string | no | metadata | PETROL, DIESEL, HYBRID |
| transmission_type | string | no | metadata | MANUAL, AUTOMATIC, CVT |
| repair_category | string | yes | **feature** | 12 system categories |
| component | string | no | metadata | Component name |
| part | string | no | metadata | Part name |
| repair_action | string | no | metadata | Replacement / Repair |
| repair_complexity | string | no | metadata | LOW, MEDIUM, HIGH |
| number_of_parts | int | no | metadata | Count of parts in repair |
| part_number | string | no | **feature** | Synthetic PN-* |
| currency | string | yes | **feature** | USD |
| parts_cost | decimal | yes | **target (parts model)** | Positive USD, simulation |
| labour_hours | decimal | yes | **target (labour model)** | Positive hours, simulation |
| price_date | date | yes | **feature source** | Mapped to `price_year` in training |
| vehicle_age_years | int | no | QC only | price_date year − model_year |
| is_synthetic | bool string | yes | governance | Always `true` |
| dataset_version | string | yes | governance | `synthetic_v1` |

**Forbidden as inputs:** `parts_cost`, `labour_hours` (targets only), totals, submitted costs, claim IDs.
