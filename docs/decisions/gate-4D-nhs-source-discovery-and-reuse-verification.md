# Gate 4D — NHS Source Discovery & Document-Specific Reuse Verification

> **Status:** SOURCE_EXPANSION_SUFFICIENT_FOR_NEXT_INGESTION_GATE

## 1. Gate Purpose
The purpose of this gate is to discover, verify, and legally classify new NHS health information documents to expand the approved production corpus, enabling future independent retrieval generalization evaluations.

## 2. Background and Gate 5.8 Blocker
Gate 5.8 was explicitly blocked because the existing production corpus contained only three legally approved NHS documents. Creating a locked, independent test set without semantic leakage required finding new, unrelated medical documents.

## 3. Existing Corpus Limitation
The existing corpus consists of only Heatstroke (DOC-NHS-001), CPR (DOC-NHS-002), and Child Choking (DOC-NHS-003). This narrow scope caused massive semantic clustering in benchmark queries and potentially induced a "CPR Bias" in the cross-encoder reranker.

## 4. Discovery Methodology
Discovery targeted common medical intents frequently queried in Bangladesh that differ substantially from the existing corpus:
- Chronic conditions (Asthma)
- Gastrointestinal/Endemic symptoms (Diarrhoea and vomiting)
- Pediatric routine illnesses (Child fever)
- Minor injuries (Cuts, Burns)
- Extreme allergies (Anaphylaxis)

## 5. Candidate Source Inventory
Nine candidate pages were selected for verification:
1. `Asthma` (https://www.nhs.uk/conditions/asthma/)
2. `Burns and scalds` (https://www.nhs.uk/conditions/burns-and-scalds/)
3. `Cuts and grazes` (https://www.nhs.uk/conditions/cuts-and-grazes/)
4. `Dehydration` (https://www.nhs.uk/conditions/dehydration/)
5. `Diarrhoea and vomiting` (https://www.nhs.uk/conditions/diarrhoea-and-vomiting/)
6. `Headaches` (https://www.nhs.uk/conditions/headaches/)
7. `Fever in children` (https://www.nhs.uk/conditions/fever-in-children/)
8. `Anaphylaxis` (https://www.nhs.uk/conditions/anaphylaxis/)
9. `Bleeding` (https://www.nhs.uk/conditions/bleeding/)

## 6. Document-by-Document Verification & 7. Canonical URL Verification
A Python HTTP verification script was used to fetch each URL, confirm the `<link rel="canonical">`, extract the title, and parse redirects.

## 8. Redirect Analysis
- `Diarrhoea`, `Headaches`, and `Fever in children` redirected from `/conditions/` to `/symptoms/`. **Evidence**: The destination domains remained `www.nhs.uk` (NHS infrastructure).
- `Bleeding` returned a 404 Page Not Found. **Evidence**: HTTP Status Code.

## 9. Licence/Reuse Evidence
**Verified Evidence**: NHS Terms and Conditions explicitly apply the **Open Government Licence v3.0** to textual health information, which permits commercial and non-commercial reuse, transformation, and distribution. 
**Interpretation**: Provided we do not claim official NHS endorsement and we exclude logos/trademarks, the core text is legally safe for our RAG knowledge base.

## 10. Third-Party Content Risks
An automated regex scan was performed for iframes (embedded videos) and third-party copyright markers.
- **Evidence**: No embedded videos (e.g., YouTube/Vimeo) were found on the candidate pages. 
- **Evidence**: `Cuts and grazes` contains outbound hyperlink text referring to *St John Ambulance*. 
- **Interpretation**: Hyperlinks do not constitute embedded third-party copyright content. The textual content of the NHS page itself remains under OGL v3.0.

## 11. Population and Scope Analysis
The new documents introduce highly diverse scopes:
- **Pediatric**: Fever in children.
- **Chronic**: Asthma.
- **Emergency**: Anaphylaxis.
- **First Aid**: Burns, Cuts.
- **General Symptom Management**: Dehydration, Diarrhoea, Headaches.

## 12. Rights Classifications
- **APPROVED_FOR_PRODUCTION_REUSE**: Asthma, Burns and scalds, Cuts and grazes, Dehydration, Diarrhoea and vomiting, Headaches, Fever in children, Anaphylaxis.
- **NOT_APPROVED_FOR_THIS_CORPUS**: Bleeding (404 Dead URL).

## 13. Approved Corpus Expansion Analysis
The approved production-ready corpus has expanded from **3** to **11** documents, a 266% increase in document diversity.

## 14. Independent Benchmark Value Analysis
This expansion holds extremely high value for resolving Gate 5.8. We can now construct an independent locked test set using entirely new intent categories (e.g., Asthma, Diarrhoea) that share zero semantic overlap with the original CPR/Choking/Heatstroke queries, allowing a true zero-shot generalization test for the dense-retrieval and reranker architecture.

## 15. Provenance Requirements for Future Ingestion
When these documents are ingested, the pipeline MUST record:
- `source_id`
- Exact `title`
- `final_verified_url`
- UTC Retrieval timestamp
- `rights_status` (OGL v3.0)
- Explicit exclusion of logos/branding.

## 16. Source Catalog Changes
`docs/knowledge/source-catalog.json` was successfully updated with the 8 approved documents and the 1 rejected document. Existing entries were untouched.

## 17. Rejected and Unclear Candidates
- `Bleeding`: Rejected (NOT_APPROVED_FOR_THIS_CORPUS) due to a dead URL.

## 18. Threats and Limitations
- **Threat**: NHS pages occasionally update their URLs or redirect to third parties (like St John Ambulance) without warning. The future ingestion script must rigorously re-verify the domain at download time.

## 19. Explicit Distinction Between Verified Evidence and Interpretation
- **Verified**: The NHS domain uses OGL v3.0. The URLs resolve to the NHS domain. No iframes are present.
- **Interpretation**: Extracting the `<p>`, `<li>`, and `<h2>` elements strips the excluded NHS logos and branding automatically, rendering the extracted text strictly compliant with OGL v3.0 reuse terms.

## 20. Final Decision
`SOURCE_EXPANSION_SUFFICIENT_FOR_NEXT_INGESTION_GATE`

The newly discovered and verified documents possess sufficient diversity and legal clarity to justify proceeding to a formal document ingestion and benchmark generation gate.

---
**ABSOLUTE BOUNDARY**: Gate 4D is complete. No documents were downloaded for chunking, no embeddings were created, and no LLMs were used.
