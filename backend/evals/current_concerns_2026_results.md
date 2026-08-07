# Nebraska Pork Producer Current-Concerns Benchmark

Evaluated locally against the synchronized Nebraska corpus on August 7, 2026.

## Result

| Measure | Result |
| --- | ---: |
| Approved sources indexed | 51 |
| Source-ingestion failures | 0 |
| Retrieval questions passing after ranking fixes | 20 of 20 |
| End-to-end questions completed | 20 of 20 |
| Final verified evidence status after targeted remediation | 20 of 20 |
| Answers with at least one validated citation | 20 of 20 |
| Conflicting-source answers | 0 |
| API errors | 0 |
| Initial-run median latency | 11.7 seconds |

The benchmark covers livestock-waste inspection and permits, county conditional uses, Title 130, manure acreage and records, discharge reporting, nutrient management, African Swine Fever, reportable diseases, swine imports, mortality disposal, youth employment, H-2A, Form I-9, manure-agitation safety, and California destination-market requirements.

## Defects found and corrected

1. A county conditional-use question initially ranked state environmental program pages above the Nebraska statutes. The query expansion and ranking bonus now prioritize Neb. Rev. Stat. sections 54-2437 and 23-114.01 when county or zoning facts are present.
2. An H-2A question initially treated the ordinary verb “use” as county-permit intent. County intent now requires county, zoning, or conditional terminology, and H-2A questions receive their own federal-program expansion and ranking control.
3. A county-permit answer correctly explained the conditional rule but labeled the evidence insufficient because the producer had not supplied a county ordinance. The prompt now classifies this as verified evidence with missing farm facts when state authority establishes the conditional framework.
4. A manure-agitation question lacked task-specific safety evidence. Nebraska Extension's manure-spreader guidance was added to establish ventilation and hydrogen-sulfide precautions while clearly labeling them as guidance rather than law.
5. One generated answer leaked a JSON-like array of internal chunk identifiers into visible text. The sanitizer now strips quoted arrays, raw identifiers, trailing JSON fragments, and empty bracket markers. Regression tests cover both ordinary and malformed citation artifacts.

## Remaining limitation

The 11.7-second initial median exceeded the PRD's target of less than eight seconds, and one child-labor answer took approximately 49 seconds. The evidence and citation controls worked, but production latency needs monitoring and likely model or orchestration optimization before the speed target can be claimed.

These are automated engineering results. They do not constitute expert legal, veterinary, or regulatory review. A Nebraska specialist should review expected conclusions and citations before the benchmark is treated as a compliance-accuracy score.
