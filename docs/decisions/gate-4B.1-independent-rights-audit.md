# Gate 4B.1: Independent Source & Rights Audit

> **Status:** AUDIT COMPLETE (STOPPED)
> **Purpose:** Independently verify copyright, access, and AI embedding rights for all knowledge candidates.
> **Constraint Enforced:** No ingestion, downloading, vectorization, or architecture changes have occurred.

## 1. Final Source-by-Source Classification Table

| Source ID | Publisher | Document | Classification |
|---|---|---|---|
| DOC-DGHS-001 | DGHS | Dengue Clinical Management (4th Ed) | `NEEDS_LEGAL_OR_RIGHTS_REVIEW` |
| DOC-WHO-001 | WHO | Cholera Fact Sheet | `RESEARCH_ONLY` |
| DOC-WHO-002 | WHO | Nipah virus Fact Sheet | `RESEARCH_ONLY` |
| DOC-IEDCR-001 | IEDCR | Nipah Virus Advisory | `NEEDS_LEGAL_OR_RIGHTS_REVIEW` |
| DOC-WHO-003 | WHO | Depression Fact Sheet | `RESEARCH_ONLY` |
| DOC-WHO-004 | WHO | Suicide Fact Sheet | `RESEARCH_ONLY` |
| DOC-NHS-001 | NHS | Heat exhaustion and heatstroke | `NEEDS_LEGAL_OR_RIGHTS_REVIEW` |
| DOC-NHS-002 | NHS | Paracetamol for adults | `NEEDS_LEGAL_OR_RIGHTS_REVIEW` |
| DOC-DGHS-002 | DGHS | Malaria Elimination Guidelines | `NEEDS_LEGAL_OR_RIGHTS_REVIEW` |
| DOC-WHO-005 | WHO | Tuberculosis Fact Sheet | `RESEARCH_ONLY` |
| DOC-NHS-003 | NHS | First aid - Choking | `NEEDS_LEGAL_OR_RIGHTS_REVIEW` |
| DOC-WHO-006 | WHO | Rabies Fact Sheet | `RESEARCH_ONLY` |
| DOC-DGHS-003 | DGHS | Snakebite Strategy | `NEEDS_LEGAL_OR_RIGHTS_REVIEW` |
| DOC-DGHS-004 | DGHS | Animal Bite Management | `NEEDS_LEGAL_OR_RIGHTS_REVIEW` |

## 2. Exact Evidence for Classifications

### World Health Organization (WHO) (6 Documents)
*   **Classification:** `RESEARCH_ONLY`
*   **Evidence:** `https://www.who.int/about/policies/publishing/copyright`
*   **Permissions:** Local acquisition, storage, and text extraction are permitted *strictly* for non-commercial purposes under CC BY-NC-SA 3.0 IGO.
*   **Restrictions:** Commercial deployment is explicitly prohibited without prior written authorization. Furthermore, AI chunking/vectorization likely constitutes an "adaptation," triggering the ShareAlike clause, which would legally require the resulting vector database to also be distributed under CC BY-NC-SA 3.0. AI extraction is not explicitly banned, but commercial deployment is a hard blocker.
*   **Third-Party Content:** WHO policies warn that users bear sole responsibility for clearing third-party materials (e.g., charts, photos) embedded in WHO documents.

### National Health Service (NHS, UK) (3 Documents)
*   **Classification:** `NEEDS_LEGAL_OR_RIGHTS_REVIEW`
*   **Evidence:** `https://www.nhs.uk/about-us/terms-and-conditions/` and standard OGL v3.0 limits.
*   **Permissions/Restrictions:** While text is nominally covered by the Open Government Licence (OGL v3.0, allowing commercial use), NHS website terms of use dictate that scraping or bulk syndication requires an explicit NHS API Syndication agreement. Extracting website text into an AI retrieval database without API clearance violates access policies, even if the underlying text is OGL.
*   **Attribution/Logos:** NHS logos and trademarks are strictly excluded and cannot be extracted.

### Bangladesh Government Sources (DGHS, IEDCR) (5 Documents)
*   **Classification:** `NEEDS_LEGAL_OR_RIGHTS_REVIEW`
*   **Evidence:** Standard copyright notices on `dghs.gov.bd`.
*   **Permissions/Restrictions:** No open data license (e.g., Creative Commons) is affixed to these documents. Under standard Bangladesh copyright law, the government retains strict copyright. Local acquisition, text extraction, chunking, embedding, and AI retrieval are legally unverified and presumed prohibited for commercial LLM deployment without explicit, written clearance from the DGHS Management Information System (MIS).

## 3. Contradictions & Corrections to Gate 4B
*   **Correction to NHS Findings:** Gate 4B previously approved NHS documents based on the OGL. **Correction:** Independent verification of the NHS *website access terms* reveals that scraping for syndication bypasses their required API framework. NHS documents must be demoted from `APPROVED` to `NEEDS_LEGAL_OR_RIGHTS_REVIEW`.
*   **Correction to WHO Findings:** Gate 4B approved WHO for non-commercial ingestion. **Correction:** Due to the risk of "ShareAlike" infecting the vector database and the explicit future commercial intent of the project, WHO documents are strictly downgraded to `RESEARCH_ONLY` (sandbox testing). They cannot be approved for a production pipeline.

## 4. Smallest Defensible Ingestion Set
**Zero (0) Documents for Production.**
*   None of the 14 candidates possess explicit, verified legal clearance for scraping, chunking, embedding, and commercial AI retrieval. 
*   **For isolated R&D Sandbox only:** The 6 WHO documents can be used strictly offline for `RESEARCH_ONLY` to test chunking logic, provided the resulting database is destroyed or never commercialized.

## 5. Unresolved Risks
*   **ShareAlike Vector Infection:** It is legally unresolved whether embedding CC BY-NC-SA text turns the proprietary RAG vector database into a derivative work that must be open-sourced.
*   **Commercial Blocker:** The project has no legal path to a commercial launch if it relies on scraping WHO (commercial ban) or NHS (API ban) without securing formal partnership agreements.
*   **Local Clinical Vacuum:** Because DGHS strictly controls its copyright, the system cannot legally ingest Bangladesh's own clinical guidelines without explicit government partnership, leaving the AI without authorized local medical boundaries.

## 6. Recommendation for Next Gate
**Gate 4C — Legal Partnership & API Strategy.**
*   **Stop scraping.** Do not proceed with technical document ingestion.
*   The project must transition from a "PDF scraping" strategy to an "API and Licensing" strategy.
*   We must establish contact with DGHS for permission, apply for the NHS Syndication API, and submit formal licensing requests to the WHO for AI use.
