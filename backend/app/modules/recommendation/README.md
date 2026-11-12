# Recommendation Module (Phase 5)

Deterministic Python business rules produce the **final** system recommendation. LLM output is **advisory only** and never overrides Phase 4 technical validation.

## Outcomes

- `PROCEED_TO_HUMAN_REVIEW` (alias `PROCEED_TO_REVIEW`)
- `REQUEST_MORE_EVIDENCE`
- `FLAG_FOR_REVIEW`
- `INSUFFICIENT_INFORMATION`

Financial assessment status remains `PENDING` until Phase 6.

## Entry point

`RecommendationEngine.recommend(RecommendationContext)` — see `business_rules.py` for rule IDs (`R_*`).
