# Phase 4 — Existing implementation audit

**Date:** 2026-03-12  
**Purpose:** Step 0 baseline before refinement (per Phase 4 completion plan).  
**Classification key:** IMPLEMENTED | PARTIAL | MISSING | NEEDS_REFINEMENT | NOT_APPLICABLE

---

## 1. Module map

| Module | Path | Responsibility |
|--------|------|----------------|
| Pipeline | `app/modules/technical_validation/technical_validation_pipeline.py` | Pure orchestration → `TechnicalValidationResult` |
| Complaint–diagnosis | `complaint_diagnosis_validator.py` | `ConsistencyLevel` from NLP + heuristics |
| Repair justification | `repair_justification_validator.py` | Single summary + heavy/light mismatch |
| Diagnostic evidence | `diagnostic_evidence_validator.py` | Passage classification + quality_score |
| Contradictions | `contradiction_detector.py` | Symptom + voltage vs failure patterns |
| Missing evidence | `missing_evidence_detector.py` | `list[str]` messages |
| Evidence quality | `evidence_quality_assessor.py` | Text summary only |
| Rules | `validation_rules.py` | Status aggregation (hardcoded rules) |
| Confidence | `confidence_calculator.py` | Qualitative + numeric heuristic |
| Service | `app/services/technical_validation_service.py` | NLP + RAG + `validate_technical` |
| API | `app/api/routes/technical_validation.py` | `POST /technical-validation/analyze` |
| Schemas (public) | `app/schemas/technical_validation.py` | Result + `EvidenceItem` |
| Internal DTOs | `app/modules/technical_validation/schemas.py` | `ValidationContext`, `ClassifiedEvidence` |

---

## 2. API / auth matrix (Refinement 1)

| Entry point | Returns / runs TV | Auth (pre-fix) | Org-scoped claim load |
|-------------|-------------------|----------------|------------------------|
| `POST /api/v1/technical-validation/analyze` | Yes | **None** | **No** (`ClaimService.get_claim`) |
| `POST /api/v1/assessment/analyze` | Yes (embedded) | **None** | **No** |
| Investigation worker | Persists on claim | Job `org_id` | Yes |
| `GET /api/v1/claims/{id}` | ClaimInput only | `claims:read` | Yes |
| `GET /api/v1/claims/{id}/processing-status` | Status only | `claims:read` | Yes |
| RAG `retrieve-for-claim` | Upstream of TV | **None** | **No access context** |

**Security gap:** TV and assessment analyze endpoints are **unauthenticated** and use unscoped claim resolution. **Track S** required before external exposure.

---

## 3. Requirement matrix (spec §5–§14)

| Requirement | Status | Notes |
|-------------|--------|-------|
| Single deterministic pipeline, no LLM in P4 | IMPLEMENTED | |
| `analyze_with_context` | IMPLEMENTED | Worker uses it |
| Technical status enums | IMPLEMENTED | |
| `human_review_required` default | IMPLEMENTED | Rules tighten SUPPORTED |
| Complaint–diagnosis (§5) | PARTIAL | NLP comparison; limited polarity/certainty |
| Diagnostic evidence (§6) | PARTIAL | Regex/heuristics; trust caps partial |
| Per repair operation justification (§7) | MISSING | One summary only |
| Contradictions (§8) | PARTIAL | Few coded patterns |
| Missing evidence structured scopes (§9) | MISSING | Strings only |
| Repair scope validator (§10) | PARTIAL | `R_HEAVY_REPAIR_LIGHT_DIAG` only |
| Central trust policy (§11) | NEEDS_REFINEMENT | Split across classifier |
| Status aggregation (§12) | PARTIAL | `apply_rules` only |
| `ValidationFinding` model (§4.3) | MISSING | `ContradictionFinding` internal only |
| `validation_id`, rules/pipeline version, fingerprint (§4, §14) | MISSING | `generated_at` only |
| Full EvidenceItem provenance (§4.2) | PARTIAL | Added `evidence_source_type`; scope/historical ids missing |
| Rule registry + versioning (§14) | NEEDS_REFINEMENT | Python list in `validation_rules.py` |
| API auth (§13) | MISSING | |
| Persistence metadata (§17) | PARTIAL | On `PersistedClaim` without fingerprint |
| Phase 5 contract | IMPLEMENTED | Uses existing `TechnicalValidationResult` fields |

---

## 4. Overlap / duplication

- Complaint negation checked in both `complaint_diagnosis_validator` and `contradiction_detector`.
- `quality_score` and `retrieval_score` separated in schema; rules sometimes conflate via `relevance_score` alias on `EvidenceItem`.
- Status set only in `apply_rules` (good); validators do not assign final status (good).

---

## 5. Schema compatibility

- **Frontend:** `frontend/src/api/types/assessment.ts` expects `technical_validation` with string `missing_evidence[]` — keep for backward compatibility.
- **Phase 5:** `contextual_input_builder.py` reads summaries and evidence lists — additive fields safe if optional.

---

## 6. Tests

| Area | Files | Gap |
|------|-------|-----|
| Rules | `test_tv_rules.py` | No per-action repair tests |
| Classification | `test_tv_classification.py` | |
| Integration | `test_technical_validation.py`, `test_technical_validation_api.py` | No auth; no provenance E2E |
| Scenarios §21.4 (20) | Partial in `phase4_technical_validation.md` | ~8 covered |

---

## 7. Recommended minimal changes (execution order)

1. **Track S** — Auth + `get_claim_for_user` + RAG `RetrievalAccessContext` on API paths.
2. **Schemas** — Additive: `ValidationFinding`, `RepairActionAssessment`, `MissingEvidenceFinding`, versions, fingerprint, provenance on `EvidenceItem`.
3. **Trust policy** — Multi-dimensional `EvidenceTrustDimensions`; rules read dimensions.
4. **Validators** — Repair action linker; missing evidence scopes; `repair_scope_validator.py`.
5. **Registry + aggregator** — Split detection vs aggregation; stamp `rules_version`.
6. **Fingerprint** — Idempotent TV reuse in investigation.
7. **Tests + docs** — Auth tests, provenance test, evaluation report template.

---

## 8. Final pre-implementation classification summary

| Area | Count |
|------|-------|
| IMPLEMENTED | Core pipeline, service, statuses, worker integration |
| PARTIAL | Validators, evidence, API security, persistence |
| MISSING | Per-action repair, structured findings, fingerprint, eval metrics |
| NEEDS_REFINEMENT | Trust policy, rule registry, aggregation narrative |

**Recommendation:** Proceed with Track S immediately, then Phase 4A additive schema + validators, then Phase 4B eval/security docs. **Do not** add a second pipeline or LLM to Phase 4.
