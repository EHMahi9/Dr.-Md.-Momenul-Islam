# Gate 4B: Document-Level Approval & Rights Verification

> **Status:** RIGHTS VERIFICATION COMPLETE (STOPPED)
> **Purpose:** Perform document-level rights verification and final approval for the initial knowledge base. 
> **Important Constraint:** No documents have been ingested, chunked, or vectorized. 

## 1. Document Approval Metrics

*   **Total Candidates Evaluated:** 14
*   **APPROVED_FOR_INGESTION:** 9
*   **NEEDS_REVIEW:** 5
*   **REJECTED:** 0

## 2. Final Rights Findings

### World Health Organization (WHO) (6 Documents)
*   **Rights Status:** `VERIFIED_RESTRICTED`
*   **Licence:** CC BY-NC-SA 3.0 IGO
*   **Commercial Use:** PROHIBITED without explicit permission.
*   **Adaptation/Translation:** PERMITTED. Adaptations (including translations to Bangla) must be shared under the same license, and a disclaimer is required indicating WHO does not endorse the translation.
*   **Third-Party Content:** Must be manually excluded (images/graphs often carry independent copyright).

### National Health Service (NHS, UK) (3 Documents)
*   **Rights Status:** `VERIFIED_RESTRICTED`
*   **Licence:** Open Government Licence (OGL v3.0) / NHS Copyright
*   **Commercial Use:** PERMITTED in principle under OGL, but NHS terms of use require an explicit API agreement for bulk syndication or large-scale scraping.
*   **Adaptation/Translation:** PERMITTED. Must not claim official NHS endorsement.
*   **Third-Party Content:** NHS logos and trademarks are explicitly excluded from the OGL and must not be reproduced.

### Bangladesh Government Sources (DGHS, IEDCR) (5 Documents)
*   **Rights Status:** `UNKNOWN`
*   **Licence:** UNKNOWN
*   **Commercial Use:** UNKNOWN
*   **Adaptation/Translation:** UNKNOWN
*   **Reasoning:** Although these are public government guidelines (Dengue, Malaria, Nipah, Snakebite, Animal Bite), the ability to download a PDF does not automatically grant legal permission to scrape, adapt, and serve via an AI application. Because no explicit open licence is stated, we record rights conservatively as UNKNOWN.

## 3. Unresolved Candidates (NEEDS_REVIEW)
The following 5 documents are technically and clinically authoritative but fail the conservative rights verification check due to `UNKNOWN` licensing:
1.  **DGHS - National Guidelines for Clinical Management of Dengue Syndrome** (No explicit license)
2.  **DGHS - National Malaria Elimination Guidelines** (No explicit license)
3.  **IEDCR - Nipah Virus Outbreak Updates** (No explicit license)
4.  **DGHS - National Snakebite Strategy & Costed Plan of Action** (No explicit license)
5.  **DGHS - National Guideline for Animal Bite Management in Bangladesh 2021** (No explicit license)

## 4. Initial Ingestion Set (5–8 Recommended Documents)
From the 9 `APPROVED_FOR_INGESTION` candidates (which are approved strictly for the current non-commercial/research phase), the following 7 documents should form the initial ingestion set to maximize coverage of different RAG challenges (disease facts, crisis, medication bounding, and climate emergency) while maintaining clear licensing bounds:

1.  **WHO - Cholera Fact Sheet** (Baseline public health facts)
2.  **WHO - Nipah virus Fact Sheet** (Endemic threat definitions)
3.  **WHO - Dengue and severe dengue Fact Sheet** (Baseline facts to replace the unapproved DGHS clinical guide for now)
4.  **WHO - Rabies Fact Sheet** (High-urgency triage boundaries)
5.  **WHO - Suicide Fact Sheet** (Crisis handling baseline)
6.  **NHS - Heat exhaustion and heatstroke** (Consumer emergency boundaries)
7.  **NHS - Paracetamol for adults** (Safe OTC medication bounding)

## 5. Remaining Source Gaps
*   **Local Clinical Guidelines:** Because DGHS and IEDCR documents are currently blocked by licensing uncertainty, the system lacks localized clinical precedence (e.g., BD-specific malaria zones, local snakebite anti-venom protocols).
*   **Maternal and Neonatal Health:** No documents evaluated yet.
*   **Localized Mental Health:** Currently relying solely on global WHO definitions.

## 6. Stop Condition Enforced
*   **Ingestion:** NOT STARTED
*   **Embeddings/Chunking:** NOT STARTED
*   **Vector DB Selection:** NOT STARTED
*   **Medical Text Downladed:** NONE (Only metadata cataloged).
