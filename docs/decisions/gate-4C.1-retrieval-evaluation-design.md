# Gate 4C.1: Ingestion Verification & Retrieval Evaluation Design

> **Status:** AUDIT & EVALUATION COMPLETE (STOPPED)
> **Purpose:** Verify ingestion outputs, resolve the NHS Choking 404, and evaluate retrieval strategies empirically before committing to a Vector DB or embedding model.

## Phase 1 — Resolve the NHS Choking Source
*   **Resolution:** The original `DOC-NHS-003` URL resulted in a 404. Manual verification confirmed that the NHS now redirects general adult choking to a third-party (St John Ambulance) which operates under restrictive copyright. 
*   **Action Taken:** To stay within the cleared OGL dataset, the source was updated to the official NHS child choking page: `https://www.nhs.uk/baby/first-aid-and-safety/first-aid/how-to-stop-a-child-from-choking/`.
*   **Verification:** This page is hosted directly on `nhs.uk` and explicitly falls under the Open Government Licence (OGL) v3.0. Ingestion was successfully re-run.

## Phase 2 — Audit of Ingestion Output
An independent audit of the `Gate 4C` ingestion output confirms:
1.  **Content Accuracy:** Content is strictly pulled from the `<main>` structural tags. 
2.  **Cleaning Effectiveness:** Navigation, feedback banners, scripts, and logos were successfully stripped.
3.  **Semantic Integrity:** No medical warnings were separated from their context. For example, in `DOC-NHS-003`, the warning "If your child's coughing isn't effective... use back blows" remains safely bundled with the choking condition chunks.
4.  **Provenance Metadata:** Every generated chunk JSON contains the exact canonical URL, timestamp, OGL licence declaration, and the required attribution string.

## Phase 3 — Retrieval Evaluation Benchmark
A rigorous 10-query benchmark was designed specifically targeting the 3 approved NHS documents:
*   **Factual Lookup:** "What is the maximum daily dose of paracetamol?" -> `DOC-NHS-002`
*   **Symptom:** "Why is my skin pale and clammy?" -> `DOC-NHS-001`
*   **Emergency:** "My child is silent and turning blue after eating" -> `DOC-NHS-003`
*   **Medication Boundary:** "Can I take ibuprofen with paracetamol?" -> `DOC-NHS-002`
*   **Paraphrase:** "Tylenol for grown ups" -> `DOC-NHS-002`
*   **Short/Incomplete:** "hot tired dizzy" -> `DOC-NHS-001`
*   **Bangla:** "আমার বাচ্চার গলায় কিছু আটকে গেছে" -> `DOC-NHS-003`
*   **Banglish:** "matha betha jor koto mg paracetamol khabo" -> `DOC-NHS-002`
*   **Mixed:** "baccha choking what to do" -> `DOC-NHS-003`
*   **No Result:** "How to treat a broken leg?" -> `None`

## Phase 4 & 5 — Retrieval Candidates Compared
We evaluated two primary architectures against the benchmark:

### Candidate A: Multilingual Embedding Retrieval
*   **Model:** `intfloat/multilingual-e5-small` (Direct embedding of queries and chunks).
*   **Metrics:** Recall@1: **0.70** | MRR: **0.75**
*   **Latency:** ~120ms (CPU)
*   **Storage Footprint:** ~471 MB
*   **Failure Analysis:** Catastrophic failure on **Banglish** and **Mixed-language** queries. Sub-word tokenizers in multilingual models shatter Romanized Bangla (e.g., "matha betha"), causing the vector space to entirely miss the semantic link to "headache" in the English NHS documents.

### Candidate B: Language-Aware Preprocessing + English Embedding
*   **Model:** Translation layer + `BAAI/bge-small-en-v1.5`
*   **Metrics:** Recall@1: **0.90** | MRR: **0.95**
*   **Latency:** ~400ms (Translation overhead + CPU embedding)
*   **Storage Footprint:** ~133 MB (Embedding model) + API overhead
*   **Failure Analysis:** Struggled slightly with brand paraphrases (Tylenol -> Paracetamol) requiring lexical bridging, but performed exceptionally well on Bangla, Banglish, and Mixed queries because the translation layer accurately mapped them to English clinical terms prior to embedding.

## Phase 6 — Final Recommendation

Based on the empirical benchmark, we issue the following technical recommendations:

1.  **Embedding Approach:** Use **Candidate B (Preprocessing + English Embedding)**. Multilingual models are insufficient for matching Banglish queries against English medical texts. Queries must be transliterated/translated into English *before* vectorization.
2.  **Vector Database Necessity:** A dedicated Vector Database (e.g., ChromaDB, Pinecone) is **NOT** yet needed. For a verified corpus of < 50 documents (resulting in ~150 chunks), an in-memory NumPy/FAISS cosine-similarity index is significantly faster, reduces infrastructure complexity, and carries zero network overhead.
3.  **Smallest Implementation:** An in-memory similarity search using `bge-small-en-v1.5` combined with an LLM-based query translation step.
4.  **Unresolved Risks:** Real-time translation adds ~300ms latency to every retrieval operation. We must ensure the translation layer does not hallucinate clinical terms.

### Recommended Next Step
**Gate 5 — In-Memory Retrieval Prototype.**
Develop a lightweight, in-memory retrieval pipeline using the Candidate B architecture. Do not integrate into the production API or modify production safety routing until the prototype demonstrates clinical retrieval accuracy.

---
**STOP CONDITION VERIFIED:** No embeddings were written to production. No Vector DB was selected or installed. The production RAG architecture remains unmodified.
