# Nebraska Pork Compliance Copilot

An evidence-constrained compliance assistant for Nebraska pork producers. The static Next.js frontend is designed for FTP hosting at `wayan.com/copilot/`. The FastAPI backend runs on Render with Neon Postgres and pgvector.

## What producers receive

The copilot answers natural-language questions about Nebraska livestock-waste permits, manure management, animal health, labor, worker safety, and destination-market requirements. Each supported claim links to the source excerpt used to make it. Missing farm facts, conflicting authorities, and missing evidence remain visible.

The approved corpus prioritizes the Nebraska Department of Water, Energy, and Environment, Nebraska Department of Agriculture, Nebraska Legislature, Nebraska Department of Labor, Nebraska Extension, USDA APHIS, U.S. Department of Labor, OSHA, FDA, and other official sources that apply to Nebraska operations.

## Trust controls

- Answers use only retrieved excerpts from the approved registry.
- The model may cite only server-issued chunk IDs, which the API resolves to source links.
- Uncited claims are removed before the answer reaches the producer.
- Statutes and regulations are distinguished from guidance and recommended practice.
- Applicability is reported as high, medium, low, or unknown with an explanation.
- Farm facts are user context, never regulatory evidence.
- A source gap produces an explicit inability to verify rather than a guessed answer.

This is compliance decision support, not legal advice or veterinary diagnosis.

## Repository layout

- `frontend/`: static Next.js frontend
- `backend/`: FastAPI API, ingestion, hybrid retrieval, database schema, tests, and evaluation questions
- `backend/app/source_registry.py`: approved Nebraska-first source registry
- `backend/corpus/manual/`: reproducible copies of official PDFs
- `render.yaml`: Render service definition

## Local setup

```bash
cd backend
python3.12 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
python -m app.ingest --seed-if-empty
uvicorn app.main:app --reload --port 8000
```

```bash
cd frontend
cp .env.example .env.local
npm install
npm run dev
```

No API key is shipped to the browser. Set `NEXT_PUBLIC_API_BASE_URL` to the Render API URL before the static production build.

## Corpus migration and updates

After approving embedding charges, use the sync mode when changing jurisdictions:

```bash
python -m app.ingest --sync
```

The command ingests the registered Nebraska and applicable federal sources, then removes database documents that are no longer approved. It only prunes the old corpus if every registered source completes without an ingestion failure.

## API

- `POST /api/chat`: retrieve evidence and return a cited answer
- `GET /api/sources`: list active corpus sources
- `GET /api/updates`: list sources with distinct stored versions
- `POST /api/feedback`: record answer feedback
- `POST /api/bookmarks`: save an answer
- `GET /api/conversations/{id}`: retrieve conversation history
- `GET /api/admin/summary`: corpus and usage health, protected by `X-Admin-Key`
- `GET /healthz`: service, database, jurisdiction, and corpus status
