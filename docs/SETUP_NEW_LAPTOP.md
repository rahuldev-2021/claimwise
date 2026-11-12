# CLAIMWISE — new laptop setup

Quick checklist to match a full local dev environment (API + UI + Mongo + RAG + financial ML + LiteLLM gateway).

## 1. System software

| Tool | Version | Notes |
|------|---------|--------|
| **Git** | any recent | Clone the repo |
| **Python** | **3.11+** | Required by `backend/pyproject.toml` |
| **Node.js** | **18+** (20 LTS ok) | Frontend (`npm`) |
| **MongoDB** | 6.x or 7.x | Local `mongodb://localhost:27017` (or Atlas URI in `.env`) |

Optional:

- **Network access** to your LLM gateway (`CHATGPT_BASE_URL` / corporate VPN) if not using `LLM_PROVIDER=mock`
- **~2–4 GB disk** for Hugging Face embedding model on first RAG ingest (`all-MiniLM-L6-v2`)

## 2. Get the code

```bash
git clone <your-repo-url> claim_wise
cd claim_wise
```

Copy secrets and gateway settings from your current machine (do **not** commit `.env`):

- `backend/.env`
- `frontend/.env` (if you customized API URL)

Or start from examples:

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

Edit `JWT_SECRET`, bootstrap admin password, and LLM gateway variables.

## 3. MongoDB

**Windows (installer):** install MongoDB Community, run `mongod` as a service.

**Docker:**

```bash
docker run -d --name claimwise-mongo -p 27017:27017 mongo:7
```

First API start creates DB `claimwise` and bootstrap admin (see `AUTH_BOOTSTRAP_*` in `.env`).

## 4. Backend

```bash
cd backend
python -m venv .venv
```

Windows:

```powershell
.venv\Scripts\activate
pip install -U pip
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

macOS/Linux:

```bash
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

Run API:

```bash
python main.py
```

- Health: http://127.0.0.1:8000/health  
- LLM health: http://127.0.0.1:8000/api/v1/llm/health  

Tests (optional):

```bash
pytest -q
```

## 5. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open **the same host you put in `VITE_API_BASE_URL`** (e.g. http://localhost:5173 with `VITE_API_BASE_URL=http://localhost:8000`). Mixing `localhost` and `127.0.0.1` breaks auth cookies.

## 6. Repo data you need (in git)

These ship with the repo — no extra download:

- `backend/data/sample/` — demo claims
- `backend/config/financial/` — financial rules
- `backend/data/financial_models/` — trained ML artifacts (if present in repo)
- RAG builds `backend/data/rag/chroma/` on first ingest (`RAG_STARTUP_INGEST=true`)

## 7. `requirements.txt` vs optional

Everything for the stack you run today is in **`backend/requirements.txt`**:

| Area | Packages |
|------|----------|
| API | fastapi, uvicorn, pydantic, python-multipart, … |
| Auth / DB | pymongo, PyJWT, argon2-cffi |
| RAG | chromadb, rank-bm25, sentence-transformers |
| NLP | spacy (+ `en_core_web_sm` model download) |
| Financial ML | pandas, scikit-learn, joblib, xgboost, numpy |
| LLM | openai, litellm |

Optional providers (not in `requirements.txt`): `google-genai`, `anthropic` — uncomment in file if needed.

`pyproject.toml` `[project.optional-dependencies]` mirrors extras for editable installs: `pip install -e ".[ml,rag,nlp,llm-litellm]"`.

## 8. Minimal “mock LLM” setup

If the other laptop has no gateway:

```env
LLM_PROVIDER=mock
LLM_FALLBACK_PROVIDER=mock
FINANCIAL_REQUIRE_MODELS=false
```

Assessment still runs; LLM advisory uses mocks/templates.

## 9. Troubleshooting

| Symptom | Fix |
|---------|-----|
| Sign-in fails | Mongo running; `MONGODB_URI`; matching localhost/127.0.0.1 on UI + API |
| RAG / ingest slow first time | Normal — downloads embedding model |
| Financial step skipped | `pip install -r requirements.txt`; `FINANCIAL_ENABLED=true` |
| LiteLLM errors | `pip install litellm`; check `CHATGPT_*` and VPN |
| spaCy errors | `python -m spacy download en_core_web_sm` or `NLP_ENABLE_SPACY=false` |
