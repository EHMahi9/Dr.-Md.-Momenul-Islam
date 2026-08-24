# Gate 4D.2 — Evidence Correction and Source Approval Audit

> **Status:** SOURCE_SET_APPROVED_FOR_GATE_4E

## 1. Primary Objective
This audit corrects overstatements made in Gate 4D and Gate 4D.1, replacing assumed universal claims with strictly documented evidence. It evaluates 9 candidate NHS documents for ingestion suitability based on precise technical observations and licensing terms, without fabricating legal certainty.

## 2. Methodological Corrections
1. **Semantic Overlap**: The previous claim of "zero semantic overlap" was materially incorrect. Medical documents inherently share terminology (e.g., "doctor", "hospital", "pain"). The correct description is that the new candidates are **topic-disjoint relative to the original corpus** (Asthma vs CPR), introducing intent diversity, though lexical overlap remains.
2. **Zero-Shot Generalization**: Testing on new documents provides a *source-level holdout*. However, this is NOT a "true zero-shot" generalization test unless the queries themselves are also constructed independently. If benchmark queries are written using the same phrasing templates, prompt leakage will artificially inflate accuracy.
3. **Third-Party Content**: The previous audit equated "no iframe found" with "no third-party content." This was a methodological error. A rigorous audit must check for `<video>` tags, images, captions, and embedded modules that may fall outside standard licensing.

## 3. Bleeding Candidate Correction
- **Original URL**: `https://www.nhs.uk/conditions/bleeding/` (Status: 404)
- **Alternative Searches**: NHS site search for "severe bleeding" and direct probes of `/conditions/severe-bleeding/` yielded no direct match or returned 404s.
- **Conclusion**: `NO_SUITABLE_SOURCE_IDENTIFIED_IN_THIS_AUDIT`. (This corrects the previous overstatement that no active bleeding page exists on the NHS universally).

## 4. Document-by-Document Evidence

| Candidate | Status | Redirect Chain | Final URL | Canonical URL | H1 / Scope |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Asthma** | 200 | None | `/conditions/asthma/` | `/conditions/asthma/` | "Asthma" (General population) |
| **Burns** | 200 | None | `/conditions/burns-and-scalds/` | `/conditions/burns-and-scalds/` | "Burns and scalds" (General population) |
| **Cuts** | 200 | None | `/conditions/cuts-and-grazes/` | `/conditions/cuts-and-grazes/` | "Cuts and grazes" (General population) |
| **Dehydration**| 200 | None | `/conditions/dehydration/` | `/conditions/dehydration/` | "Dehydration" (General population) |
| **Diarrhoea** | 200 | `[.../conditions/...]` | `/symptoms/diarrhoea-and-vomiting/` | `/symptoms/diarrhoea-and-vomiting/`| "Diarrhoea and vomiting" (General population) |
| **Headaches** | 200 | `[.../conditions/...]` | `/symptoms/headaches/` | `/symptoms/headaches/` | "Headaches" (General population) |
| **Child Fever**| 200 | `[.../conditions/...]` | `/symptoms/fever-in-children/` | `/symptoms/fever-in-children/` | "High temperature (fever) in children" (Strictly Pediatric) |
| **Anaphylaxis**| 200 | None | `/conditions/anaphylaxis/` | `/conditions/anaphylaxis/` | "Anaphylaxis" (Emergency, General) |
| **Bleeding** | 404 | None | `/conditions/bleeding/` | `NONE` | "Page not found" |

## 5. Licensing and Reuse Audit

**A. VERIFIED FACT**
The official NHS Terms and Conditions explicitly state that health information text on `www.nhs.uk` is covered by the Open Government Licence (OGL) v3.0, allowing commercial and non-commercial reuse. Logos, branding, and third-party media are explicitly excluded from the OGL.

**B. TECHNICAL OBSERVATION**
- Asthma, Dehydration, and Fever in children contain embedded `<video>` elements.
- Cuts and grazes contains outbound text hyperlinks to *St John Ambulance*.
- No `<iframe>` modules from third parties were detected.

**C. ENGINEERING INTERPRETATION**
Because the extraction pipeline will parse only structural text (`<p>`, `<li>`, `<h1>`, `<h2>`) and discard `<video>`, `<img>`, and styling assets, the ingestion process appears compatible with the documented OGL terms. We are not copying the excluded media. Outbound links are standard web references and do not constitute embedded third-party copyright.

**D. UNRESOLVED UNCERTAINTY**
It remains unverified whether the specific `<video>` elements are NHS-owned or third-party-owned. However, because they will be excluded from text extraction, this uncertainty does not block the corpus expansion.

## 6. Final Source Approval Table

| Source | Final URL | Scope | Rights Evidence | Content Risk | Final Classification | Reason |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Asthma** | `.../asthma/` | Chronic | NHS OGL v3.0 | `<video>` element found | `APPROVED_FOR_PLANNED_TEXT_REUSE` | Text extraction isolates OGL-compliant content. |
| **Burns** | `.../burns-and-scalds/` | First Aid | NHS OGL v3.0 | None detected | `APPROVED_FOR_PLANNED_TEXT_REUSE` | Clean textual page. |
| **Cuts** | `.../cuts-and-grazes/`| Minor injury | NHS OGL v3.0 | Hyperlink to St John | `APPROVED_FOR_PLANNED_TEXT_REUSE` | External links do not violate OGL text reuse. |
| **Dehydration** | `.../dehydration/` | Symptoms | NHS OGL v3.0 | `<video>` element found | `APPROVED_FOR_PLANNED_TEXT_REUSE` | Text extraction isolates OGL-compliant content. |
| **Diarrhoea** | `.../symptoms/diarrhoea-and-vomiting/` | Symptoms | NHS OGL v3.0 | None detected | `APPROVED_FOR_PLANNED_TEXT_REUSE` | Clean textual page. |
| **Headaches** | `.../symptoms/headaches/` | Symptoms | NHS OGL v3.0 | None detected | `APPROVED_FOR_PLANNED_TEXT_REUSE` | Clean textual page. |
| **Child Fever** | `.../symptoms/fever-in-children/` | Pediatric | NHS OGL v3.0 | `<video>` element found | `APPROVED_FOR_PLANNED_TEXT_REUSE` | Text extraction isolates OGL-compliant content. |
| **Anaphylaxis** | `.../conditions/anaphylaxis/` | Emergency | NHS OGL v3.0 | None detected | `APPROVED_FOR_PLANNED_TEXT_REUSE` | Clean textual page. |
| **Bleeding** | `.../bleeding/` | N/A | N/A | Dead URL | `REJECTED` | `NO_SUITABLE_SOURCE_IDENTIFIED_IN_THIS_AUDIT` |

## 7. Reproducibility Requirements
- **Script**: `audit_script_4d2.py` (Python `requests` and `re`).
- **Timestamp**: 2026-08-21 18:15 UTC.
- **Official Source Consulted**: `https://www.nhs.uk/about-us/terms-and-conditions/`

## 8. Final Decision
**SOURCE_SET_APPROVED_FOR_GATE_4E**

The 8 valid candidates possess sufficient documentation and evidentiary backing to justify controlled text extraction in a future Gate 4E.

---
**ABSOLUTE STOP CONDITION REACHED**: No documents have been ingested, chunked, or embedded. Retrieval pipelines and production code are untouched. Awaiting user instruction.
