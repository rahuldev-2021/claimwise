# Phase 2 – NLP Pipeline (v0.4.0 / Phase 2.2)

## Workflow

```
ClaimInput (immutable)
  → preprocessing (lowercased normalized copy; original preserved)
  → entity extraction (rules + regex + fuzzy aliases + optional spaCy)
  → taxonomy normalization
  → field extractions (complaint | diagnosis | recommended_repair)
  → missing information suggestions
  → complaint–diagnosis comparison (review hints)
  → relationship extraction + repair_alignment_hints (observations only)
  → fallback decision metadata (always when using build_nlp_pipeline)
  → optional LLM contextual enrich [LLM_NLP_ENABLED=false default]
  → NLPAnalysisResult v0.4.0
```

## Shared extraction block

`structured_extraction` fields align with the architecture extraction schema used for RAG in Phase 3:

| Field | Meaning |
|-------|---------|
| symptom | Canonical symptom from complaint |
| component | Primary component |
| failure_mode | Canonical failure mode **only** when failure-mode taxonomy matches; not inferred from symptom |
| repair_action | Canonical repair verb or action |
| part_number | From claim repair record |

## Phase 2.1 changes

- Lowercase normalized complaint/diagnosis/repair text for matching.
- Fuzzy alias matching after exact taxonomy pass (`match_method` on entities).
- Temperature measurements (°C / °F) via regex.
- spaCy moved to optional `pip install -e ".[nlp]"` extra.
- Narrower service-layer errors (unexpected exceptions propagate).
- `ContextualExtractionProvider` Protocol for future Gemini integration (no SDK in this phase).

## API example

```bash
curl -X POST http://127.0.0.1:8000/api/v1/nlp/analyze \
  -H "Content-Type: application/json" \
  -d "{\"claim_id\": \"CLM-001\"}"
```

Response includes normalized repair text, `entity_relationships`, `repair_alignment_hints` (all `requires_validation: true`), and `structured_extraction` (`processing_metadata.pipeline_version` = `0.3.0`). NLP does not set technical status or `human_review_required` (Phase 4).

### Representative output (CLM-001)

- Symptom: `abnormal_noise`
- Component: `engine` / `timing_chain` context from text
- Failure mode: `null` (noise symptom does not imply a failure mode)
- Comparison note: recommended engine block vs timing-chain-oriented diagnosis
- Original complaint text unchanged in `original_complaint`

## Limitations

- English-only, synthetic-data-oriented taxonomy.
- Rule coverage gaps for uncommon phrasing; unknown terms are slugified or omitted from structured fields.
- spaCy `en_core_web_sm` is general English, not automotive fine-tuned.
- No repair validity decision in Phase 2 (reserved for Phase 4).
- No LLM calls in Phase 2.1.

## Future integration

- Phase 3: embed `structured_extraction` + normalized text for vector search.
- Contextual provider: Gemini for ambiguous descriptions after deterministic extraction.
- Phase 4: technical validation consumes `complaint_diagnosis_comparison` and extractions.
