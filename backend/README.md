# CLAIMWISE

**AI-Driven Automotive Repair Claim Validation and Decision Support System**

Smarter validation. Evidence-driven decisions.

## Business Problem

Automotive warranty claim reviewers evaluate whether a technician's recommended repair is supported by the customer complaint and diagnosis, and whether the submitted parts cost and labour hours are reasonable. CLAIMWISE assists reviewers by combining NLP, RAG, ML, and Gemini into a single evidence-based recommendation, while keeping the final decision with the human agent.

This is an educational project using synthetic data. It is not an official automotive manufacturer product.

## Current Status: Phase 7A (backend + reviewer UI)

**Phase 1** (complete): schemas, sample data, repository, health API.

**Phase 2 / 2.1** (complete): NLP pipeline `POST /api/v1/nlp/analyze` (rules, regex, fuzzy matching, optional spaCy).

**Phase 3** (complete): RAG ingestion + hybrid retrieval, ChromaDB vector store, BM25 + RRF, evaluation harness, APIs:

- `POST /api/v1/rag/ingest`
- `POST /api/v1/rag/search`
- `POST /api/v1/rag/retrieve-for-claim`
- `GET /api/v1/rag/health`
- `POST /api/v1/rag/evaluate`

**Phase 4** (complete): Evidence-based technical validation — rule engine, passage classification, confidence, human-review flags:

- `POST /api/v1/technical-validation/analyze`

**Phase 5** (complete): Model-agnostic LLM layer, contextual assessment (advisory), Python recommendation engine, full assessment workflow:

- `POST /api/v1/assessment/analyze`
- `GET /api/v1/llm/health`

See [`docs/phase5_llm_assessment.md`](docs/phase5_llm_assessment.md) and [`docs/llm_provider_guide.md`](docs/llm_provider_guide.md).

**Phase 7A** (complete): Reviewer dashboard (React) + claims/feedback APIs + CORS:

- `GET /api/v1/claims`, `GET /api/v1/claims/{claim_id}`
- `POST /api/v1/reviewer-feedback`, `GET /api/v1/reviewer-feedback/{claim_id}`

Frontend: [`../frontend/README.md`](../frontend/README.md). Docs: [`docs/phase7a_dashboard.md`](docs/phase7a_dashboard.md).

**CORS:** set `CORS_ORIGINS` (default includes `http://localhost:5173`).

**Tests:** 151+ backend tests passed. Frontend: `cd frontend && npm test`.

**Phase 6** (in progress): Financial validation module, PROVISIONAL config, APIs, and Phase 5 assessment wiring. ML training on the approved dataset is **pending**. See [`docs/phase6_financial_validation.md`](docs/phase6_financial_validation.md).

GCP deployment is not yet implemented.

## Technology Stack

- Python 3.11+
- FastAPI
- Pydantic v2 and Pydantic Settings
- Pytest
- Uvicorn

## Project Structure

```
claim_wise/
    app/
        main.py                          # FastAPI entry point
        api/routes/health.py             # GET /health
        core/
            config.py                    # Pydantic Settings
            logging_config.py            # Structured logging
            exceptions.py                # Application exceptions
        schemas/                         # All Pydantic data contracts
            vehicle.py
            repair.py
            claim.py
            repair_document.py
            technical_validation.py
            financial_validation.py
            recommendation.py
        services/
            interfaces.py                # Module Protocols (NLP, RAG, etc.)
            claim_service.py             # Service layer
        modules/                         # Future module implementations
            nlp/
            rag/
            technical_validation/
            financial_validation/
            recommendation/
        repositories/
            sample_claim_repository.py   # JSON file repository
    data/sample/                         # Synthetic test data
    tests/
        unit/                            # Schema and repository tests
        integration/                     # API tests
    docs/                                # Architecture and design docs
    architecture/                        # draw.io diagram
```

## Setup

```bash
# Create and activate a virtual environment
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

# Install core dependencies (rules, regex, fuzzy matching)
pip install -r requirements.txt

# Optional: spaCy noun-chunk hints (NLP — failure never blocks claims)
python -m pip install "spacy>=3.7,<4"
python -m spacy download en_core_web_sm
# Or: pip install -e ".[nlp]" when editable install is configured

# Optional: sentence-transformers for RAG semantic embeddings
pip install -e ".[rag]"
```

Copy `.env.example` to `.env` and adjust values if needed:

```bash
cp .env.example .env
```

## Running the Application

```bash
python main.py
```

Host/port come from `.env`: `HOST=127.0.0.1`, `PORT=8000`.

Equivalent: `uvicorn main:app --reload --host 127.0.0.1 --port 8000`

- Health: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)
- NLP analyze: `POST http://127.0.0.1:8000/api/v1/nlp/analyze` with body `{"claim_id": "CLM-001"}`

See [docs/phase2_nlp.md](docs/phase2_nlp.md) for workflow and limitations.

## Running Tests

```bash
pytest -v
```

## Future Roadmap

| Phase | Scope |
|-------|-------|
| 1 | Project foundation and data contracts (complete) |
| 2 | NLP pipeline: structured extraction (complete) |
| 3 | RAG: historical case retrieval with hybrid search |
| 4 | Technical repair validation |
| 5 | ML cost and labour prediction |
| 6 | Business rules engine |
| 7 | Recommendation engine |
| 8 | Gemini integration for structured explanations |
| 9 | API and claims agent dashboard |
| 10 | GCP deployment, monitoring, and feedback loop |

## License

Educational project. Not for production use.
