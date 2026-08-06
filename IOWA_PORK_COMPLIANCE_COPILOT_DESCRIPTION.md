# Iowa Pork Compliance Copilot

Iowa’s pork industry operates at a scale that demands both efficiency and discipline. USDA data show that Iowa had approximately 25.2 million hogs on farms as of December 2025, the largest inventory of any state. In 2024, Iowa accounted for 32 percent of the nation’s hog inventory, and hog sales generated an estimated $9.02 billion in cash receipts. ([USDA National Agricultural Statistics Service](https://www.nass.usda.gov/Quick_Stats/Ag_Overview/stateOverview.php?state=Iowa), [2025 Iowa Agricultural Statistics](https://data.nass.usda.gov/Statistics_by_State/Iowa/Publications/Annual_Statistical_Bulletin/2025-Iowa-Annual-Bulletin.pdf))

The Iowa Pork Compliance Copilot is designed to help producers manage the regulatory decisions that accompany that scale. It is a public web application that accepts a question in ordinary language, searches a controlled collection of approved government and official guidance documents, and returns a plain-English response with citations to the underlying sources.

The tool is deliberately narrower than a general-purpose chatbot. It does not answer from unrestricted model knowledge. It retrieves evidence before generating an answer, and its server checks that every citation refers to a source excerpt retrieved for that question. If the evidence does not support a claim, the tool is designed to withhold the claim and explain what it could not verify.

> **Screenshot placeholder 1:** Insert `docs/screenshots/copilot-overview.jpg` here.
>
> *Suggested caption: The public question interface centers the producer’s question while keeping farm context, search scope, and source status visible.*

## What the tool does

A producer can ask questions such as:

- Do I need a permit before building a new hog barn?
- How much land do I need to apply manure from my pigs?
- Can a 15-year-old clean a hog barn?
- What signs of African Swine Fever should employees report?

The Copilot searches approved material from the Iowa Department of Natural Resources, Iowa Legislature, U.S. Department of Agriculture, U.S. Department of Labor, Occupational Safety and Health Administration, and Iowa State University Extension. Its [public source inventory](https://iowa-pork-copilot-api.onrender.com/api/sources) currently contains 46 documents.

Answers are divided into practical sections: a short answer, why the rule applies, applicable rules, documentation to keep, limitations, and official sources. Each substantive answer claim must have a citation. The producer can expand a source to read the supporting excerpt, see retrieval and effective dates when available, and open the original publication.

Agricultural requirements often depend on facts omitted from a short question. Iowa DNR guidance distinguishes confinement operations from open feedlots and uses animal-unit capacity when determining some manure-management and certification obligations. A manure management plan is generally required for certain confinement operations above 500 animal units, while open feedlots are treated differently except when a permit or agreement imposes additional requirements. ([Iowa DNR manure management plans](https://www.iowadnr.gov/environmental-protection/animal-feeding-operations/afo-confinements/manure-management-plans), [Iowa DNR manure application guidance](https://www.iowadnr.gov/environmental-protection/animal-feeding-operations/afo-manure-application))

The Copilot therefore allows a producer to provide optional farm facts, including county, operation type, animal-unit capacity, manure-storage type, worker relationships, and whether the operation sells into California. These facts help retrieve relevant evidence and explain applicability. They do not become regulatory evidence themselves, and the farm profile is not copied into server conversation history.

> **Screenshot placeholder 2:** Insert `docs/screenshots/copilot-farm-facts.jpg` here.
>
> *Suggested caption: Optional farm facts help distinguish confinement and open-feedlot requirements and identify facts that could change the answer.*

The product separates two conditions that automated systems often blur. A **source gap** means the approved corpus did not contain enough authoritative evidence to support an answer. A **missing-fact condition** means the rule was found, but the producer has not supplied a fact needed to apply it. The Copilot identifies missing farm facts separately and explains why they matter.

## Why a producer would use it

Compliance research consumes time because controlling information is distributed across statutes, administrative rules, agency forms, federal fact sheets, manuals, and frequently updated web pages. A familiar manure question can require a producer to determine the operating category, locate the correct form, check thresholds, identify required records, and distinguish a legal requirement from recommended practice.

The Copilot provides a faster starting point without concealing the source. A producer can use it before calling a consultant, attorney, veterinarian, extension specialist, or regulator. The result identifies applicable terminology, likely authority, and unresolved facts. It can also help prepare for an inspection, create a recordkeeping checklist, review a young worker’s proposed assignment, or brief employees on disease reporting.

The value is strongest when the answer remains inspectable. A producer can challenge it, follow the citation, and compare the response with the agency document. The tool retains the current conversation and saved answers in the producer’s browser, supports follow-up questions, and offers a print-optimized PDF export. These features turn a one-time search into a practical compliance work product.

The source-status panel shows the number of indexed sources, the most recent retrieval date, and whether multiple versions of a source have been stored. At present, 11 documents have multiple stored versions available through the [source-update endpoint](https://iowa-pork-copilot-api.onrender.com/api/updates). The tool does not claim that a rule changed merely because a document was retrieved again. A reliable change summary requires two distinct versions and a defensible comparison.

> **Screenshot placeholder 3:** Insert `docs/screenshots/copilot-source-status.jpg` here.
>
> *Suggested caption: Producers can see corpus size, retrieval freshness, and whether earlier source versions are available for comparison.*

## Benefits for Iowa pork production

From a statewide public-interest perspective, the central benefit is greater consistency in how producers find and interpret compliance information. Independent operations, multi-site managers, and new employees can begin with the same official materials. Better access does not eliminate professional judgment, but it can reduce errors caused by outdated forms, incomplete searches, or uncited recollections.

The tool can also strengthen the connection between production and stewardship. Iowa DNR requires animal feeding operations to manage manure in ways that protect surface water and groundwater, observe applicable separation distances, report releases, and maintain required plans and records. The agency explains that manure management plans help calculate manure volume, nutrient concentration, required acres, and planned application rates. ([Iowa DNR confinement guidance](https://www.iowadnr.gov/environmental-protection/animal-feeding-operations/afo-confinements), [Iowa DNR manure management plans](https://www.iowadnr.gov/environmental-protection/animal-feeding-operations/afo-confinements/manure-management-plans)) Making those requirements easier to locate supports both productive agriculture and credible environmental compliance.

Evidence gaps and negative feedback can guide future improvements. If many producers ask a question the corpus cannot answer, administrators can see that pattern and prioritize the missing authority or retrieval fix. This creates a disciplined way to expand the tool according to demonstrated producer needs.

Mobile access is equally significant. Compliance questions arise in barns, offices, fields, vehicles, and meetings, not only at a desktop computer. The interface remains usable on a phone, with the same public access and no producer code or mandatory account.

> **Screenshot placeholder 4:** Insert `docs/screenshots/copilot-mobile.jpg` here.
>
> *Suggested caption: The responsive phone interface keeps farm context, search controls, and source status available where farm work occurs.*

The Copilot has firm limits. It is not legal advice, a veterinary diagnosis, or an emergency-reporting service. Regulations and guidance change, and the current corpus does not cover every question a producer may face. The tool earns trust by stating uncertainty and linking producers to the controlling source.

For Iowa, the standard should be practical: help producers get to the right source faster, understand why it applies, identify what they still need to know, and keep the records that demonstrate responsible operation. A compliance assistant that consistently meets that standard can reduce uncertainty for producers while strengthening animal health, worker protection, environmental stewardship, and public confidence in one of Iowa’s most important industries.
