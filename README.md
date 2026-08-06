# Iowa Pork Compliance Copilot

An evidence-constrained compliance assistant for Iowa pork producers. The frontend exports to static files for FTP hosting. The FastAPI backend runs on Render with Neon Postgres and pgvector.

## Trust controls

- Answers are generated only from retrieved, approved-source excerpts.
- The model may cite only server-issued chunk IDs. The API resolves those IDs to official URLs.
- Every answer claim has citations or is rejected.
- Conflicting evidence is preserved and disclosed.
- Retrieved pages are treated as untrusted data, so document text cannot override system instructions.
- Low-evidence questions return an explicit inability to verify, not a guessed answer.
- Applicability uses `high`, `medium`, `low`, or `unknown`, never a numeric score.
- Missing source evidence is distinguished from missing farm facts.
- Optional farm context is user-provided context, never regulatory evidence.

This is decision support, not legal, veterinary, or emergency advice.

## Repository layout

- `frontend/`: Next.js app configured for static export to `frontend/out/`
- `backend/`: FastAPI API, Postgres schema, hybrid retrieval, ingestion, and tests
- `render.yaml`: Render Blueprint for the API

## Local setup

### Backend

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

The root `.env.local` created by Codex is intentionally ignored. Copy its `OPENAI_API_KEY` into `backend/.env` without committing it.

### Frontend

```bash
cd frontend
cp .env.example .env.local
npm install
npm run dev
```

Set `NEXT_PUBLIC_API_BASE_URL` to the Render API URL. For a static production build:

```bash
npm run build
```

Upload the contents of `frontend/out/` to `wayan.com/copilot/`.

## Production setup

1. Create a Neon Postgres database and enable the `vector` extension.
2. Create the Render service from `render.yaml`.
3. Set `DATABASE_URL`, `OPENAI_API_KEY`, `CORS_ORIGINS`, and `ADMIN_API_KEY` in Render.
4. Run the Render pre-deploy command to migrate the database.
5. After separately approving OpenAI embedding charges, run `python -m app.ingest --seed-if-empty` once to seed the approved starter corpus.
6. Build the frontend with the final Render URL and upload `frontend/out/` by FTP.

No API key is ever shipped to the browser.

## API

- `POST /api/chat`: retrieve evidence and return a cited answer
- `GET /api/sources`: list approved corpus sources
- `GET /api/updates`: list sources with multiple distinct stored versions
- `POST /api/feedback`: record answer feedback
- `POST /api/bookmarks`: save an answer
- `GET /api/conversations/{id}`: retrieve conversation history
- `GET /api/admin/summary`: corpus and usage health, requires `X-Admin-Key`
- `GET /healthz`: liveness and dependency status

## Corpus updates

Edit `backend/app/source_registry.py`, then run:

```bash
python -m app.ingest --seed
```

The starter registry contains official Iowa DNR, U.S. Department of Labor, USDA APHIS, OSHA, FDA, and Iowa Legislature sources. Each fetched source is stored with a content hash and retrieval timestamp for version tracking.

See `PRD_COMPARISON.md` for the current requirement-by-requirement assessment and remaining priorities.
