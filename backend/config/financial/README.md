# Financial ML configuration (PROVISIONAL)

**Status:** PROVISIONAL — not approved for production decisions.

These YAML files support Phase 6 development while the approved dataset and business-rule specifications are prepared elsewhere.

- Do **not** treat thresholds, bands, or feature mappings as final.
- Final thresholds must be **calibrated on the approved dataset** and documented before production use.
- Replace these files when the approved data dictionary and rules are delivered.

Files:

| File | Purpose |
|------|---------|
| `data_dictionary.yaml` | Logical training dataset schema |
| `feature_mapping.yaml` | Separate training vs inference feature maps |
| `rules.yaml` | PROVISIONAL discrepancy bands and rule IDs |
| `training_defaults.yaml` | Seeds, split strategy placeholders, model candidates |
