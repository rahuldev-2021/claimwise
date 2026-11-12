**SYNTHETIC DATA — EXPERIMENTAL EVALUATION**

# parts_cost — candidate comparison (validation)

| Algorithm | Status | Val MAE (USD) | Val RMSE | Val R² | Val MedAE | Train (s) |
|---|---:|---:|---:|---:|---:|---:|
| xgboost | NOT RUN |  |  |  |  |  |
| dummy_mean | RUN | 399.636389381076 | 544.480508019621 | -1.7500311117801814e-05 | 337.39644491826573 | 0.541 |
| linear_regression | RUN | 87.2918215274359 | 136.58996767964507 | 0.9370666962891836 | 60.35963274811138 | 0.133 |
| ridge | RUN | 87.1221450582938 | 136.3948896595337 | 0.937246330819417 | 60.47030878222483 | 0.119 |
| random_forest | RUN | 65.17108043331076 | 118.34892039476006 | 0.9527532948553296 | 30.173800000000142 | 2.53 |
| gradient_boosting | RUN | 72.7966318147767 | 114.88031864347334 | 0.9554821492329408 | 45.10970364674267 | 6.039 |
| hist_gradient_boosting | RUN | 61.668808499573096 | 112.01815070513696 | 0.9576727821284773 | 28.260420412879114 | 0.96 |

**Validation winner (MAE tie-break):** `hist_gradient_boosting`
**Selection outcome:** `SELECTED`
**Rationale:** {
  "criteria": {
    "min_relative_mae_improvement_vs_dummy": 0.02,
    "weak_r2_threshold": 0.0,
    "rationale": "Candidate must improve validation MAE by at least min_relative_mae_improvement_vs_dummy (default 2%) versus dummy_mean; validation R\u00b2 at or below weak_r2_threshold yields weak performance."
  },
  "selected_candidate": "hist_gradient_boosting",
  "validation_mae": 61.668808499573096,
  "validation_r2": 0.9576727821284773,
  "dummy_validation_mae": 399.636389381076,
  "relative_mae_improvement_vs_dummy": 0.8456877047781342,
  "reason": "meets validation improvement and R\u00b2 criteria"
}