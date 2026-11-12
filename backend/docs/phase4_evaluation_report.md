# Phase 4 evaluation report (template)

**Dataset:** Synthetic fixtures (`tests/unit/test_tv_rules.py`, integration CLM-001/002).  
**Status:** Baseline run pending labelled expert scenarios (target 50–100).

## Metrics (to record per release)

| Metric | Definition | Current |
|--------|------------|---------|
| Unsupported finding rate | Findings without claim/evidence trace | TBD |
| Repair↔diagnosis association accuracy | vs labelled `repair_action_assessments` | TBD |
| False contradiction rate | | TBD |
| Missing evidence precision | Structured `source_scope_checked` | TBD |
| Evidence reference integrity | Pydantic ref validation + integration test | **PASS** (automated) |
| Abstention correctness | INSUFFICIENT / NOT_CHECKED wording | TBD |
| Expert agreement | | TBD |

## Limitations

- Synthetic sample claims and corpus only.
- Do not infer real-world automotive accuracy from these metrics.
