# Iowa Pork Compliance Copilot: PRD Comparison

Reviewed against PRD version 0.1 on August 6, 2026.

## Bottom line

The product now delivers the PRD's central promise: a public Iowa-first assistant that retrieves approved evidence, answers in plain English, and links every supported claim to an official source. Its strongest controls are structural. The model receives only retrieved excerpts, citations must match server-issued chunk IDs, and uncited claims are removed before an answer reaches the user.

The product is still short of the PRD's long-term trust standard. The corpus is manually maintained, source changes are stored but not yet summarized, the evaluation set has 20 questions rather than 500 reviewed questions, and availability and accessibility have not been independently verified against the stated targets.

## Requirement status

| PRD requirement | Status | Current implementation |
| --- | --- | --- |
| Natural-language questions | Implemented | Public chat API and responsive web form |
| Retrieval from authoritative documents | Implemented | Approved-source registry, hybrid keyword and semantic retrieval, metadata filters |
| Plain-English answers | Implemented | Structured answer with short answer, why, rules, and records |
| Official citations and links | Implemented | Server-validates chunk IDs and resolves them to official URLs |
| Follow-up questions | Implemented | Conversation context plus clickable evidence-generated follow-ups |
| Conversation memory | Implemented with limits | Server conversation history and browser persistence; no cross-device account |
| Source filtering | Implemented | Tier and topic filters |
| Applicability assessment | Improved | High, medium, low, or unknown with explanation and optional farm profile |
| “What changed?” summaries | Partial | Distinct document versions are stored and exposed; reliable change summaries are not generated yet |
| Document versioning | Implemented | Content hashes and full stored versions |
| Search logging | Implemented | Query, retrieved chunk IDs, latency, evidence status, and failures |
| Feedback collection | Implemented | Helpful or not helpful plus an optional explanation |
| Recent regulation updates | Partial | Source retrieval dates and multi-version status are visible; updates are not scheduled or summarized |
| Bookmark answers | Implemented with limits | Saved on the producer's device and recorded by the backend; no cross-device account |
| Export PDF | Implemented | Print-optimized browser PDF export |
| Admin dashboard | Improved | Corpus health, failures, ratings, freshness, and frequent evidence gaps |
| Public access without a gate | Implemented | No producer access code or sign-in requirement |
| Mobile responsive | Implemented | Mobile-specific layout and controls |
| WCAG AA | Partial | Semantic controls, labels, focus states, reduced-motion support; no formal AA audit yet |
| Encryption and audit logging | Partial | HTTPS in production and query logs; infrastructure encryption and retention policy need a documented audit |
| Response under 10 seconds | Partial | The benchmark records latency, but the target is not continuously monitored |
| 99% availability | Not verified | Render hosts the API; no independent uptime monitor or service-level report |
| 500-question reviewed benchmark | Not implemented | Current benchmark has 20 common producer questions |

## Improvements made in this release

1. Added an optional farm profile for county, operation type, animal-unit capacity, manure storage, worker relationship, and California sales. These facts are treated as user context, never as authority.
2. Separated a source gap from a missing farm fact. An answer can now say that the authoritative rule was found while clearly listing the facts needed to apply it.
3. Added visible applicability explanations instead of showing only a high, medium, low, or unknown badge.
4. Added topic filters for permits, manure, labor, animal health, safety, and animal care, while keeping all topics as the default.
5. Persisted the current conversation, filters, farm facts, and saved answers in the producer's browser.
6. Made related questions actionable. A producer can click one to continue the same evidence-backed conversation.
7. Added source inventory, retrieval freshness, and honest version-tracking status. The interface explicitly says when it cannot establish what changed.
8. Added an emergency warning for active animal-health, worker-safety, fire, gas, and manure-spill situations.
9. Added written negative-feedback collection so the corpus team can see what was missing or wrong.
10. Removed raw internal chunk identifiers from visible answer text while retaining citation links.
11. Expanded the private dashboard to list the repeated questions that produced evidence gaps.
12. Added regression tests for farm context, citation cleanup, public access, and source-version reporting.

## Highest-priority remaining work

1. **Automate source monitoring and ingestion.** Check every approved URL on a schedule, retain the prior version, flag failed downloads, and notify an administrator when a source changes or disappears.
2. **Generate reviewed change summaries.** Compare two stored versions deterministically, cite both versions, and require human approval before publishing a “what changed” answer.
3. **Expand and review the benchmark.** Grow from 20 to 500 producer questions, have Iowa compliance specialists review every expected answer, and publish citation-accuracy, source-gap, hallucination, and latency results.
4. **Complete the authoritative corpus.** Add current Iowa administrative rules, permit instructions, county-role guidance, worker-safety materials, animal-disease reporting requirements, animal-care program standards, and relevant interstate market rules. Each addition needs an owner and review date.
5. **Add continuous production monitoring.** Track uptime, median and tail latency, OpenAI failures, database failures, citation coverage, retrieval misses, and stale sources. Alert on thresholds rather than relying on manual dashboard checks.
6. **Conduct producer usability testing.** Observe at least 10 Iowa producers or farm managers using the tool on a phone. Test whether they can distinguish a legal requirement, agency guidance, a missing fact, and a source gap.
7. **Complete an independent accessibility audit.** Test keyboard-only use, screen readers, color contrast, zoom, touch targets, error recovery, and exported PDFs against WCAG 2.2 AA.
8. **Define privacy and retention rules.** Document what query logs contain, how long conversations and feedback are retained, who can access the admin dashboard, and how a producer can remove local saved data.
9. **Add optional cross-device storage without adding a public gate.** If producers request it, offer optional accounts while keeping anonymous public questions available.
10. **Add farm document workflows only after the core benchmark is trustworthy.** Inspection reports, permits, and farm-specific checklists should inherit the same citation and uncertainty controls rather than becoming a separate generic upload chatbot.
