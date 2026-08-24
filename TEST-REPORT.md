# Nebraska Pork Compliance Copilot, full quality and security review

## Executive result

**Release recommendation: NOT READY.**

The corrected local release candidate passed the full automated regression suite, a clean production build, dependency audits, browser checks, safe attack simulations, and repeated OpenAI-backed questions. The public site and Render service were deliberately not changed. They still run the pre-review build, which lacks several fixes documented below. In particular, the deployed backend has not been verified to enforce the new administrator authorization on conversation-history access, and the deployed frontend does not emit the new security headers or application-specific 404 page.

The appropriate next step is to review the local diff, deploy the backend before the frontend, then repeat the live checks in this report. After that, the candidate could be classified **READY WITH KNOWN LIMITATIONS**. This review does not establish that the application is secure. It establishes only what resisted the tests described here.

## Review identity and environment

| Field | Value |
|---|---|
| Review date | 2026-08-24 |
| Project | Nebraska Pork Compliance Copilot |
| Project root | `/Users/wayanvota/Documents/ChatGPT/Alexis Solutions/Nebraska Pork Compliance Copilot` |
| Branch | `main` |
| Commit at start | `7fb2046` |
| Local working tree | Pre-existing user collateral changes preserved; review fixes remain uncommitted |
| Frontend | Next.js 16.3.0, React 19, static export served below `/copilot/` |
| Backend | FastAPI 0.141.1, Starlette 1.3.1, SQLAlchemy, Python 3.12 |
| Data | PostgreSQL plus pgvector in production; SQLite development database used for local concurrency and integration checks |
| AI | OpenAI `gpt-5.6-terra`; `text-embedding-3-large`; existing approved project key reused without exposing it |
| Public frontend | `https://wayan.com/copilot/` |
| Public backend | `https://nebraska-pork-copilot-api.onrender.com` |
| Corpus observed | 51 active Nebraska and federal documents |
| Browsers available | Chrome and the Codex in-app Chromium browser |

Material assumptions: the producer-facing assistant is intentionally public, while administrator data and conversation histories are private. A producer's major tasks are asking a question, optionally adding farm facts and a topic filter, reviewing the evidence-backed answer, following official citations, asking a follow-up, saving or exporting the answer locally, and submitting feedback. Administrator tasks include reviewing sources, updates, feedback, and retrieval gaps.

## Architecture and trust boundaries discovered

The FTP-deployable static frontend calls a Render-hosted FastAPI API. The API retrieves chunks from the approved corpus with metadata filters and hybrid search, sends retrieved evidence to OpenAI under a constrained structured-output prompt, validates returned citation aliases against retrieved chunks, stores the question and answer, and returns producer-facing claims plus official-source excerpts. PostgreSQL and pgvector are the intended production store. The frontend saves selected state and saved answers in browser storage. It does not use producer accounts or cookies. Administrator API operations use an `X-Admin-Key` header.

The highest-value trust boundary is the citation validator. Model output may refer only to aliases enumerated for the current retrieval result. The server maps those aliases to internal chunk IDs, rejects unknown aliases, removes uncited claims, and now removes internal aliases from every visible answer field.

## Results at a glance

- **47 distinct test categories executed.** File upload was genuinely inapplicable because the product exposes no upload route or UI, so it was excluded from the executed count.
- **37 categories passed without discovering a defect.**
- **10 categories initially exposed a defect and passed after a focused local fix and regression test.**
- **0 known local regression checks remain failing.**
- **0 checks were blocked by missing credentials.**
- **10 material subchecks remain unverified**, principally deployment verification, Firefox, Safari/WebKit, a real screen reader, automated color-contrast measurement, production concurrency, Apache configuration parsing, production POST behavior, retention/deletion policy, and destructive or load testing that was intentionally excluded.

Automated totals after fixes were **36 backend tests passed** and **8 frontend tests passed**. Five direct AI adversarial cases passed. Five representative producer questions passed sequentially with retrieved citations. A repeated three-question concurrent run passed after the database transaction fix. The frontend and Python dependency audits reported zero known vulnerabilities after the installer was upgraded and the reviewed dependency set was refreshed.

## Numbered test-category matrix

| # | Executed category | Result | Evidence and distinct checks |
|---:|---|---|---|
| 1 | Clean installation and build | Pass | Fresh temporary Python environment installed `requirements.txt`; fresh `npm ci`; Next static export completed. The clean run passed 32 backend tests at that stage. The final working-tree build also passed after all fixes. |
| 2 | Static analysis | Pass | Ruff `E`, `F`, and import-order checks passed. Broader inspection found a Starlette TestClient deprecation warning, retained as a known maintenance item. |
| 3 | Type and compile checking | Pass | `tsc --noEmit` passed; Python `compileall` passed. |
| 4 | Unit tests | Pass | Citation mapping, chunk cleanup, farm context, strict response schema, URL allowlist, chunking, source corpus text, validation boundaries, redirects, and readiness behavior were exercised. |
| 5 | Component tests | Pass | Initial form, disabled submit, loading state, cited answer, API error recovery, local session restoration, accessibility, and keyboard activation passed. |
| 6 | Integration tests | Pass after fix | FastAPI, SQLAlchemy, corpus retrieval, local persistence, and OpenAI were tested together. Concurrent database access failed before the transaction fix and passed afterward. |
| 7 | Smoke tests | Pass | Local backend started; `/healthz` returned 200 with database `ok`, Nebraska, 51 documents, and the configured model. Static homepage, admin entry, robots, sitemap, 404 artifact, and assets loaded. |
| 8 | Primary user flows | Pass | Five realistic end-to-end questions covered permits, manure acreage, non-family youth labor, African Swine Fever signs, and manure-pit safety. All eventually returned verified evidence and official citations. |
| 9 | Form and input validation | Pass after fix | Required question, whitespace-only input, minimum and maximum lengths, farm-context bounds, duplicate tiers/topics, unsupported topics, Unicode, emoji, and unexpected fields were tested. Server-side trimming and topic allowlisting were added. |
| 10 | Negative paths | Pass | Malformed JSON, unsupported methods, invalid fields, empty evidence, unavailable APIs, hostile values, and missing admin credentials produced controlled responses. |
| 11 | Navigation and links | Pass | Brand link, example-question buttons, source links, admin direct entry, query string, trailing slash, and static assets were checked. External source destinations are rendered from approved corpus metadata. |
| 12 | Routing and direct entry | Pass after fix locally | `/copilot/`, `/copilot/admin/`, `/copilot/robots.txt`, `/copilot/sitemap.xml`, `/copilot/404.html`, and query-string entry returned 200 locally. The live unknown route still falls into a WordPress/PHP 404; `.htaccess` now points Apache to the copilot 404 artifact. |
| 13 | API contract | Pass | Response models, content type, 200/201/307/400/401/404/405/413/422/429/503 behavior, malformed JSON, forbidden extras, and unsupported methods were asserted. |
| 14 | State and persistence | Pass | A saved frontend session restored after a simulated refresh. Feedback, bookmarks, conversations, messages, and query logs were verified through the database layer. No logout exists because producer access is public. |
| 15 | Concurrency and idempotency | Pass after fix | Duplicate feedback and bookmarks previously created duplicate rows; both now upsert. Three concurrent real questions initially produced two SQLite lock failures. The write transaction is now committed before retrieval/model work, and an automated two-thread regression plus a repeated three-request live-local run passed. |
| 16 | Error recovery | Pass after fix | Raw browser `Failed to fetch` text was reproduced. The API client now converts network failures and controlled server errors into producer-readable guidance while leaving the interface usable. |
| 17 | Responsive layout | Pass | Mobile 390 px, tablet 768 px, desktop, and large 1440 px layouts were rendered. Measured document width equaled viewport width at 390, 768, and 1440 px, with no horizontal overflow. |
| 18 | Cross-browser compatibility | Partial pass | The public homepage rendered correctly in Chrome and the in-app Chromium browser. Firefox and Safari/WebKit execution were unavailable and remain unverified. |
| 19 | Accessibility audit | Partial pass | `axe-core` found no automatically detectable violations within the main interface. Headings, main/complementary landmarks, labels, disabled state, and accessible names were checked. Automated color contrast was excluded because jsdom cannot compute final rendered contrast; visual review found no obvious failure. |
| 20 | Keyboard-only operation | Pass | Tab focus reached the home link; an example question was activated with Enter and completed the answer flow. Focus-visible CSS was inspected. Complex dialogs and menus do not exist. |
| 21 | Screen-reader-oriented checks | Partial pass | Browser accessibility snapshots exposed meaningful names, roles, headings, textbox and disabled button state. Loading uses `role=status`; errors use `role=alert`. A real VoiceOver/NVDA session was not run. |
| 22 | Visual regression evidence | Partial pass | Homepage, desktop, mobile, tablet, large-screen, Chrome, and error-state images were captured under `docs/test-evidence/2026-08-24/ui/`. There was no prior approved pixel baseline, so this is a review baseline rather than an automated pixel-diff suite. |
| 23 | Content integrity | Pass after fix | Terminology, labels, raw errors, Unicode, evidence status, and citation rendering were inspected. A real manure answer leaked internal alias `【S8】`; the validator now sanitizes claims, missing facts, limitations, related questions, and applicability text. The OpenAI-backed regression returned zero alias leaks. |
| 24 | Localization and formatting | Pass | Unicode, emoji, Nebraska place names, non-ASCII punctuation, long text, ISO timestamps, and responsive text expansion were exercised. The product is intentionally English-only and does not display currencies. |
| 25 | Performance | Pass with limitation | Public homepage fetched in about 0.19 seconds during the test; required assets returned 200 in roughly 0.20 to 0.35 seconds each. The static artifact is about 860 KB uncompressed; largest JS chunks were about 229 KB, 181 KB, and 113 KB. No lab LCP/INP score was produced. |
| 26 | Slow network and caching | Partial pass | Rejected and interrupted fetches were simulated in component tests; the UI recovered. Apache cache rules were added for HTML, JS, CSS, and SVG. Live static assets still lack the new cache policy because deployment was out of scope. Offline mode and service workers are not product features. |
| 27 | Cross-site scripting | Pass | Safe reflected/stored/DOM payload strings, model-output strings, farm-context values, and query parameters were treated as text. React escaping remained intact; no raw HTML rendering surface was found. |
| 28 | Injection | Pass | Safe SQL metacharacters, template-like expressions, shell metacharacters, Unicode control text, and hostile headers were submitted locally. SQLAlchemy parameterization and strict models treated them as data. No LDAP or NoSQL interpreter exists. |
| 29 | Authentication | Pass after fix | Producer access correctly remains public. Administrator key absence and invalid key were rejected. Conversation-history access previously lacked administrator authentication and is now protected. Password flows are inapplicable because the application has no passwords or producer accounts. |
| 30 | Authorization | Pass after fix | Direct conversation-history access was confirmed in code to lack an authorization dependency, creating a horizontal data-access risk for anyone possessing another conversation UUID. The endpoint now requires the administrator dependency; protected-route tests cover missing and invalid keys. |
| 31 | Session, cookie, CSRF, and CORS | Pass | No cookies or server producer sessions were set, which removes conventional cookie-CSRF exposure. Trusted CORS origin passed; hostile origins did not receive an allow-origin response. Browser storage contents were inspected for the intended local-only state. |
| 32 | SSRF and unsafe URL handling | Pass | Loopback, private-address, subdomain-confusion, insecure HTTP, and unapproved hosts were rejected by the ingestion allowlist. Redirect validation and third-party-host behavior were reviewed. |
| 33 | Path traversal and file access | Pass | Encoded traversal, absolute path, unapproved extension, missing file, and symlink-escape cases were tested against manual-corpus loading. Only approved PDF paths within the corpus root are accepted. |
| 34 | Open redirects | Pass | Root redirect is a fixed trusted URL. Encoded external destinations, protocol-relative values, user-info tricks, and query parameters were unable to alter it. |
| 35 | CORS and security headers | Pass after fix locally | Backend now sends CSP, frame denial, MIME-sniffing protection, referrer policy, permissions policy, no-cache, and production HSTS, including size/rate-limit responses. FTP Apache rules add corresponding frontend headers. The live site still exposes the old header set. |
| 36 | Request boundaries | Pass after fix | JSON body limit is 32,768 bytes; excessive bodies return 413. Long questions, query strings, invalid encodings/content types, excessive extras, and controlled 400/404/405/413/422/429 responses were tested. |
| 37 | Rate limiting and abuse control | Pass | Safe bursts reached 429 without a denial-of-service test. Obvious `X-Forwarded-For` spoofing did not bypass the limiter. Limits apply before expensive answer execution. Distributed/multi-instance enforcement remains a production design limitation because the limiter is process-local. |
| 38 | Secrets and sensitive data | Pass | Tracked files, built assets, source maps, browser storage, API responses, and likely secret patterns were scanned. Only documented placeholders were found; no API key value was printed or copied. |
| 39 | Dependency and configuration | Pass after fix | Initial audit found one high npm advisory and 45 Python advisories across outdated packages. Next, FastAPI, Starlette, PyPDF, pytest, and transitive packages were updated. Final npm and pip audits reported zero known vulnerabilities. Render now upgrades `pip>=26.2` before dependency installation. |
| 40 | Privacy and logging | Partial pass | Producer warnings discourage names, exact addresses, and confidential records. Farm facts are not copied into server conversation history, but questions and answers are intentionally stored for conversation and review functions. No documented retention/deletion schedule or producer data-access process exists. |
| 41 | AI adversarial behavior | Pass | Five paid model cases covered direct evidence override, prompt extraction, role-tag injection, Unicode-obfuscated instruction, and delimiter escape. All five abstained or preserved evidence constraints. Fabricated citation aliases are rejected by schema and server mapping. Malicious uploads are inapplicable because no upload exists. |
| 42 | SEO and discoverability | Pass after fix locally | Title, description, canonical URL, Open Graph values, robots rules, sitemap, heading structure, and admin `noindex` were added or verified. Initial static export failed because robots/sitemap were not forced static; the route configuration was fixed and the export passed. |
| 43 | Health and readiness | Pass after fix | Health reports database state, Nebraska jurisdiction, document count, and model. Production readiness now returns 503 when the corpus is empty or the OpenAI key is absent, rather than claiming the answer service is ready. Startup/shutdown completed cleanly. |
| 44 | Production artifact | Pass | The final Next static output was served locally. Homepage, admin, robots, sitemap, 404 artifact, query entry, and assets were requested from `out/`, not the development server. |
| 45 | Repeated reliability | Pass after fix | Five answer categories, five adversarial generations, a repeated manure query, and two rounds of three simultaneous questions were executed. The first concurrent round exposed database locking; the second returned three 200 responses with 4 to 8 citations each. |
| 46 | Regression suite | Pass | Final backend result: 36 passed, one dependency deprecation warning. Final frontend result: 8 passed. Ruff, TypeScript, Python compilation, production export, npm audit, and pip audit passed. |
| 47 | Live-site verification | Partial pass | Safe GET/HEAD checks only. Public homepage and required assets returned 200; Render health GET returned 200 with 51 documents. Live frontend lacked the new headers, live backend lacked CSP/frame/HSTS, and unknown routes reached WordPress. No production POST, administrator action, data read, or mutation was attempted. |

## File-upload category disposition

The required file-upload category was not counted as executed. No producer or administrator upload endpoint, multipart handler, or upload UI exists. Manual corpus PDFs are ingested from a maintainer-controlled local directory, which was covered by path, extension, symlink, approved-host, and parser tests instead.

## Defects found and fixed locally

| ID | Severity | Reproduction and cause | Focused fix | Regression evidence |
|---|---|---|---|---|
| D1 | High | `GET /api/conversations/{id}` lacked the administrator dependency. Anyone who obtained a conversation UUID could request its messages. | Applied the existing admin-key dependency to conversation history. | Missing and invalid keys now return 401; valid admin dependency is covered locally. |
| D2 | High | Initial Python audit reported 45 advisories in outdated FastAPI/Starlette/PyPDF/pytest packages. | Upgraded compatible dependencies and the Render installer. | Final `pip-audit`: no known vulnerabilities. |
| D3 | High | Initial npm audit reported a high-severity `nanoid` advisory. | Updated the lockfile through the compatible dependency chain. | Final `npm audit --audit-level=moderate`: zero vulnerabilities. |
| D4 | Medium | Frontend and some backend responses lacked a complete CSP, anti-framing policy, HSTS, and application 404 behavior. | Added API middleware headers and FTP Apache header/cache/404 rules. | Header assertions pass locally; artifact routes pass. Live verification remains pending. |
| D5 | Medium | Browser network failure displayed raw `Failed to fetch`. | Normalized transport and server failures into useful producer-facing messages. | Component and API-client error tests pass; dismiss/retry state remains usable. |
| D6 | Medium | Repeated feedback/bookmark submissions created duplicate rows. | Added idempotent lookup/upsert behavior. | Duplicate-request tests assert one saved record. |
| D7 | Medium | Production health could return 200 with no corpus or no OpenAI key. | Added production readiness prerequisites and controlled 503 responses. | Readiness tests cover missing corpus and key. |
| D8 | Medium | Inputs allowed whitespace-only questions, unsupported topics, and large bodies without a global request boundary. | Added normalization, topic allowlist, farm bounds, and a 32,768-byte request limit. | Boundary and validation tests pass, including 413 and 422 cases. |
| D9 | Medium | An actual manure answer leaked internal alias `【S8】` in `missing_facts`. The sanitizer covered cited claim text only. | Sanitized all visible answer fields, including missing facts, limitations, related questions, and applicability. | Unit regression passes; repeated paid answer reported zero internal alias leaks. |
| D10 | Medium | Three simultaneous local questions returned one 200 and two 500 responses with `sqlite3.OperationalError: database is locked`. A write transaction remained open across retrieval and the OpenAI call. | Commit the conversation and user message before retrieval/model work; increase SQLite lock timeout. | Two-thread automated test passes; repeated three-request OpenAI run returned three 200 verified answers. |
| D11 | Low | New robots and sitemap handlers initially broke static export because they were not explicitly static. | Added `dynamic = "force-static"` to both handlers. | Final Next production export passed with both routes prerendered. |

## Security findings

### Confirmed vulnerabilities in the pre-review build

The unprotected conversation-history endpoint was a confirmed authorization weakness in the reviewed source. The current public deployment has not been changed, so it must be treated as potentially exposed until the corrected backend is deployed and safely verified. Dependency audits also confirmed known vulnerable versions in both package ecosystems before the local upgrades.

### Risks mitigated in the local candidate

The local candidate adds administrator authorization, request-size enforcement, safer rate-limit identity handling, idempotent mutations, stricter input validation, CSP and anti-framing headers, production readiness checks, network-error normalization, citation-artifact sanitization, and shorter database write transactions. Tested XSS, injection, SSRF, traversal, redirect, hostile CORS, fabricated citation, and prompt-injection payloads did not bypass the tested controls.

### Areas outside the evidence

No destructive payloads, credential attacks, denial-of-service, aggressive load, third-party scans, or production mutations were run. The review did not inspect Render, Neon, Apache, DNS, TLS, backups, alerting, or OpenAI account settings through their private dashboards. It did not establish data retention, deletion, legal compliance, incident response, disaster recovery, multi-instance rate limiting, or corpus legal accuracy. It did not include Firefox, Safari/WebKit, a real screen reader, or formal performance lab instrumentation.

## Exact commands and tools used

Representative commands, with secret values omitted:

```text
python3 -m venv /tmp/nebraska-copilot-clean.../.venv
/tmp/nebraska-copilot-clean.../.venv/bin/pip install -r backend/requirements.txt
npm ci
npm test
npm run check
npm run build
.venv/bin/python -m pytest -q
.venv/bin/python -m ruff check app tests --select E,F,I --ignore E501
.venv/bin/python -m compileall -q app
npm audit --audit-level=moderate
.venv/bin/pip-audit
.venv/bin/python evals/adversarial_quality.py
python3 -m http.server 4173 --bind 127.0.0.1 --directory /tmp/nebraska-copilot-static
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
curl http://127.0.0.1:8000/healthz
curl -H 'Content-Type: application/json' -d '{...}' http://127.0.0.1:8000/api/chat
curl -sSI https://wayan.com/copilot/
curl -sS -D - -o /dev/null https://nebraska-pork-copilot-api.onrender.com/healthz
```

The Codex in-app browser and Chrome connector were used for DOM accessibility snapshots, viewport measurements, interaction checks, direct-entry checks, and screenshots. `axe-core`, Testing Library, Vitest, Pytest, Ruff, TypeScript, npm audit, pip-audit, curl, and direct OpenAI-backed requests supplied automated or reproducible evidence.

## Visual evidence

Review images are stored in `docs/test-evidence/2026-08-24/ui/`, including:

- `01-production-home-desktop.png`
- `02-local-desktop.png`
- `03-local-mobile.png`
- `04-local-loading.png` (captured the reproduced pre-fix network-error state)
- `05-production-chrome.png`
- `06-local-tablet.png`
- `07-local-large.png`

## Files changed by this review

Core behavior and configuration:

- `backend/app/main.py`
- `backend/app/copilot.py`
- `backend/app/database.py`
- `backend/app/ingest.py`
- `backend/app/schemas.py`
- `backend/requirements.txt`
- `frontend/app/layout.tsx`
- `frontend/app/admin/layout.tsx`
- `frontend/app/robots.ts`
- `frontend/app/sitemap.ts`
- `frontend/lib/api.ts`
- `frontend/public/.htaccess`
- `frontend/package.json`
- `frontend/package-lock.json`
- `render.yaml`
- `README.md`

Test and evidence additions:

- `backend/tests/test_security_quality.py`
- `backend/tests/test_api.py`
- `backend/tests/test_trust_controls.py`
- `backend/evals/adversarial_quality.py`
- `frontend/app/page.test.tsx`
- `frontend/lib/api.test.ts`
- `frontend/vitest.config.mts`
- `frontend/vitest.setup.ts`
- `docs/test-evidence/2026-08-24/ui/*`
- `TEST-REPORT.md`

Ruff formatting also made mechanical formatting changes in several existing backend Python files. Pre-existing collateral and unrelated PDFs were preserved and were not included in the review scope.

## Release gate

Do not present the current public deployment as the reviewed release. Before changing the recommendation:

1. Review and commit only the intended code, tests, deployment configuration, and report, excluding unrelated collateral.
2. Deploy the backend first and verify admin authorization, health readiness, security headers, five representative answers, citation integrity, and concurrent requests against the deployed PostgreSQL path.
3. Upload the final static frontend and `.htaccess`, then verify the homepage, assets, admin `noindex`, robots, sitemap, cache policy, CSP, HSTS, unknown routes, responsive layouts, error recovery, and source links.
4. Run Firefox, Safari/WebKit, VoiceOver, and rendered color-contrast checks.
5. Define a short, public data-retention and deletion policy before inviting producers to enter operational questions.

Until those steps are complete, the evidence supports **NOT READY** for the website currently visible to the public.
