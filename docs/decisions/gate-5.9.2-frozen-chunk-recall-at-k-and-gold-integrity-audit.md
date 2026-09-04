# Gate 5.9.2 — Frozen Chunk-Level Recall@K & Gold-Label Integrity Audit

> **Status:** EVIDENCE_MOSTLY_MISSING_FROM_TOP5

---

## 1. Audit Purpose

Gate 5.9.1 established that while the Gate 5.9 frozen pipeline achieved an **85.0% source-level Recall@1** on the locked holdout, it achieved only **20.0% chunk-level Recall@1** due to extensive intra-document chunk mismatches.

The purpose of Gate 5.9.2 is to determine whether this evidence gap is solved by multi-chunk retrieval context (i.e. whether the correct clinical evidence chunk is present within the **Top-3 or Top-5 ranked context**), or whether the evidence is missing from the retrieved context entirely.

All audits were conducted strictly on the **frozen Gate 5.9 retrieval rankings**. No model weights, chunking parameters, Top-K settings, or retrieval code were modified, and no embeddings or rerankers were re-executed.

---

## 2. Gold-Label Integrity Verification

An exhaustive audit of [`chunk_gold_labels.json`](../../research/gate_5_9_optimization/chunk_gold_labels.json) was conducted against the 68 chunks in [`provenance_manifest.json`](../../research/gate_5_9_optimization/chunks/hybrid_600/provenance_manifest.json) and [`frozen_benchmark.json`](../../research/gate_5_8_retrieval_validation/benchmark/frozen_benchmark.json):

- **Total Valid Benchmark Queries Audited**: 80 (40 DEV + 40 LOCKED TEST).
- **Valid Gold Mappings**: **80 / 80 (100.0%)**.
- **Invalid / Non-Existent Chunk References**: **0**.
- **Parent Source Mismatches**: **0** (100% of gold chunk IDs belong to the query's expected parent document).
- **Multiple Acceptable Chunks Represented**: 19 queries (composite queries spanning overview and specific treatment steps).
- **Integrity Status**: **`GOLD_LABELS_100_PERCENT_VALID`**.

---

## 3. Frozen Artifact Reproducibility & Checksums

| Artifact | File Path | SHA-256 Checksum |
| :--- | :--- | :--- |
| **Frozen Benchmark** | `research/gate_5_8_retrieval_validation/benchmark/frozen_benchmark.json` | `7debd4b7d804938d4c7ecf8f414f51d936830b5a6d9d62ebfcaedde1874c8a81` |
| **Frozen Config Manifest** | `research/gate_5_9_optimization/frozen_config_manifest.json` | `c04495e865f128bc5f67ea55b6efcfec6e8ec9ee8109d3b37937fe5d2f33c373` |
| **HYBRID_600 Provenance** | `research/gate_5_9_optimization/chunks/hybrid_600/provenance_manifest.json` | `c04495e865f128bc5f67ea55b6efcfec6e8ec9ee8109d3b37937fe5d2f33c373` |
| **Gate 5.9 Eval JSON** | `research/gate_5_9_optimization/evaluations/gate_5_9_locked_holdout_evaluation.json` | `dffb3bb9dcf4fcfd7a64117b35ea83cb0d738f654b9d0726bbd92b3c21c7d2c3` |
| **Gold Labels Manifest** | `research/gate_5_9_optimization/chunk_gold_labels.json` | `e97b102b3ef3e317c2f61fc1ef366050b1df1e8cb85b0cb9ffbe5232d36d88b4` |
| **Exact Top-5 Rankings** | `research/gate_5_9_optimization/evaluations/gate_5_9_exact_top5_rankings.json` | `9d554a938c414995f9cf62955f1712a76f2d24497ce79f22ca8ea7b36bb03649` |

---

## 4. Chunk-Level Recall@1, Recall@3, Recall@5, and MRR

Re-scoring the exact frozen Gate 5.9 rankings across the benchmark yields the following side-by-side comparison:

| Benchmark Split | Sample Size (N) | Evaluation Level | Pipeline Config | Recall@1 | Recall@3 | Recall@5 | MRR |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **DEVELOPMENT SPLIT** | 40 | Source-Level | Dense Only | 26/40 (65.00%) | 32/40 (80.00%) | 37/40 (92.50%) | 0.7425 |
| | 40 | Source-Level | Top-5 + Rerank | 29/40 (72.50%) | 35/40 (87.50%) | 37/40 (92.50%) | 0.7987 |
| | 40 | **Chunk-Level** | Dense Only | 13/40 (32.50%) | 19/40 (47.50%) | 26/40 (65.00%) | 0.4287 |
| | 40 | **Chunk-Level** | **Top-5 + Rerank** | **18/40 (45.00%)** | **25/40 (62.50%)** | **26/40 (65.00%)** | **0.5217** |
| **LOCKED HOLDOUT** | 40 | Source-Level | Dense Only | 31/40 (77.50%) | 34/40 (85.00%) | 37/40 (92.50%) | 0.8300 |
| | 40 | Source-Level | Top-5 + Rerank | 34/40 (85.00%) | 37/40 (92.50%) | 37/40 (92.50%) | 0.8875 |
| | 40 | **Chunk-Level** | Dense Only | 10/40 (25.00%) | 10/40 (25.00%) | 14/40 (35.00%) | 0.2737 |
| | 40 | **Chunk-Level** | **Top-5 + Rerank** | **9/40 (22.50%)** | **12/40 (30.00%)** | **14/40 (35.00%)** | **0.2667** |
| **OVERALL CORPUS** | 80 | Source-Level | Dense Only | 57/80 (71.25%) | 66/80 (82.50%) | 74/80 (92.50%) | 0.7863 |
| | 80 | Source-Level | Top-5 + Rerank | 63/80 (78.75%) | 72/80 (90.00%) | 74/80 (92.50%) | 0.8431 |
| | 80 | **Chunk-Level** | Dense Only | 23/80 (28.75%) | 29/80 (36.25%) | 40/80 (50.00%) | 0.3512 |
| | 80 | **Chunk-Level** | **Top-5 + Rerank** | **27/80 (33.75%)** | **37/80 (46.25%)** | **40/80 (50.00%)** | **0.3942** |

---

## 5. Development vs. Locked Holdout Comparison

- **Development Split**: Top-5 context captures the gold evidence in **65.0% (26/40)** of queries. Top-1 chunk accuracy improves from 32.5% (Dense) to 45.0% (Rerank).
- **Locked Holdout Split**: Top-5 context captures the gold evidence in only **35.0% (14/40)** of queries. Top-1 chunk accuracy is only **22.5% (9/40)**.
- **The Generalization Drop**: While source-level accuracy appeared to generalize (85.0% holdout vs 72.5% DEV), chunk-level evidence presence collapsed from 65.0% in DEV to **35.0% on the holdout**.

---

## 6. Linguistic Category Breakdown (DEV vs. Holdout)

### Development Split (N=40):
| Language Category | N | Source R@1 (Rerank) | **Chunk R@1 (Dense)** | **Chunk R@1 (Rerank)** | **Chunk R@3 (Rerank)** | **Chunk R@5 (Rerank)** | Chunk MRR (Rerank) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **English** | 12 | 12/12 (100.0%) | 7/12 (58.33%) | **8/12 (66.67%)** | 10/12 (83.33%) | **11/12 (91.67%)** | 0.7528 |
| **Native Bangla** | 10 | 8/10 (80.00%) | 2/10 (20.00%) | **4/10 (40.00%)** | 6/10 (60.00%) | **6/10 (60.00%)** | 0.4833 |
| **Standard Banglish** | 10 | 5/10 (50.00%) | 1/10 (10.00%) | **3/10 (30.00%)** | 5/10 (50.00%) | **5/10 (50.00%)** | 0.3667 |
| **Abbreviated Banglish** | 8 | 4/8 (50.00%) | 3/8 (37.50%) | **3/8 (37.50%)** | 4/8 (50.00%) | **4/8 (50.00%)** | 0.4167 |

### Locked Holdout Split (N=40):
| Language Category | N | Source R@1 (Rerank) | **Chunk R@1 (Dense)** | **Chunk R@1 (Rerank)** | **Chunk R@3 (Rerank)** | **Chunk R@5 (Rerank)** | Chunk MRR (Rerank) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **English** | 12 | 12/12 (100.0%) | 5/12 (41.67%) | **4/12 (33.33%)** | 6/12 (50.00%) | **7/12 (58.33%)** | 0.4097 |
| **Native Bangla** | 11 | 10/11 (90.91%) | 4/11 (36.36%) | **4/11 (36.36%)** | 4/11 (36.36%) | **5/11 (45.45%)** | 0.3864 |
| **Standard Banglish** | 9 | 6/9 (66.67%) | 0/9 (0.00%) | **0/9 (0.00%)** | 1/9 (11.11%) | **1/9 (11.11%)** | 0.0556 |
| **Abbreviated Banglish** | 8 | 6/8 (75.00%) | 1/8 (12.50%) | **1/8 (12.50%)** | 1/8 (12.50%) | **1/8 (12.50%)** | 0.1250 |

---

## 7. Top-1 vs. Top-5 Evidence Availability (The Core Decision Table)

| Availability Category | DEV Split (N=40) | Locked Holdout (N=40) | Overall Valid Corpus (N=80) | Percentage (Overall) |
| :--- | :---: | :---: | :---: | :---: |
| **`TOP1_CORRECT`** | 18 | 9 | **27** | **33.75%** |
| **`TOP1_WRONG_BUT_TOP3_CONTAINS_GOLD`** | 7 | 3 | **10** | **12.50%** |
| **`TOP3_WRONG_BUT_TOP5_CONTAINS_GOLD`** | 1 | 2 | **3** | **3.75%** |
| **`GOLD_ABSENT_FROM_TOP5`** | **14** | **26** | **40** | **50.00%** |

### Key Insight:
- In the **Locked Holdout**, **65.0% (26 / 40)** of queries have **NO valid evidence chunk anywhere in the Top-5 retrieved context**.
- Providing a Top-5 context to an LLM would result in the generator lacking the ground truth evidence in **65.0% of unseen queries**.

---

## 8. Reranker Effect at Chunk Level

Evaluating the cross-encoder (BGE Reranker v2 m3) strictly at the chunk level across all 80 valid queries:

- **Dense Correct \(\rightarrow\) Rerank Correct**: 22 queries (27.5%).
- **Dense Wrong \(\rightarrow\) Rerank Correct (Chunk Improvement)**: **5 queries (6.25%)**.
- **Dense Correct \(\rightarrow\) Rerank Wrong (`OBSERVED_CHUNK_RANKING_REGRESSION`)**: **1 query (1.25%)** (`TEST-DIA-05`).
- **Dense Wrong \(\rightarrow\) Rerank Wrong**: 52 queries (65.0%).
- **Source-Level Improvement but Chunk-Level Regression**: **5 queries** (The reranker elevated the correct document to Rank 1, but placed an uninformative overview chunk above the actual evidence chunk).

---

## 9. Critical Failure Cases Analysis

Across the 36 queries where the parent source was correctly retrieved but the Top-1 chunk was wrong:

1. **`GOLD_IN_TOP5` (Reranker Selection Failure — 11 cases / 30.56%)**:
   - The dense retriever included the gold chunk in the Top-5 candidate pool, but the cross-encoder reranker chose a generic overview or adjacent chunk from the same document.
   - *Example*: `DEV-BUR-05` (*"Should you put butter or oil on a burn?"*)
     - Expected: `DOC-NHS-005-HYB-001` (contraindication against butter/ice).
     - Dense Top-5 contained `DOC-NHS-005-HYB-001` at rank 3.
     - Reranker selected `DOC-NHS-005-HYB-004` (general aftercare ointment) at Rank 1.
2. **`GOLD_OUTSIDE_TOP5` (Dense Recall Failure — 25 cases / 69.44%)**:
   - The dense retriever failed to include the gold evidence chunk anywhere in its Top-5 candidate list, populating the Top-5 pool with other chunks from the same document.
   - *Example*: `TEST-DIA-03` (*"diarrhoea ar bomi hole bashay ki korbo?"*)
     - Expected: `DOC-NHS-008-HYB-000` (home hydration & rest).
     - Dense Top-5: `['DOC-NHS-010-HYB-005', 'DOC-NHS-008-HYB-003', 'DOC-NHS-004-HYB-015', 'DOC-NHS-008-HYB-004', 'DOC-NHS-007-HYB-003']`.
     - Gold chunk was completely absent from Top-5.

---

## 10. Hard Negative & Out-of-Corpus Handling

- **Hard Negatives (N=12)** & **Out-of-Corpus (N=8)** were excluded from Recall@K metrics.
- Cross-encoder scores remain the sole effective rejection barrier: 100% of out-of-corpus queries scored \(\le 0.0031\) and 100% of hard negatives scored \(\le 0.1840\), while supported valid queries scored up to \(0.9967\).

---

## 11. Methodological Limitations

1. **Dense Retriever Inherent Granularity Bias**: `multilingual-e5-small` embeddings tend to align strongly with top-level introductory headings (`Symptoms`, `About`, `Overview`) rather than specific clinical rule bullet points located in lower sections.
2. **Top-K Capacity Limit (\(K=5\))**: With \(K=5\), dense recall is bottlenecked when multiple documents compete for candidate slots, leaving no room for intra-document subsection chunks.
3. **Banglish Lexical Disconnect**: In Standard and Abbreviated Banglish, the absence of query normalization prevents the dense encoder from retrieving the specific evidence chunk in over 88% of holdout cases.

---

## 12. Corrected Retrieval Interpretation & Scenario Evaluation

Referring to the three potential project scenarios:
- **Scenario A (Top-5 is 80–90%)**: **DISPROVEN**.
- **Scenario B (Top-5 is 50–60%)**: Partially holds for DEV (65.0%), but **DISPROVEN for Holdout**.
- **Scenario C (Top-5 is ~20–35%)**: **CONFIRMED on Locked Holdout (35.0%)**.

### Final Conclusion:
In **65.0% of locked holdout queries (26 / 40)**, the required evidence chunk is **completely absent from the Top-5 retrieved context**. Therefore, feeding a Top-5 context to a downstream LLM would result in the generator lacking grounding evidence in nearly two-thirds of unseen cases.

---

## 13. Final Decision

**`EVIDENCE_MOSTLY_MISSING_FROM_TOP5`**

### Summary:
- The current retrieval architecture (`multilingual-e5-small` \(\rightarrow\) Top-5 \(\rightarrow\) `bge-reranker-v2-m3`) cannot support downstream clinical RAG generation in its current form because **65.0% of held-out queries lack the gold evidence chunk in their Top-5 context**.
- Transitioning to Gate 6 (LLM generation) is **NOT** recommended until the dense retrieval and ranking pipeline is strengthened to achieve \(\ge 80\%\) chunk-level Recall@5.

---
**ABSOLUTE STOP CONDITION REACHED**: Gate 5.9.2 is complete. No retrieval architecture was altered, no models were re-executed, no LLMs were called, and no production code was modified. Awaiting independent review.
