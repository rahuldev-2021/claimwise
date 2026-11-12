# Phase 4 business rules (registry)

**Rules version:** `4.1.0` (see `app/modules/technical_validation/versions.py`)

Detection rules live in `validation_rules.py` and are registered via `rules/technical_rule_registry.py`. **Aggregation** (final `technical_status`) runs only in `aggregation/technical_status_aggregator.py`.

| rule_id | Status when triggered | Human review |
|---------|----------------------|--------------|
| R_EMPTY_RETRIEVAL | INSUFFICIENT_EVIDENCE | default true |
| R_COMPLAINT_DIAGNOSIS_DISCONNECT | NEEDS_REVIEW | true |
| R_SUSPECTED_NO_FINDINGS | INSUFFICIENT_EVIDENCE | true |
| R_EXPLICIT_CONTRADICTION | NEEDS_REVIEW | true |
| R_PROCEDURE_THRESHOLD_UNKNOWN | INSUFFICIENT_EVIDENCE | true |
| R_HISTORY_ONLY | QUESTIONABLE | true |
| R_HEAVY_REPAIR_LIGHT_DIAG | NEEDS_REVIEW | true |
| R_DIRECT_VERIFIED_SUPPORT | SUPPORTED (only if no blocking rules) | may be false |

Blocking rules prevent automatic clearance of `human_review_required`.
