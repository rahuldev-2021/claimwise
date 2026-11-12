# CLAIMWISE Architecture

## Overview

CLAIMWISE processes two types of data through independent validation paths:

- **Structured data** (parts cost, labour hours, vehicle, dealer, region, outcome) feeds the financial validation module and ML cost model.
- **Unstructured text** (customer complaint, technician diagnosis, recommended repair) feeds the NLP pipeline, RAG retrieval, and technical validation module.

Both paths produce separate results. A rule engine combines them into one recommendation. The claims agent makes the final decision.

## Data Flow

```
Dealer claim submission
    |
    v
NLP Extraction (shared schema)
    |
    +---> Structured features ---> Financial Validation (ML + catalogue baseline)
    |
    +---> Embedded text ---------> RAG Retrieval (similar historical cases)
                                       |
                                       v
                                 Technical Validation (repair-fit check)
    |
    v
Rule Engine (combines both verdicts + thresholds)
    |
    v
Recommendation (with Gemini explanation)
    |
    v
Claims Agent Workbench (human-in-the-loop)
    |
    v
Feedback stored (agent decisions become training labels)
```

## Module Responsibilities

### NLP Module (implemented – Phase 2 / 2.1)
Extracts structured information from free-text claim fields using a shared extraction schema (symptom, component, failure_mode, repair_action, part_number). Implemented in `app/modules/nlp/` with deterministic rule/regex extraction, fuzzy taxonomy fallback, and optional spaCy noun chunks (`pip install -e ".[nlp]"`). Normalized text is lowercased for matching; originals are preserved on the API response. `failure_mode` is distinct from `symptom` and is only set when failure-mode taxonomy aliases match. `NLPPipeline` accepts an optional `ContextualExtractionProvider` for future LLM enrichment (not wired in Phase 2.1). Exposed via `POST /api/v1/nlp/analyze`. Historical batch extraction for indexing remains a Phase 3 concern.

### RAG Module (implemented – Phase 3)
Ingests `RepairDocument` records from the sample repository into ChromaDB (persistent `data/rag/chroma`) with `sentence-transformers` embeddings (`all-MiniLM-L6-v2`, optional `[rag]` extra) and an in-memory BM25 index. Retrieval modes: **basic** (semantic) and **advanced** (hybrid semantic + BM25 fused with RRF). Query construction reuses NLP output and taxonomy expansion for claim-based search. Responses are `RetrievalResult` objects with cited passages (document id, chunk id, title, verification status, scores). Exposed via `POST /api/v1/rag/ingest`, `search`, `retrieve-for-claim`, and `GET /api/v1/rag/health`. Evidence is for review only — RAG does not validate repairs (Phase 4). `VectorStore` / `EmbeddingProvider` protocols are the seam for Vertex AI later.

### Technical Validation Module (implemented – Phase 4)
Deterministic pipeline in `app/modules/technical_validation/` classifies `RetrievedPassage` evidence (direct vs historical vs contextual), detects contradictions and missing diagnostics, and applies configurable rules to produce `TechnicalValidationResult`. Orchestrated by `TechnicalValidationService` (NLP + RAG + pipeline). Exposed via `POST /api/v1/technical-validation/analyze`. Retrieval scores are stored separately from evidence quality. `human_review_required` defaults to true. Does not call Gemini or auto-approve claims. See [`docs/phase4_technical_validation.md`](phase4_technical_validation.md).

### Financial Validation Module (Phase 6 — in progress)
Configuration-driven dual regressors (parts cost, labour hours) with PROVISIONAL rules in `config/financial/`. APIs under `/api/v1/financial-validation/*`; wired into `POST /api/v1/assessment/analyze`. Training is offline; approved dataset required for production models. See [`docs/phase6_financial_validation.md`](phase6_financial_validation.md).

### LLM Module (implemented – Phase 5)
Provider-agnostic contextual reasoning in `app/modules/llm/`: factory, adapters (`gemini`, `openai`, `anthropic`, `ollama`, `mock`), orchestrator, prompt templates, and grounding validation. LLM output does not override Phase 4 technical validation. `GET /api/v1/llm/health`.

### Reviewer UI (implemented – Phase 7A)
React/Vite dashboard in `frontend/` integrates with claims list, full assessment, and reviewer feedback APIs. Financial validation UI is a Phase 6 placeholder. See [`docs/phase7a_dashboard.md`](phase7a_dashboard.md).

### Recommendation Module (implemented – Phase 5)
Python business rules in `app/modules/recommendation/` combine technical validation and optional LLM advisory input into `ClaimRecommendation`. Financial assessment remains `PENDING` until Phase 6. Full workflow: `POST /api/v1/assessment/analyze`. The system never approves or rejects a claim automatically.

## Two Separate Checks

1. **Repair-fit check:** Does the complaint and diagnosis support this repair, or does the evidence point to a smaller one?
2. **Price check:** Is the submitted cost reasonable for the repair the technician actually submitted?

These are kept separate throughout the pipeline and combined only in the rule engine.

## Future GCP Architecture

When deployed, the system will use:

- **Cloud Run** for FastAPI services
- **BigQuery** for structured claim data and predictions
- **Cloud Storage** for documents and model artifacts
- **Vertex AI** for Gemini, embeddings, Vector Search, and ML model management
- **Pub/Sub + Dataflow** for claim ingestion
- **Sensitive Data Protection (DLP)** for de-identifying free text
- **IAM, CMEK, VPC Service Controls** for security
- **Cloud Monitoring and Audit Logs** for observability

The detailed GCP architecture is in [`architecture/claimwise_architecture.drawio`](../architecture/claimwise_architecture.drawio).

Phase 1 runs entirely locally without GCP credentials.
