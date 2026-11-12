# NLP Module (Phase 2 / 2.1)

Converts unstructured warranty claim text into structured entities using **rule-based and regex extraction**, optional **fuzzy taxonomy matching**, and optional **spaCy** noun-chunk hints. This is not a trained domain ML model.

## Pipeline stages

1. **preprocessing** – whitespace and punctuation normalization; **normalized text is lowercased**; originals preserved unchanged on the API response.
2. **entity_extractor** – exact alias matching, fuzzy fallback, DTC/voltage/temperature/mileage regex, optional `en_core_web_sm` noun chunks.
3. **fuzzy_matcher** – `difflib` similarity against taxonomy aliases when exact match fails (`NLP_FUZZY_MATCH_THRESHOLD` in settings).
4. **taxonomy** / **taxonomy_data** – alias → canonical maps including `failure_mode` (separate from `symptom`).
5. **information_extractor** – per-field extractions for complaint, diagnosis, and recommended repair.
6. **missing_information** – review suggestions only (not auto-rejection).
7. **complaint_diagnosis_matcher** – overlap and scope hints; does not declare repairs valid or invalid.
8. **relationship_extractor** / **alignment_hints** – provenance-backed links and `repair_alignment_hints` (observations only).
9. **entity_confidence** – confirmed vs heuristic (`spacy_heuristic`) tiers for comparisons and Phase 4 inputs.
10. **pipeline** (`NLPPipeline`, v0.4.0) – deterministic path; optional spaCy; optional LLM fallback via `build_nlp_pipeline(settings)`.
11. **llm_contextual_provider** – conditional LLM enrichment (`LLM_NLP_ENABLED=false` by default).

## Semantics: symptom vs failure mode

| Concept | Source | Notes |
|---------|--------|-------|
| Symptom | Customer complaint | What the driver experiences (e.g. `abnormal_noise`). |
| Component / part | Complaint or diagnosis | Vehicle system or physical part. |
| Failure mode | Complaint or diagnosis | Specific degradation only when failure-mode taxonomy matches; **never copied from symptom**. |
| Diagnostic | Technician text | Inspection / test findings. |

`structured_extraction.failure_mode` is `null` when not established.

## Entity match metadata

Each `ExtractedEntity` includes `match_method`: `exact` (regex measurements/DTC), `alias` (taxonomy hit), or `fuzzy`.

## Optional spaCy setup

Core install (rules/regex/fuzzy only) never requires spaCy:

```bash
pip install -r requirements.txt
```

Optional noun-chunk hints (install only if you want them):

```bash
pip install -e ".[nlp]"
python -m spacy download en_core_web_sm
```

Behavior:

- Missing package or model: pipeline continues; `spacy_available` is `false`; intake and claims are **not** blocked.
- Runtime spaCy errors: logged as warnings; deterministic extraction still completes.
- `NLP_ENABLE_SPACY=false` in `.env` disables spaCy even when installed (useful for CI or debugging parity).

A missing `spacy` package is **normal** for the default install — it is not an application failure.

## Entity tiers

- **Confirmed:** taxonomy, regex, rule_based, fuzzy — used for `complaint_diagnosis_comparison`, structured extraction, relationship `affects`, alignment hints, LLM fallback triggers.
- **Heuristic:** `spacy_heuristic` — retained in `field_extractions` for debugging only.
- **LLM:** `extraction_method=llm` with `llm_reconciled=true` after validation/reconcile.

## Optional LLM NLP fallback (Phase 2.2)

Set `LLM_NLP_ENABLED=true` and configure Phase 5 provider keys. Uses `LLM_NLP_*` env vars (see `.env.example`). Fallback decision metadata is always attached via `processing_metadata.llm_fallback` when using `build_nlp_pipeline`.

## API

`POST /api/v1/nlp/analyze` with `{"claim_id": "CLM-001"}` or an inline `claim` payload.

## Known limitations

- English-only taxonomy; fuzzy matching can still miss rare misspellings or over-match short tokens if threshold is lowered.
- Temperature regex requires an explicit `C`/`F` (or `°`) unit.
- LLM fallback is observational only; does not set technical or approval status.
