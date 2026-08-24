# Gate 4A: Medical Knowledge Source Discovery & Document Verification

> **Status:** DISCOVERY PASS COMPLETE (PENDING REVIEW)
> **Purpose:** Create a document-level candidate catalog for the initial trusted medical knowledge base.
> **Important:** No documents have been ingested, chunked, or vectorized. The architecture remains unmodified.

## 1. Discovery Summary

*   **Total Candidates Identified:** 12
*   **Metadata Verified:** 12
*   **Rejected:** 0 (Pre-filtered prior to catalog entry)
*   **Needs-Review (Licensing/Access):** 12

### Source Distribution
*   **World Health Organization (WHO):** 6 documents
*   **Directorate General of Health Services (DGHS, Bangladesh):** 2 documents
*   **National Health Service (NHS, UK):** 3 documents
*   **IEDCR (Bangladesh):** 1 document

## 2. Strongest Initial Candidates (Top 12)
The full verified metadata is available in `docs/knowledge/source-catalog.json`.
1.  **DGHS - National Guidelines for Clinical Management of Dengue Syndrome (4th Ed)** (BD Clinical)
2.  **DGHS - National Malaria Elimination Guidelines** (BD Clinical)
3.  **IEDCR - Nipah Virus Outbreak Updates and Prevention** (BD Public Health)
4.  **WHO - Cholera Fact Sheet** (Global Consumer/Public Health)
5.  **WHO - Nipah virus Fact Sheet** (Global Consumer/Public Health)
6.  **WHO - Dengue and severe dengue Fact Sheet** (Global Consumer)
7.  **WHO - Rabies Fact Sheet** (Global Consumer / High Urgency)
8.  **WHO - Tuberculosis Fact Sheet** (Global Consumer)
9.  **WHO - Depression Fact Sheet** (Global Mental Health)
10. **WHO - Suicide Fact Sheet** (Global Mental Health / Crisis)
11. **NHS - Heat exhaustion and heatstroke** (UK Consumer - gap filler for climate urgency)
12. **NHS - Paracetamol for adults** (UK Consumer - gap filler for common OTC med)

## 3. Duplicates, Conflicts & Precedence
*   **Dengue Guidelines:** The DGHS 4th Edition explicitly supersedes earlier versions. It takes precedence over the WHO fact sheet for local clinical triage boundaries.
*   **Nipah Virus:** The IEDCR advisory focuses on local behavioral warnings (e.g., date palm sap consumption in winter), which is complementary to the WHO fact sheet's clinical symptom lists. No conflict; they act together.
*   **Malaria Guidelines:** DGHS protocols map specific endemic zones in the Chittagong Hill Tracts, taking precedence over generalized WHO protocols for Bangladesh queries.

## 4. Licensing & Access Uncertainties (NEEDS_REVIEW)
We cannot assume a public URL grants legal permission to scrape, copy, and vectorize content into a commercial or public-facing LLM application.
*   **DGHS / IEDCR:** Standard government public documents. However, explicit terms allowing automated redistribution or vectorization are not published.
*   **WHO:** Copyrighted. Non-commercial reproduction is generally permitted with attribution, but exact terms regarding AI ingestion and embedding storage must be legally verified.
*   **NHS:** Generally governed by the Open Government Licence (OGL), but the specific scraping policies of the NHS.uk website require verification.
*   *Action:* All 12 documents remain in `NEEDS_REVIEW` status.

## 5. Remaining Research Gaps
While this candidate set covers major endemic diseases and emergency boundaries, several gaps remain for the initial target list:
*   **Snakebite Management:** Highly relevant for rural Bangladesh. Requires the official DGHS Snakebite Management Guidelines.
*   **Maternal and Neonatal Health:** No documents currently included.
*   **Local Mental Health:** Currently relying on WHO generic sheets. A validated BD-specific crisis resource (e.g., Kaan Pete Roi guidelines) may be necessary to augment the WHO baseline.

## 6. Stop Condition Enforced
*   **Ingestion:** NOT STARTED
*   **Embeddings/Chunking:** NOT STARTED
*   **Vector DB Selection:** NOT STARTED
*   **Architecture Modification:** NOT MODIFIED
