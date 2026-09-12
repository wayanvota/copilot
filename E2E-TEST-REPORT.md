# Nebraska Pork Compliance Copilot end-to-end test report

## Scope

The harness builds and serves the production Next.js static export in Chromium
against the real FastAPI application. The E2E server replaces only model and
retrieval output with deterministic cited fixtures and uses an isolated in-memory
database. Real request schemas, CORS, security headers, body limits, rate limits,
feedback, bookmarks, source status, and admin boundaries remain active.

No database, OpenAI, Neon, Render, or public website credential is required in
CI. A live OpenAI check, when separately authorized, remains a small opt-in smoke
outside the deterministic release gate.

## Required categories

| ID | Category | Expected behavior |
| --- | --- | --- |
| U01 | Public trust boundary | Purpose, evidence posture, and confidentiality warning render |
| U02 | Empty question | Ask control remains disabled |
| U03 | Cited answer | Browser-to-FastAPI flow returns a sourced answer |
| U04 | Farm context | County and operation facts affect applicability |
| U05 | Topic scope | Selected topic reaches the answer workflow |
| U06 | Source-tier guard | User cannot remove the final source tier |
| U07 | Helpful feedback | Rating persists through the API and UI state |
| U08 | Corrective feedback | User can submit an explanatory comment |
| U09 | Local save | Saved answer survives browser reload |
| U10 | Service failure | Error is dismissible and follow-up input remains usable |
| A01 | Malformed JSON | Parser rejects invalid JSON without a stack trace |
| A02 | Invalid question | Whitespace-only or too-short input is rejected |
| A03 | Oversized body | Request fails before parsing |
| A04 | Unsupported topic | Schema rejects an unknown compliance domain |
| A05 | Impossible farm fact | Negative capacity is rejected |
| A06 | CORS boundary | Disallowed origin receives no browser permission |
| A07 | Request flood | Twenty-first question is rate-limited |
| A08 | Admin boundary | Conversation history requires an admin key |
| A09 | Active HTML | Script-like input remains inert and receives no executable output |
| A10 | Route abuse | Unknown route and unsupported method fail with security headers |

## Verification record

Status: passed locally on 2026-09-11 with Python 3.12 and Node 22.16.0.

- Existing backend tests: 36 passed
- Existing frontend tests: 8 passed
- Deterministic E2E categories: 20 passed, exactly U01-U10 and A01-A10
- TypeScript check and production static build: passed
- Frontend dependency audit: 0 vulnerabilities at all severities
- Python dependency consistency check: passed
- Optional OpenAI smoke using the authorized local key: structured evidence boundary passed
- GitHub Actions: pending after branch push

Reproduce with:

```bash
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install -r backend/requirements.txt
PYTHONPATH=backend python -m pytest -q backend/tests
cd frontend
npm ci
npx playwright install chromium
npm run test:ci
npm audit --audit-level=high
```
