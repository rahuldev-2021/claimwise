# Phase 3 — Data ingestion specification (MVP)

**Status:** Specification for implementation (pre–MVP corpus expansion)  
**Audience:** Engineers implementing ingest, dataset authors, reviewers  
**Related:** [`phase3_rag.md`](phase3_rag.md), [`data/sample/repair_documents.json`](../data/sample/repair_documents.json), [`data/sample/historical_repairs_DQR.md`](../data/sample/historical_repairs_DQR.md)

## 1. Purpose

Ingest **automotive repair knowledge** into the RAG index so that, when a warranty claim arrives, retrieval surfaces evidence that helps a reviewer judge whether the **submitted diagnosis** and **recommended repair** are supported — without deciding approval (Phase 4).

**Principle:** MongoDB (and structured files) hold **canonical records**; ChromaDB holds **searchable chunks + embeddings** only. Never use the vector store as the system of record.

## 2. MVP scope — five source families

| # | Source | MVP role | Sample / gate |
|---|--------|----------|----------------|
| 1 | `repair_documents.json` | Technician/diagnostic reports, parts, labour, short histories | **12 docs today** — extend toward 20–30 procedure/manual-style docs |
| 2 | Repair manuals / procedures | Inspection, removal/install, troubleshooting | Add as `REPAIR_MANUAL` (new type) or enriched `TECHNICIAN_REPORT` with `section_kind` |
| 3 | Parts reference | Part numbers, compatibility, specs | `PART_REFERENCE` (DOC-011 pattern) — target 10–20 |
| 4 | Labour operation reference | Standard times, operation descriptions | `LABOUR_REFERENCE` (DOC-012 pattern) — target 10–20 |
| 5 | `historical_repairs.json` | Structured past cases with provenance | **DQR required** ([`historical_repairs_DQR.md`](../data/sample/historical_repairs_DQR.md)); ingest only after approval |

### Target counts (development, not industry norms)

| Dataset | Initial target |
|---------|----------------|
| Repair manuals / procedures | 20–30 |
| Technician / diagnostic reports | 30–50 |
| Parts reference | 10–20 |
| Labour reference | 10–20 |
| Approved historical repair records | 20–30 |

Use **`synthetic: true`** and clear titles where real OEM PDFs are unavailable.

## 3. What must NOT be ingested into Chroma

| Data | Store elsewhere |
|------|------------------|
| Claim IDs, VIN, customer PII | MongoDB `claims` |
| Claim submission payloads | MongoDB |
| Auth / users | MongoDB |
| Financial training rows, model outputs | CSV / MongoDB / financial service |
| Raw uploaded blobs | `data/uploads/{claim_id}/` + MongoDB `repair_documents` |

Chunks may carry **`claim_id`** only when the source document is already tied to a claim in the corpus (e.g. technician report sample). Do not index live production claims by default.

## 4. Alignment with current codebase

| Your recommendation | Current CLAIMWISE state | Spec action |
|---------------------|-------------------------|-------------|
| Collection `claimwise_repair_knowledge` | `RAG_COLLECTION_NAME=claimwise_rag` | Optional rename via env; one collection for MVP |
| `RepairDocument` JSON ingest | Implemented (`RAGService.ingest`) | Extend schema + metadata |
| Chunk metadata (make, model, category, …) | [`metadata_extractor.py`](../app/modules/rag/metadata_extractor.py) copies scalar fields | Add `synthetic`, `component`, `source_document_ids` |
| `document_type` enum | `TECHNICIAN_REPORT`, `DIAGNOSTIC_REPORT`, `REPAIR_HISTORY`, `PART_REFERENCE`, `LABOUR_REFERENCE` | **Add `REPAIR_MANUAL`** for procedure manuals |
| `historical_repairs.json` | Schema + DQR + unit tests; **not yet RAG-ingested** | New adapter: render narrative `content` + metadata → `RepairDocument` or parallel ingest |
| NLP → RAG | `retrieve_for_claim` + taxonomy query expansion | Filters: `repair_category` (+ configurable make/model/year) |
| Phase 4 consumption | RAG returns `RetrievalResult` + citations | Unchanged |

## 5. Canonical document model (`RepairDocument`)

**Authoritative store:** JSON sample file and/or MongoDB `repair_documents` collection (upload pipeline).

### 5.1 Required fields

| Field | Type | Notes |
|-------|------|-------|
| `document_id` | string | Stable, e.g. `DOC-013` |
| `document_type` | enum | See §6 |
| `title` | string | Human-readable |
| `content` | string | Full text to chunk (Markdown/plain) |
| `verification_status` | `VERIFIED` \| `UNVERIFIED` \| `PENDING` | Passed through to citations |
| `created_at` | ISO-8601 TZ-aware | Provenance |

### 5.2 Optional fields (recommended for filtering)

| Field | Type | Filter use |
|-------|------|------------|
| `claim_id` | string \| null | Linkage only; not used as mandatory RAG filter |
| `vehicle_make` | string \| null | Hard filter when set on claim config |
| `vehicle_model` | string \| null | Hard filter when set |
| `model_year` | int \| null | Hard filter when set |
| `repair_category` | string \| null | **Primary** filter (e.g. `BRAKING`) |
| `part_number` | string \| null | Soft signal in query expansion |
| `repair_outcome` | string \| null | Historical / outcome narratives |

### 5.3 Fields to add (MVP extension)

| Field | Type | Notes |
|-------|------|-------|
| `synthetic` | bool, default `false` | `true` for sample/OEM-substitute content |
| `component` | string \| null | Taxonomy canonical, e.g. `brake_pad` — soft retrieval |
| `source_document_ids` | list[string] \| null | For docs derived from others |
| `section_kind` | string \| null | Optional: `inspection` \| `removal_install` \| `troubleshooting` |

Implement in [`app/schemas/repair_document.py`](../app/schemas/repair_document.py) and extend `_OPTIONAL_FIELDS` in `metadata_extractor.py` (Chroma-safe scalars only).

## 6. Document types

| `document_type` | Your category | Ingest? | Example |
|-----------------|---------------|---------|---------|
| `REPAIR_MANUAL` | Repair manuals | Yes | Brake pad R&R procedure |
| `TECHNICIAN_REPORT` | Technician diagnostic reports | Yes | DOC-002 F-150 brakes |
| `DIAGNOSTIC_REPORT` | Diagnostic reports / DTC context | Yes | DOC-003 cooling |
| `PART_REFERENCE` | Parts / component reference | Yes | DOC-011 |
| `LABOUR_REFERENCE` | Labour operations | Yes | DOC-012 |
| `REPAIR_HISTORY` | Narrative historical case in doc corpus | Yes | DOC-009/010 |
| *(from historical JSON)* | Structured historical repairs | Yes, via adapter | `HR-002` → searchable narrative |

**Historical repair rules (MVP):**

- Ingest only rows that pass DQR and eligibility (completed repair with explicit `actual_repair_performed` provenance).
- Never index `recommended_repair` as `actual_repair_performed` without `field_provenance.explicit`.
- Set `synthetic: true` for sample-derived rows until replaced by verified OEM/dealer data.

## 7. Vector index — chunk model

### 7.1 Collection

- **Name:** `claimwise_repair_knowledge` (recommended) or keep `claimwise_rag` via `RAG_COLLECTION_NAME`.
- **Path:** `RAG_PERSIST_DIR` (default `data/rag/chroma`).

### 7.2 Chunk identity

- **Format:** `{document_id}::chunk-{index:04d}` (deterministic; idempotent re-ingest).
- **Embedded text:** Normalized chunk body (see [`document_cleaner.py`](../app/modules/rag/document_cleaner.py)).
- **Parent window:** For docs longer than `parent_chunk_size`, attach `parent_text` (already implemented).

### 7.3 Chunk metadata (stored in Chroma)

Minimum set (implemented + extensions):

```json
{
  "chunk_id": "DOC-002::chunk-0000",
  "document_id": "DOC-002",
  "chunk_index": 0,
  "document_type": "TECHNICIAN_REPORT",
  "vehicle_make": "Ford",
  "vehicle_model": "F-150",
  "model_year": 2023,
  "repair_category": "BRAKING",
  "part_number": "HL3Z-2001-D",
  "verification_status": "VERIFIED",
  "synthetic": true,
  "component": "brake_pad",
  "created_at": "2026-09-16T13:30:00Z"
}
```

Do **not** store full `source_text` in metadata — it lives in the chunk body. Citations return `document_id`, `chunk_id`, `title`, `document_type`, `verification_status`.

### 7.4 Chunking rules

| Setting | Default | Manuals / long docs |
|---------|---------|---------------------|
| `RAG_CHUNK_SIZE` | 500 chars | 400–600; prefer paragraph boundaries |
| `RAG_CHUNK_OVERLAP` | 100 | 80–120 |
| `parent_chunk_size` | 1000 | Enable for multi-section manuals |

**Structure-aware splitting:** Paragraph → sentence → clause (see [`chunking.py`](../app/modules/rag/chunking.py)).

**Procedure docs:** Prefer chunk boundaries at numbered steps and headings (future: preprocessor for OEM PDF/DOCX).

**Empty / duplicate:** Skip blank content; `SKIPPED_DUPLICATE` on re-ingest same `document_id` without `force_reindex`.

## 8. Ingestion pipeline (implementation checklist)

1. **Load** — `repair_documents.json` and/or MongoDB repository (`SampleRepairDocumentRepository` / `MongoRepairDocumentRepository`).
2. **Validate** — Pydantic `RepairDocument`; reject unknown types after enum extension.
3. **Clean** — Normalize whitespace, encoding (`document_cleaner`).
4. **Metadata** — `extract_metadata(doc)` + `chunk_index` at chunk time.
5. **Chunk** — `RecursiveChunker.chunk_document`.
6. **Embed** — `EmbeddingProvider` (`all-MiniLM-L6-v2` when `[rag]` installed).
7. **Upsert** — ChromaDB + rebuild BM25 lexical index.
8. **Historical adapter (new)** — For each approved `HistoricalRepair`, build:

   ```text
   title: "Historical repair {historical_repair_id} – {vehicle_make} {vehicle_model}"
   document_type: REPAIR_HISTORY
   content: complaint + diagnosis + actual_repair_performed + outcome (no invented fields)
   metadata: historical_repair_id, source_document_ids, synthetic, field_provenance as JSON string or omitted
   ```

9. **API** — `POST /api/v1/rag/ingest` with `force_reindex` for rebuild.

## 9. Retrieval integration (Phase 2 → 3)

**Input:** `ClaimInput` + `NLPAnalysisResult` (Phase 2).

**Query construction (existing):** Symptoms, components, repair category, taxonomy expansions.

**Metadata filters (existing + config):**

- **Hard (when present on claim):** `repair_category`, optionally `vehicle_make`, `vehicle_model`, `model_year` (`RAG_CLAIM_HARD_FILTER_FIELDS`).
- **Soft (no Chroma `where`):** DTCs, failure modes, `component` — boost via query terms only.

**Fallback:** If filtered retrieval returns fewer than `RAG_MIN_PASSAGES_FALLBACK`, relax filters (`filter_fallback_applied=true`).

**Example (F-150 braking claim):** Should retrieve DOC-002, DOC-012, part/labour refs, and HR braking row once ingested — not approve the claim.

## 10. Data quality gates before ingest

### 10.1 `repair_documents.json`

- Unique `document_id`.
- Non-empty `content`.
- `repair_category` set when document is category-specific.
- Manuals: `synthetic` + OEM/source attribution in `title` or preamble in `content`.

### 10.2 `historical_repairs.json`

- Complete DQR sign-off ([`historical_repairs_DQR.md`](../data/sample/historical_repairs_DQR.md)).
- Resolve DOC-008 / DOC-010 `claim_id` clash before adding new HR rows.
- No `recommended_repair` indexed as performed without provenance.

## 11. MVP corpus expansion order

1. **Braking vertical slice** — Align with Ford F-150 sample claims (CLM-002, CLM-0016 pattern):
   - 3–5 `REPAIR_MANUAL` chunks (pad measure, rotor measure, R&R).
   - Keep DOC-002, add 2–3 more technician reports.
   - DOC-012 labour; add 1–2 parts refs (`brake_pad`, `brake_rotor`).
   - Ingest approved `HR-002` (+ future HR braking rows).

2. **Cross-category** — Engine/cooling/electrical samples already in JSON; grow to target counts.

3. **Evaluation** — Extend [`data/rag/evaluation_queries.json`](../data/rag/evaluation_queries.json) with labelled `relevant_chunk_ids` per new doc.

## 12. Explicit non-goals (this spec)

- PDF/DOCX parsers (interface exists; JSON MVP first).
- Vertex / managed vector DB (migration seam documented in `phase3_rag.md`).
- Automatic ingestion of live claim uploads into global Chroma (claim-scoped docs stay Mongo + optional per-claim index later).

## 13. Acceptance criteria

- [ ] `REPAIR_MANUAL` + `synthetic` + `component` on schema and Chroma metadata.
- [ ] Corpus meets §2 targets for **at least one** repair category (braking).
- [ ] `historical_repairs.json` ingested only after DQR approval; citations show `synthetic` and `source_document_ids`.
- [ ] `retrieve-for-claim` for CLM-0016 returns ≥2 braking-relevant passages with correct `verification_status`.
- [ ] No customer PII or financial training data in Chroma.
- [ ] Re-ingest is idempotent; `force_reindex` rebuilds BM25 + vectors.

---

**Next implementation PR (suggested):** Schema extension → metadata extractor → 5–10 synthetic `REPAIR_MANUAL` JSON entries → historical ingest adapter → evaluation query labels → optional `RAG_COLLECTION_NAME=claimwise_repair_knowledge`.
