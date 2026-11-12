# Phase 6 Gate 3 — Financial ML integration report

**Date:** 2026-11-12  
**Models:** HistGradientBoosting (`hist_gradient_boosting`) for `parts_cost` and `labour_hours`  
**Registry:** `data/financial_models/synthetic_v1/experimental_artifacts/`  
**Banner:** **SYNTHETIC DATA — EXPERIMENTAL EVALUATION**

## Step 1 — Audit summary

| Component | Pre-Gate 3 | Gate 3 change |
|-----------|------------|----------------|
| `FinancialValidationService` | Orchestrates features → predict → rules | Unchanged flow; enriched result metadata |
| `PredictionService` | Single production registry path | **Settings-driven** production vs experimental registry |
| `ModelRegistry` | `get_active_entry` production-only | **`inference_mode`** + `eligible_for_experimental_inference()` |
| Financial APIs | `/health`, `/models`, `/predict`, `/analyze` | Org-scoped auth on predict/analyze; `claims:read` on `/models`; health unauthenticated |
| Phase 5 assessment | Calls `FinancialValidationService` | Inherits experimental settings from `Settings` |
| Feature engineering | Aligned with Gate 1 / synthetic_v1 | No change |

No duplicate services or pipelines were added.

## Step 2 — Experimental integration

Enable explicitly:

```bash
# Environment (example)
FINANCIAL_EXPERIMENTAL_MODELS_ENABLED=true
FINANCIAL_EXPERIMENTAL_REGISTRY_DIR=data/financial_models/synthetic_v1/experimental_artifacts
```

| Flag off (default) | Flag on |
|-------------------|---------|
| Registry `data/financial_models` | Registry `FINANCIAL_EXPERIMENTAL_REGISTRY_DIR` |
| `inference_mode=production` | `inference_mode=experimental` |
| Experimental artifacts **not** loaded | Gate 2 HistGB models loaded |

Production registry path remains **unchanged** (no `data/financial_models/registry.json`).

## Step 3 — API examples

### Health (experimental off)

```json
{
  "financial_enabled": true,
  "inference_mode": "production",
  "parts_model_loaded": false,
  "labour_model_loaded": false,
  "experimental_models_enabled": false
}
```

### Predict / analyze (experimental on)

Response includes existing fields plus:

- `parts_model_algorithm` / `labour_model_algorithm` — e.g. `hist_gradient_boosting`
- `model_lifecycle` — `experimental`
- `experimental_prediction` / `synthetic_data_prediction` — `true`
- `human_review_required` — always `true`
- `limitations` — synthetic-data disclaimer
- `parts_discrepancy_pct` / `labour_discrepancy_pct` — from PROVISIONAL rules

## Step 4 — Safety

- No automatic approve/reject; `human_review_required=true`
- Phase 4 / Phase 5 unchanged
- `/models` redacts `training_data_version`; artifacts not served via API
- **Authorization:** `POST /predict` and `POST /analyze` require `claims:assess` and resolve claims via `ClaimService.get_claim_for_user` (same pattern as technical validation and assessment). `GET /models` requires `claims:read`. `GET /health` remains unauthenticated for probes.

## Step 5 — Tests

See Gate 3 completion section in the final chat summary (unit + integration execution).

## Verdict

**READY FOR GATE 4** — experimental inference is wired behind an explicit flag; production path remains isolated.
