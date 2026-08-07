# Nebraska Pork Compliance Copilot: PRD Comparison

Reviewed against PRD version 0.1 on August 7, 2026.

## Bottom line

The product implements the PRD's central promise for Nebraska: a public assistant that retrieves approved evidence, answers in plain English, and links each supported claim to an authoritative source. The model receives retrieved excerpts only. Citations must match server-issued chunk IDs, and uncited claims are removed before publication.

The corpus now centers on Nebraska livestock-waste regulation, permits, manure management, animal-health reporting, swine movement, youth employment, farm labor, and applicable federal or destination-market rules. The migration includes an explicit registry-sync control so a retired jurisdiction's documents cannot remain searchable.

## Current status

| Requirement | Status | Implementation |
| --- | --- | --- |
| Natural-language questions | Implemented | Public responsive chat |
| Authoritative retrieval | Implemented | Nebraska-first approved registry and hybrid retrieval |
| Plain-English answers | Implemented | Short answer, rationale, rules, records, and follow-ups |
| Official citations | Implemented | Server-validated evidence links |
| Conversation memory | Implemented with limits | Browser and server session memory, no cross-device account |
| Source filtering | Implemented | Topic and authority-tier filters |
| Applicability | Implemented | High, medium, low, or unknown with missing facts |
| Document versioning | Implemented | Content hashes and stored versions |
| Feedback and search logging | Implemented | Ratings, comments, retrieval IDs, latency, and evidence status |
| Bookmark and PDF export | Implemented with limits | Local saved answers and browser print-to-PDF |
| Admin monitoring | Implemented | Corpus, failures, ratings, freshness, and repeated gaps |
| Public access | Implemented | No access code or account required |
| Mobile and accessibility | Partial | Responsive and semantic; independent WCAG 2.2 AA audit remains |
| Source-change summaries | Partial | Versions are retained; reviewed change summaries remain future work |
| 500-question reviewed benchmark | Not implemented | Nebraska regression set is an initial operational benchmark |

## Highest-priority remaining work

1. Have Nebraska environmental, labor, and animal-health specialists review the expected answers and citations.
2. Expand the benchmark to 500 realistic questions, including county conditional-use differences and operation-specific edge cases.
3. Schedule source checks and alert an administrator when a source changes, disappears, or stops yielding readable text.
4. Add human-reviewed comparisons between distinct source versions before answering “what changed?”
5. Monitor production uptime, latency, retrieval gaps, citation coverage, database failures, and provider failures.
6. Test the mobile interface with Nebraska producers and farm managers, including users under time pressure.
7. Complete an independent WCAG 2.2 AA audit and document privacy, access, and retention controls.
8. Add farm-document workflows only after the Nebraska benchmark establishes reliable retrieval and citation performance.
