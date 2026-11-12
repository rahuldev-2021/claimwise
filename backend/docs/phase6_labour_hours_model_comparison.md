**SYNTHETIC DATA — EXPERIMENTAL EVALUATION**

# labour_hours — candidate comparison (validation)

| Algorithm | Status | Val MAE (hours) | Val RMSE | Val R² | Val MedAE | Train (s) |
|---|---:|---:|---:|---:|---:|---:|
| xgboost | NOT RUN |  |  |  |  |  |
| dummy_mean | RUN | 2.0308762647734344 | 2.7702433040882513 | -3.1472045303182483e-07 | 1.6671058990760481 | 0.097 |
| linear_regression | RUN | 0.43090783713260794 | 0.6778482359201298 | 0.9401272440359132 | 0.2935956178124659 | 0.114 |
| ridge | RUN | 0.4301451635192395 | 0.6777530685722905 | 0.940144054676133 | 0.2913253517929002 | 0.096 |
| random_forest | RUN | 0.31161205145565335 | 0.5137747624331137 | 0.9656038492850638 | 0.17520000000000113 | 2.422 |
| gradient_boosting | RUN | 0.3917075423488175 | 0.5769797296493829 | 0.9566204122193036 | 0.27090847476494995 | 4.842 |
| hist_gradient_boosting | RUN | 0.2939784991951627 | 0.4784605256240834 | 0.9701697745881842 | 0.17105416021851205 | 0.818 |

**Validation winner (MAE tie-break):** `hist_gradient_boosting`
**Selection outcome:** `SELECTED`
**Rationale:** {
  "criteria": {
    "min_relative_mae_improvement_vs_dummy": 0.02,
    "weak_r2_threshold": 0.0,
    "rationale": "Candidate must improve validation MAE by at least min_relative_mae_improvement_vs_dummy (default 2%) versus dummy_mean; validation R\u00b2 at or below weak_r2_threshold yields weak performance."
  },
  "selected_candidate": "hist_gradient_boosting",
  "validation_mae": 0.2939784991951627,
  "validation_r2": 0.9701697745881842,
  "dummy_validation_mae": 2.0308762647734344,
  "relative_mae_improvement_vs_dummy": 0.8552454896960653,
  "reason": "meets validation improvement and R\u00b2 criteria"
}