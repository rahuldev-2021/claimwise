# Phase 5 evaluation report (template)

**Run mock harness:** `python scripts/run_phase5_eval.py`  
**Run live:** `python scripts/run_phase5_eval.py --live`

## Metrics (fill after run)

| Metric | Mock run | Live run (optional) |
|--------|----------|---------------------|
| Structured output validity rate | | |
| Citation grounding pass rate | | |
| Python compliance pass rate | | |
| Abstention correctness (labelled scenarios) | | |

## Scenarios

Defined in `data/llm/phase5_eval_scenarios.json`. Expand with expert labels over time.

## Limitations

Mock eval validates **deterministic** pipeline wiring, not model reasoning quality. Use live eval for provider quality only with secrets configured.
