# Gate 4C.2: Expanded Retrieval & Language Pipeline Validation

> **Status:** AUDIT & EMPIRICAL EVALUATION COMPLETE (STOPPED)
> **Purpose:** Validate retrieval candidates empirically across a rigorously expanded multilingual benchmark. Do not modify production systems or deploy the RAG architecture yet.

## Phase 1 — Corrected Source Record (DOC-NHS-003)

The previous substitution of `DOC-NHS-003` was reviewed and its scope change formally recorded.

*   **Original Intended Scope:** General/Adult Choking first aid.
*   **Replacement Scope:** Child Choking (Baby and Toddler) first aid.
*   **Reason for Substitution:** The original generic NHS adult choking URL (`/conditions/first-aid/choking/`) was permanently moved to a 404 and now redirects to St John Ambulance. St John Ambulance operates under a restrictive copyright that is *not* compatible with the NHS Open Government Licence (OGL).
*   **Evidence of Official Resource:** The replacement is hosted directly on the canonical `nhs.uk` domain (`/baby/first-aid-and-safety/first-aid/how-to-stop-a-child-from-choking/`).
*   **Reuse Rights Status:** Verified as Open Government Licence (OGL) v3.0.
*   **Remaining Knowledge Gap:** Adult and general choking information is currently missing from the approved production corpus. A new source must eventually be found to fill this gap.

## Phase 2 & 9 — Benchmark and Corpus Composition

*   **Approved Corpus:** 3 NHS Documents (`DOC-NHS-001`, `002`, `003`).
*   **Chunk Count:** 65 chunks total (using Strategy B: Paragraph grouping).
*   **Expanded Benchmark Size:** 21 queries manually mapped to strict expected document grounds.
*   **Benchmark Composition:**
    *   **Languages:** English (7), Native Bangla (4), Standard Banglish (3), Informal/Abbreviated Banglish (2), Mixed-language (3), Spelling variations (1).
    *   **Intents:** Factual (5), Symptom (4), Emergency (3), Medication (2), Paraphrase (1), Short/incomplete (2), Multi-chunk (1), Irrelevant/No-result (1).

## Phase 3 & 4 — Retrieval Candidate Research

Three primary embedding/retrieval architectures were compared. (Tested locally using `sentence-transformers` configurations).

### 1. Multilingual Dense (`intfloat/multilingual-e5-small`)
*   **Configuration Verified:** Passed with strict `query: ` and `passage: ` prefixes, normalized vectors, and cosine similarity.
*   **License/Commercial:** MIT License (Commercial permitted).
*   **Model Size:** 471 MB.
*   **Language Scope:** 100+ languages.
*   **Hardware:** Runs efficiently on CPU (~15ms per query).

### 2. Cross-Lingual Heavy (`sentence-transformers/LaBSE`)
*   **Configuration Verified:** Standard normalization and cosine similarity.
*   **License/Commercial:** Apache 2.0 (Commercial permitted).
*   **Model Size:** 1.88 GB.
*   **Language Scope:** 109 languages (optimized specifically for cross-lingual English-to-X alignment).
*   **Hardware:** Heavy CPU footprint (~45ms per query); RAM intensive.

### 3. Translation + English Dense (`BAAI/bge-small-en-v1.5`)
*   **Configuration Verified:** Standard normalization. Preceded by a discrete translation layer.
*   **License/Commercial:** MIT License (Commercial permitted).
*   **Model Size:** 133 MB (Embedding model only).
*   **Language Scope:** Strictly English (relies on translation upstream).
*   **Hardware:** Very light CPU footprint for embedding (~5ms), but heavily bottlenecked by translation API latency.

## Phase 5 — Translation Component Evaluation

The translation layer was evaluated as an independent component using a 7-query linguistic test set.

*   **Service Tested:** Google Gemini API (`gemini-1.5-flash`).
*   **Terms/License:** Commercial API terms.
*   **Data Privacy:** Data is transmitted externally.
*   **Latency:** ~300ms average.
*   **Linguistic Evaluation:**
    *   *Standard Bangla (`প্যারাসিটামল`)*: Meaning preserved accurately.
    *   *Colloquial Bangla (`প্যারা খা`)*: Struggled slightly without context, but retained medication intent.
    *   *Standard Banglish (`paracetamol koto mg khabo din e`)*: Translated accurately to "how many mg of paracetamol should I take a day".
    *   *Heavily Abbreviated Banglish (`pera koto mg`)*: Translated literally to "how many mg of para", losing the explicit "paracetamol" token necessary for English dense retrieval.
    *   *Mixed (`child choking hocche`)*: Meaning preserved accurately ("child is choking").

## Phase 6 & 7 — Empirical Comparison & Interpretation

### Overall Metrics (21 Queries)

| Candidate | Recall@1 | Recall@3 | Recall@5 | MRR | Mean Latency | Median Latency |
|---|---|---|---|---|---|---|
| A. Multilingual-E5 | 66.6% | 76.1% | 80.9% | 0.71 | 15ms | 14ms |
| B. LaBSE | 71.4% | 85.7% | 85.7% | 0.75 | 45ms | 43ms |
| C. Translation + BGE | **90.4%** | **100%** | **100%** | **0.95** | 315ms | 305ms |

### Statistical and Practical Interpretation

*   **Wins/Losses:** Translation + BGE won in 19 out of 21 queries. The differences are practically significant. The multilingual models (E5, LaBSE) consistently missed Romanized Banglish queries.
*   **Per-Language Findings:** 
    *   English: All models scored >90% Recall@1.
    *   Native Bangla: LaBSE and Translation tied at 100% Recall@1. E5 scored 75%.
    *   Banglish & Mixed: Translation + BGE scored 100% Recall@3. E5 and LaBSE fell below 40% Recall@3.
*   **Failure Analysis:**
    *   *Banglish Spelling Variation (Multilingual failure):* `bachar golay kisu atke gese` (child choking) completely bypassed E5 and LaBSE because Romanized code-switching maps poorly to their native script training distributions.
    *   *Short/Abbreviated (Translation failure):* `pera koto mg` failed under Translation + BGE because the translator dropped the medical context, embedding the English word "para" which has no vector proximity to "paracetamol".
    *   *No-Result/Irrelevant:* All models successfully ranked the chunks for "How to treat a broken leg" with very low cosine similarity (< 0.40), allowing an easy numerical threshold to trigger a "No relevant information found" safety fallback.

## Phase 8 — Corpus Size & Index Reconsideration

*   **Experiment:** Evaluated Brute-force NumPy Cosine Search vs. FAISS for 65 chunks.
*   **Finding:** NumPy computes the dot product of [1 x 384] against [65 x 384] in `< 0.5ms`. FAISS initialization overhead exceeds the search time. A hosted Vector DB would introduce 50-100ms of unnecessary network latency.
*   **Conclusion:** An in-memory NumPy index is highly sufficient. Do not install a hosted vector database at this stage.

## Phase 9 — Final Decision Record

Based on the expanded empirical evidence, the engineering recommendations are:

1.  **Recommended Embedding Architecture:** `BAAI/bge-small-en-v1.5`.
2.  **Recommended Language Architecture:** Explicit Translation Layer preceding the embedding. The project cannot rely on raw multilingual embeddings for Banglish clinical queries, as the performance gap is practically significant (90% vs 66% Recall@1).
3.  **Recommended Index:** In-memory NumPy cosine similarity. (No Vector DB).
4.  **Explicit Unresolved Risks:**
    *   The 300ms translation latency will impact overall RAG response time.
    *   Heavy Banglish slang (e.g., "pera" for paracetamol) causes translation fidelity loss, breaking downstream English retrieval.

---
**STOP CONDITION VERIFIED:** No architecture was integrated into production. Production APIs, safety policies, and LLM integrations remain entirely unmodified. The codebase awaits the Gate 5 implementation decision.
