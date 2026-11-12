# Generation assumptions — synthetic_v1

**Disclaimer:** All pricing and labour relationships are **simulation assumptions**, not OEM or market data.

## Vehicle assumptions

- Fictional makes/models (`Apex`, `Bravo`, …) as categorical labels only.
- Model years 2012–2023; repair dates 2018–2024.
- Mileage: function of vehicle age with random noise (imperfect correlation).

## Repair assumptions

- 12 categories with weighted templates (brakes/electrical more frequent than transmission clutch).
- Actions and components paired (no random cross-pairing).
- Complexity LOW/MEDIUM/HIGH with multipliers on parts and labour.

## Financial assumptions (USD)

- Base parts/labour per template × vehicle category multiplier × complexity × lognormal noise × supplier jitter.
- Independent noise on parts vs labour (separate targets).
- Replacement vs repair: repair lowers parts, raises labour slightly.

## Split assumptions

- ~2,714 unique vehicles; ~10,000 repair rows (~3.7 repairs/vehicle average).
- **70/15/15 by `vehicle_id`** (no vehicle appears in more than one split).

## Repair operations

Templates include both **Replacement** and **Repair** (resurface, reseal, flush, rebuild-style) with different cost multipliers.

## Part identifiers

`part_number` uses reusable **SKU-{category}-{PART-SLUG}** catalog IDs (not row-sequential PN-BRA-000001). **Not** used as ML features.

## Known simulation gaps

- No regional labour-rate differences  
- No parts-price inflation over `price_date`  
- No supplier/OEM price tables  
- Fictional vehicle makes/models  

## Seed

`random_seed=42` in `generate_synthetic_repairs.py` (version **1.1.0**, dataset **synthetic_v1.1**).
