**SYNTHETIC DATA — EXPERIMENTAL EVALUATION**

# Model selection (validation only)

## parts_cost
- Outcome: **SELECTED**
- Selected algorithm (validation MAE): `hist_gradient_boosting`
- Details: ```json
{
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
```

## labour_hours
- Outcome: **SELECTED**
- Selected algorithm: `hist_gradient_boosting`
- Details: ```json
{
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
```