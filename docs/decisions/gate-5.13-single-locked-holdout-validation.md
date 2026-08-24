# Gate 5.13 — Single Locked Holdout Validation of the Normalized Retrieval Pipeline

> **Status:** RETRIEVAL_NORMALIZATION_PARTIALLY_GENERALIZES

---

## 1. Executive Summary & Verification

In Gate 5.12, development-only failure analysis selected **Candidate 2 (Deterministic Clinical Concept Normalization + Multilingual-E5 Dense Top-15 + BGE Reranker Top-5)**, which achieved 87.5% Chunk Recall@5 on the 40 DEV queries.

In **Gate 5.13**, this exact frozen configuration was evaluated **EXACTLY ONCE** on the untouched **Locked Holdout Split** (`DOC-NHS-008` to `DOC-NHS-011` + 40 test queries).

### Exact Hash & Configuration Verification:
- **Frozen Benchmark Hash**: `7debd4b7d804938d4c7ecf8f414f51d936830b5a6d9d62ebfcaedde1874c8a81` — **[VERIFIED]**
- **Frozen Configuration Hash**: `3318ae3bd1b671a99e98a07e46911d41c0fe8d872e4fa5a4b6d8bfaad8873f28` — **[VERIFIED]**
- **Zero Modifications**: No normalization rule, candidate depth (\(K=15\)), reranker model, passage representation, or test query was altered.

---

## 2. Empirical Holdout Results & Cross-Gate Comparison

### Aggregate Chunk-Level & Source-Level Performance:

| Evaluation Phase / Model Configuration | Candidate Depth | Candidate R@15 | Final Chunk R@1 | Final Chunk R@3 | **Final Chunk R@5 (Primary)** | Final Chunk MRR | Source-Level R@1 | Source-Level R@5 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Gate 5.10 DEV Baseline** | K=5 | 22/40 (55.0%) | 15/40 (37.5%) | 20/40 (50.0%) | **22/40 (55.0%)** | 0.4350 | 29/40 (72.5%) | 35/40 (87.5%) |
| **Gate 5.11 Holdout Baseline** | K=15 | 31/40 (77.5%) | 11/40 (27.5%) | 18/40 (45.0%) | **20/40 (50.0%)** | 0.3583 | 32/40 (80.0%) | 39/40 (97.5%) |
| **Gate 5.12 DEV (Normalized)** | K=15 | 37/40 (92.5%) | 19/40 (47.5%) | 27/40 (67.5%) | **35/40 (87.5%)** | 0.6104 | 36/40 (90.0%) | 40/40 (100.0%) |
| **Gate 5.13 HOLDOUT (Normalized)** 🎯 | **K=15** | **34/40 (85.0%)** | **10/40 (25.0%)** | **14/40 (35.0%)** | **21/40 (52.5%)** | **0.3358** | **33/40 (82.5%)** | **39/40 (97.5%)** |

---

## 3. Linguistic Breakdown on Locked Holdout (N=40)

| Language Category | Holdout N | Gate 5.11 Candidate R@15 | **Gate 5.13 Candidate R@15** | Gate 5.11 Final Chunk R@5 | **Gate 5.13 Final Chunk R@5** | Gate 5.11 MRR | **Gate 5.13 MRR** |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **English** | 12 | 11/12 (91.67%) | **11/12 (91.67%)** | 7/12 (58.33%) | **6/12 (50.00%)** | 0.4417 | **0.3917** |
| **Native Bangla** | 11 | 9/11 (81.82%) | **10/11 (90.91%)** | 7/11 (63.64%) | **8/11 (72.73%)** | 0.4121 | **0.4121** |
| **Standard Banglish** | 9 | 7/9 (77.78%) | **8/9 (88.89%)** | 4/9 (44.44%) | **5/9 (55.56%)** | 0.2889 | **0.3333** |
| **Abbreviated Banglish** | 8 | 4/8 (50.00%) | **5/8 (62.50%)** | 2/8 (25.00%) | **2/8 (25.00%)** | 0.2375 | **0.1500** |

---

## 4. Failure Decomposition Analysis (Holdout N=40)

### Evidence Availability Breakdown:
- **`TOP1_CORRECT`**: **10 / 40 (25.00%)** — Gold evidence chunk ranked at Rank 1.
- **`TOP1_WRONG_BUT_TOP3_HAS_GOLD`**: **4 / 40 (10.00%)** — Gold chunk available within Top-3 context.
- **`TOP3_WRONG_BUT_TOP5_HAS_GOLD`**: **7 / 40 (17.50%)** — Gold chunk available within Top-5 context.
- **`GOLD_ABSENT_FROM_TOP5`**: **19 / 40 (47.50%)** — Gold chunk absent from final Top-5 context.

### Dense Retrieval vs Reranker Loss:
- **`GOLD_RETAINED_IN_TOP5`**: **21 / 40 (52.50%)** — Successfully delivered to downstream LLM.
- **`GOLD_IN_DENSE15_BUT_LOST_AFTER_RERANK`**: **13 / 40 (32.50%)** — Dense retrieved gold in Top-15 (ranks 2–14), but cross-encoder reranker demoted it to ranks 6–15.
- **`GOLD_OUTSIDE_DENSE15`**: **6 / 40 (15.00%)** — Dense embedding failed to capture chunk in Top-15 pool.

---

## 5. Critical Diagnostic Insights

1. **Candidate Retrieval Generalization Succeeded**:
   - Dense Candidate Recall@15 reached **34/40 (85.00%)**, up from 77.50% in Gate 5.11.
   - Standard Banglish candidate pool recall reached **88.89% (8/9)**.
   - Native Bangla candidate pool recall reached **90.91% (10/11)**.
   - **Only 6 queries out of 40 suffered from dense candidate starvation.**

2. **The Core Bottleneck is Cross-Encoder Overview Demotion**:
   - In **13 queries (32.50% of the entire holdout set)**, the ground-truth evidence chunk was present inside the Top-15 candidate pool, but the cross-encoder reranker (`bge-reranker-v2-m3`) ranked general introductory chunks (e.g. `DOC-NHS-008-HYB-000` / `DOC-NHS-010-HYB-000`) ahead of specific treatment rules (e.g. `DOC-NHS-008-HYB-002` fluid rehydration advice or `DOC-NHS-010-HYB-003` paracetamol temperature management).
   - Because the reranker has a strong generic semantic affinity to broad medical topic overviews, specific sub-rules get pushed to ranks 6–10.

3. **Why DEV (87.5%) Overestimated Holdout (52.5%)**:
   - The deterministic query normalization rules successfully translated clinical concepts, but holdout documents (`DOC-NHS-008` Diarrhoea & Vomiting, `DOC-NHS-010` High Temperature in Children) have larger numbers of overlapping topical chunks per document (7–9 chunks) compared to DEV documents (5–7 chunks).
   - In a larger document cluster, cross-encoder scores for multiple competing chunks in the same document compress into a narrow band (0.80–0.95), pushing specific evidence outside the Top-5 threshold.

---

## 6. Unsupported Query Safety Validation (20 Queries)

Evaluated across 12 Hard Negatives and 8 Out-of-Corpus queries:
- **Maximum Reranker Top-1 Score**: **0.5035** (on `HN-01` tourniquet inquiry).
- **Minimum Reranker Top-1 Score**: **0.000045** (on `OOC-05` diabetes insulin pump).
- **Average Reranker Top-1 Score**: **0.1027** (vs >0.80 on valid supported queries).
- **Conclusion**: The reranker produces low confidence scores for out-of-scope queries, providing a safe thresholding margin (\(\tau \approx 0.55\)) for the safety router.

---

## 7. Latency and Hardware Profile

- **Passage Encoding (68 chunks)**: 5.03s (one-time index build)
- **Average Query Encoding**: 51.64 ms
- **Average Dense Dot Product Search**: 0.11 ms
- **Average Top-15 Cross-Encoder Rerank**: 16.66 s (CPU)
- **Total Latency per Query**: ~16.71 s on CPU (expected to be <300 ms on GPU).

---

## 8. Final Status & Next Step Recommendation

### Final Gate Status:
**`RETRIEVAL_NORMALIZATION_PARTIALLY_GENERALIZES`**

### Summary of Reality:
- Dense candidate pool availability is now solid (**85.0% on holdout, 92.5% on DEV**).
- Native Bangla Top-5 Evidence availability is high (**72.73%**).
- Standard Banglish Top-5 Evidence availability is moderate (**55.56%**).
- However, **47.5% of unseen queries still lack the gold evidence chunk in Top-5 context**, with **68.4% of those failures (13/19) caused by cross-encoder overview chunk demotion**.

### Actionable Next Step:
Before connecting an LLM, the remaining architecture bottleneck must be solved:
1. **Context Expansion / Chunk Packing**: Instead of Top-5 isolated chunks, concatenate parent section context or pass Top-8 chunks to the LLM context.
2. **Overview Chunk Suppression / Diversity Reranking (MMR)**: Penalize redundant overview chunks from the same document when a specific section chunk is present.
3. **Gate 5.14 / Gate 7 Exploration**: Evaluate diversity-aware context window formatting before production LLM integration.

---
**ABSOLUTE STOP CONDITION REACHED**: Gate 5.13 single locked holdout evaluation is completely finished. No production code was modified, no LLM was called, and no unauthorized retries were executed.
