# synthetic_v1 dataset generation

## Regenerate

```bash
cd backend
python data/financial_models/synthetic_v1/generate_synthetic_repairs.py
```

Options: `--count 10000 --seed 42 --out-dir ...`

## Validate

```bash
python data/financial_models/synthetic_v1/validate_synthetic_dataset.py
```

Exits **1** if critical checks fail on train/validation/test/historical.

## Phase 6 compatibility gate

```bash
python -m app.modules.financial_validation.training.dataset_gate --data-path data/financial_models/synthetic_v1/train.csv
```

## Smoke training (PROVISIONAL — not production)

Requires `pandas`, `scikit-learn`, `joblib`:

```bash
python -m app.modules.financial_validation.training.train_parts_model \
  --data-path data/financial_models/synthetic_v1/train.csv \
  --registry-dir data/financial_models/synthetic_v1/registry_smoke
python -m app.modules.financial_validation.training.train_labour_model \
  --data-path data/financial_models/synthetic_v1/train.csv \
  --registry-dir data/financial_models/synthetic_v1/registry_smoke
```

Do **not** promote `registry_smoke` to production.

## Output files

| File | Purpose |
|------|---------|
| historical_repairs.csv | Full 10k dataset |
| train/validation/test.csv | Leakage-safe splits |
| edge_cases.csv | Invalid/incomplete fixtures |
| dataset_metadata.json | Version, seed, counts |
| dataset_summary.json | Counts + validation snapshot |
| field_compatibility_report.md | Phase 6 mapping |
| data_dictionary.md | Column reference |
| generation_assumptions.md | Simulation logic |
| dataset_quality_report.md | QA summary |
| chart_*.png | EDA charts |
| generate_synthetic_repairs.py | Generator |
| validate_synthetic_dataset.py | Validator |
