# Phase 4: Evidence-Based Technical Validation

## Summary

Phase 4 adds a rule-driven technical validation engine that orchestrates existing NLP and RAG outputs, classifies retrieved passages, and returns an auditable `TechnicalValidationResult`. Human reviewers remain in the loop.

**API:** `POST /api/v1/technical-validation/analyze`  
**Auth:** Bearer JWT + `claims:assess`

```json
{
  "claim_id": "CLM-002",
  "top_k": 5,
  "retrieval_mode": "advanced",
  "auto_ingest": false
}
```

| HTTP | Condition |
|------|-----------|
| 401 | Missing/invalid auth |
| 403 | Missing `claims:assess` |
| 200 | Success |
| 404 | Unknown or unauthorized `claim_id` |
| 503 | Empty RAG index and `auto_ingest=false` |

## Result metadata (4.1)

- `validation_id`, `pipeline_version`, `rules_version`, `schema_version`, `input_fingerprint`
- `repair_action_assessments`, `missing_evidence_findings`, `validation_findings`, `contextual_evidence`
- Evidence provenance on each `EvidenceItem` (`evidence_scope`, `evidence_source_type`, optional historical/source ids)

## Confidence methodology

- **Qualitative:** `ConfidenceLevel` (`HIGH` / `MEDIUM` / `LOW` / `INDETERMINATE`) from evidence mix, contradictions, and missing items.
- **Optional numeric:** `confidence` in \[0, 1\] from rule-weighted factors (documented in `confidence_calculator.py`; not statistically calibrated).

## Example (CLM-002, after RAG ingest)

After indexing sample documents, analysis for CLM-002 typically retrieves brake measurement / procedure passages. Status is usually **not** blind `SUPPORTED` unless direct verified evidence aligns with complaint/diagnosis and no blocking rules fire. `human_review_required` stays `true` on uncertain or blocking cases.

## Scenario validation matrix

| ID | Scenario | Result |
|----|----------|--------|
| A | CLM-002 direct / measurement evidence | **PASS** — evidence classified; no unsupported auto-approve |
| B | Suspect diagnosis without direct passages | **PASS** — not `SUPPORTED` without direct support |
| C | Unrelated complaint/diagnosis | **PARTIAL** — rule-based disconnect; no dedicated fixture claim |
| D | Contradiction (voltage vs failure) | **PARTIAL** — detector in unit/integration paths; CLM-004 not dedicated in suite |
| E–G | Heavy repair (CLM-001 engine block) | **PASS** — `NEEDS_REVIEW`, `R_HEAVY_REPAIR_LIGHT_DIAG` |
| K | Empty RAG index | **PASS** — `INSUFFICIENT_EVIDENCE` / 503 |
| M | Unverified documents | **PASS** — quality downrank via rules / quality assessor |
| N | High similarity, contextual only | **PASS** — unit test: high score ≠ `SUPPORTED` |

## Regression

Full backend suite: **≥106 passed** (baseline) plus new TV tests (target **120+** passed).

## Out of scope (Phase 4)

Gemini (`ContextualTechnicalReasoner` protocol stub only), financial ML, recommendation engine, GCP, automatic approve/reject.

## Final phase report

**Overall: PASS** (core engine, API, service orchestration, primary scenarios A/B/E–G/K/N, regression gate). **PARTIAL** on extended fixture scenarios C/D without bespoke claims in the test suite.
