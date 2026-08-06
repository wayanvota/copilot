# Iowa Pork Producer Current-Concerns Benchmark

Run date: 2026-08-06

Production endpoint: `https://iowa-pork-copilot-api.onrender.com/api/chat`

Corpus after expansion: 45 documents

## Outcome

- 13 verified answers
- 7 conditional answers that cite applicable evidence and identify the farm-specific facts needed for a final determination
- 0 questions returned the former empty “no approved source excerpts matched” result

“Conditional” is not treated as a failed retrieval when the governing rule depends on facts the question does not supply, such as animal-unit capacity, ground condition, job task, disease-control order, or destination market.

## Questions and final status

| # | Question | Final status |
|---|---|---|
| 1 | If I see signs of pseudorabies in my pigs, who must I notify and how quickly? | Verified |
| 2 | If my Iowa hog farm is quarantined for pseudorabies, what pig, feed, equipment, and visitor movements are restricted? | Conditional on the written quarantine order |
| 3 | During an ASF, classical swine fever, or foot-and-mouth disease outbreak, what must I have before officials may permit pig movements? | Conditional on incident-command requirements |
| 4 | What signs of African Swine Fever should employees report, and who should receive the report? | Verified |
| 5 | Is PRRS a legally reportable disease in Iowa, or should I only contact my veterinarian? | Verified |
| 6 | If influenza A or H5N1 is suspected in my pigs, is it reportable and what should I do first? | Verified |
| 7 | What safety steps should I take before agitating or pumping a foaming manure pit? | Verified |
| 8 | Can I spread liquid hog manure on snow-covered or frozen ground this winter? | Conditional on operation size, manure type, dates, and ground condition |
| 9 | What must I report after a manure spill, and which phone numbers should I call? | Verified |
| 10 | How many acres do I need to land-apply the manure from my pigs? | Conditional on manure volume, nutrient analysis, crop needs, and soil phosphorus |
| 11 | When is my annual manure-management-plan update due, and what records must I keep? | Conditional on facility ID and assigned update month |
| 12 | Do I need an Iowa DNR construction permit before building or expanding a hog barn? | Verified with capacity and storage-type conditions |
| 13 | What separation distances apply between a new Iowa confinement barn and neighbors, wells, roads, or sinkholes? | Verified with capacity, location, and well-type conditions |
| 14 | How quickly must I dispose of a dead pig, and which disposal methods are allowed? | Verified |
| 15 | What Iowa requirements apply if I compost dead pigs on the farm? | Verified with facility-location, mortality-source, and disease-status conditions |
| 16 | Does California Proposition 12 apply to my Iowa sow operation if some pork may be sold in California? | Conditional on animal class, production purpose, and California destination |
| 17 | What records and inspections do I need for Proposition 12 pork certification? | Verified |
| 18 | Can I hire a 14- or 15-year-old who is not my child to clean a hog barn? | Conditional on each task, equipment, animal exposure, and school hours |
| 19 | Which Form I-9 documents and retention records must I keep for new farm employees? | Verified |
| 20 | Can an Iowa hog operation use H-2A workers for permanent year-round jobs? | Verified |

## Source families added

- Iowa reportable-animal-disease rule, pseudorabies statute, quarantine protocol, and animal-movement permitting protocol
- Secure Pork Supply continuity-of-business plan
- USDA APHIS swine influenza guidance
- Iowa State and University of Minnesota Extension manure-foam and agitation safety guidance
- Iowa DNR winter manure guide and confinement-structure separation tables
- Iowa dead-animal disposal statute and composting rule
- California Department of Food and Agriculture Proposition 12 producer, inspection, and regulatory guidance
- USCIS Form I-9, instructions, and employer-retention guidance
- U.S. Department of Labor H-2A program guidance

## Browser-only downloads resolved

The Iowa Legislature PDFs for rule 21-64.1, Iowa Code chapters 166D and 167, and rule 567-105.6 returned HTTP 503 to the local automated downloader. Browser-downloaded copies have now been visually verified, checked for extractable controlling text, and stored in the corpus for reproducible ingestion.

The composting smoke test identified rule 567-105.3 as an additional controlling dependency. Its official URL and source-grounded text are indexed, but its local automated download is blocked and a browser-downloaded copy is still requested.
