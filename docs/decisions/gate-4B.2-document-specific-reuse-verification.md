# Gate 4B.2: Document-Specific Reuse Verification

> **Status:** AUDIT COMPLETE (STOPPED)
> **Purpose:** Correct previous rights assumptions and verify reuse rules at the specific document/page level. No documents have been ingested or chunked.

## 1. Document-by-Document Classifications

| Source ID | Publisher | Document | Classification | Explicit Licence |
|---|---|---|---|---|
| DOC-NHS-001 | NHS | Heat exhaustion and heatstroke | `APPROVED_FOR_PRODUCTION_REUSE` | Open Government Licence v3.0 |
| DOC-NHS-002 | NHS | Paracetamol for adults | `APPROVED_FOR_PRODUCTION_REUSE` | Open Government Licence v3.0 |
| DOC-NHS-003 | NHS | First aid - Choking | `APPROVED_FOR_PRODUCTION_REUSE` | Open Government Licence v3.0 |
| DOC-WHO-001 | WHO | Cholera Fact Sheet | `APPROVED_FOR_NONCOMMERCIAL_RESEARCH_ONLY` | CC BY-NC-SA 3.0 IGO |
| DOC-WHO-002 | WHO | Nipah virus Fact Sheet | `APPROVED_FOR_NONCOMMERCIAL_RESEARCH_ONLY` | CC BY-NC-SA 3.0 IGO |
| DOC-WHO-003 | WHO | Depression Fact Sheet | `APPROVED_FOR_NONCOMMERCIAL_RESEARCH_ONLY` | CC BY-NC-SA 3.0 IGO |
| DOC-WHO-004 | WHO | Suicide Fact Sheet | `APPROVED_FOR_NONCOMMERCIAL_RESEARCH_ONLY` | CC BY-NC-SA 3.0 IGO |
| DOC-WHO-005 | WHO | Tuberculosis Fact Sheet | `APPROVED_FOR_NONCOMMERCIAL_RESEARCH_ONLY` | CC BY-NC-SA 3.0 IGO |
| DOC-WHO-006 | WHO | Rabies Fact Sheet | `APPROVED_FOR_NONCOMMERCIAL_RESEARCH_ONLY` | CC BY-NC-SA 3.0 IGO |
| DOC-DGHS-001 | DGHS | Dengue Clinical Management (4th Ed) | `RIGHTS_UNCLEAR` | None attached to PDF |
| DOC-DGHS-002 | DGHS | Malaria Elimination Guidelines | `RIGHTS_UNCLEAR` | None attached to PDF |
| DOC-DGHS-003 | DGHS | Snakebite Strategy | `RIGHTS_UNCLEAR` | None attached to PDF |
| DOC-DGHS-004 | DGHS | Animal Bite Management | `RIGHTS_UNCLEAR` | None attached to PDF |
| DOC-IEDCR-001 | IEDCR | Nipah Virus Advisory | `RIGHTS_UNCLEAR` | None explicitly stated |

## 2. Exact Evidence & Reuse Permissions

### National Health Service (NHS, UK)
*   **Exact Licence:** Open Government Licence (OGL) v3.0.
*   **Permitted Operations:** Copying, storing, transforming, chunking, and incorporation into both commercial and non-commercial applications.
*   **Required Attribution:** Must state "Contains information from NHS England, licensed under the current version of the Open Government Licence."
*   **Exclusions:** NHS logos, trademarks, and third-party content (e.g., specific stock images) are explicitly excluded from the OGL and must be stripped before ingestion.
*   **Technical Access:** No specific technical blocker prevents manual or respectful automated downloading of OGL content. (The syndication API is a service offering, not a revocation of OGL text rights).

### World Health Organization (WHO)
*   **Exact Licence:** CC BY-NC-SA 3.0 IGO.
*   **Permitted Operations:** Copying, storing, transforming, chunking, and incorporation into non-commercial applications.
*   **Commercial Reuse:** Explicitly prohibited by the NonCommercial (NC) clause.
*   **Attribution:** Standard WHO attribution required.
*   **Unresolved Legal Interpretations:** Whether transforming text into vector embeddings constitutes an "adaptation" that triggers the ShareAlike (SA) clause is legally unsettled. Until legal precedent clarifies this, we record the interaction between CC-SA and vector databases as an unresolved legal interpretation rather than a strict technical prohibition.

### Bangladesh Government Sources (DGHS, IEDCR)
*   **Exact Licence:** No open licence (such as CC or OGL) is stated on the documents.
*   **Permitted Operations:** Unverified. 
*   **Commercial Reuse:** Unverified.
*   **Unresolved Legal Interpretations:** While they are government documents intended for public dissemination, the absence of an explicit open licence means their reuse status is legally ambiguous (`RIGHTS_UNCLEAR`). They are not definitively "prohibited", but cannot be safely assumed open.

## 3. Corrections to Gate 4B.1
1.  **NHS Syndication:** Gate 4B.1 incorrectly concluded that NHS documents were blocked from commercial ingestion without an API agreement. **Correction:** The text of the NHS website is explicitly licensed under OGL v3.0, which allows commercial extraction and reuse. The syndication API is the *preferred* delivery mechanism, but does not invalidate OGL rights to the published text.
2.  **WHO ShareAlike Infection:** Gate 4B.1 incorrectly asserted that embedding CC BY-NC-SA content automatically forces the entire vector database to become open-source. **Correction:** The legal classification of vector embeddings as derivative works under Creative Commons is genuinely unsettled globally. This is an unresolved legal interpretation, not a verified prohibition.
3.  **DGHS/IEDCR Impossibility:** Gate 4B.1 stated it was "legally impossible" to ingest Bangladesh guidelines. **Correction:** The lack of an open licence simply renders the rights unverified and unclear (`RIGHTS_UNCLEAR`), which warrants caution but is not an absolute legal impossibility if fair use or specific government open-data norms are later established.

## 4. Minimum Defensible Ingestion Sets

*   **Smallest Defensible Production-Capable Set:** 3 Documents (NHS Heatstroke, Paracetamol, Choking). These have explicit OGL clearance permitting commercial reuse and adaptation.
*   **Smallest Defensible Research-Only Set:** 9 Documents. (3 NHS OGL documents + 6 WHO CC BY-NC-SA documents). This provides a substantial dataset for offline RAG chunking and semantic testing.

## 5. Explicit Permission Necessary
Explicit legal permission is necessary for:
*   Commercializing any system containing WHO (CC BY-NC-SA) content.
*   Ingesting DGHS/IEDCR content into a production system, until their open-data status is officially clarified.

## 6. Recommendation for Next Gate
**Gate 4C — Technical Ingestion & Chunking Strategy.**
With a cleared production-capable set (NHS) and a robust research-only set (WHO), the project can now proceed to design the ingestion pipeline, select chunking strategies, and establish the vector database structure without modifying the governing documents or deploying commercial code.
