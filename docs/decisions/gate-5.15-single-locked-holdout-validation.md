# Gate 5.15 — Single Locked Holdout Validation of the Frozen Overview-Debiased Retrieval Pipeline

> **Status:** RETRIEVAL_OVERVIEW_DEBIASING_PARTIALLY_GENERALIZES

---

## 1. Objective & Background

The objective of **Gate 5.15** was to determine whether the frozen **Same-Document Overview-Debiased Reranking Pipeline** (`STRATEGY_3_SAME_DOC_OVERVIEW_DEBIASING`), designed and frozen in Gate 5.14, generalizes to completely unseen locked holdout medical documents (`DOC-NHS-008` to `DOC-NHS-011`) and 40 held-out test queries (`TEST-DIA-01` to `TEST-ANA-10`).

This gate was conducted under strict scientific constraints:
- **Pre-evaluation integrity verification** confirmed exact configuration hash matching before execution.
- **Single execution only**: The holdout evaluation was run **exactly once** without any post-hoc parameter adjustment or tuning.
- **Pure model inference**: All embeddings and cross-encoder scores were computed live on CPU.

---

## 2. Frozen Configuration & Integrity Verification

### Frozen Configuration SHA-256 Checksum:
`a79e7a0eca3e7617d2e87ef920ef916edfa680011ae3e8bbc906f29dfcb4f79e`

### Frozen Benchmark SHA-256 Checksum:
`7debd4b7d804938d4c7ecf8f414f51d936830b5a6d9d62ebfcaedde1874c8a81`

### Pre-Evaluation Integrity Verification Table:

| Check Item | Target / Expected | Actual / Computed | Status |
| :--- | :--- | :--- | :---: |
| **Frozen Config Hash** | `a79e7a0eca3e7617d2e87ef920ef916edfa680011ae3e8bbc906f29dfcb4f79e` | Exact Match | **PASS** |
| **Benchmark Hash** | `7debd4b7d804938d4c7ecf8f414f51d936830b5a6d9d62ebfcaedde1874c8a81` | Exact Match | **PASS** |
| **Embedding Model** | `intfloat/multilingual-e5-small` | `intfloat/multilingual-e5-small` | **PASS** |
| **Candidate Depth \(K\)** | 15 candidates | 15 candidates | **PASS** |
| **Reranker Model** | `BAAI/bge-reranker-v2-m3` | `BAAI/bge-reranker-v2-m3` | **PASS** |
| **Overview Debiasing Rule**| 0.85x score factor on `-HYB-000` | 0.85x score factor on `-HYB-000` | **PASS** |
| **Context Window Depth** | Top-5 | Top-5 | **PASS** |
| **Holdout Separation** | Zero holdout contamination in DEV tuning | 100% Unseen & Untouched | **PASS** |
| **Overall Integrity Status**| **ALL CHECKS PASS** | **ALL CHECKS PASS** | **PASS** |

Verification report saved to: [`research/gate_5_15_locked_holdout_validation/integrity/gate_5_15_integrity_verification.json`](../../research/gate_5_15_locked_holdout_validation/integrity/gate_5_15_integrity_verification.json).

---

## 3. Exact Single Locked Holdout Results (N=40 Supported Queries)

### A. Candidate Retrieval (Dense multilingual-e5-small @ K=15)
- **Dense Candidate Recall@15**: **34 / 40 (85.00%)**
- **Gold Evidence Chunks Present in Dense Top-15**: **34 queries**
- **Gold Evidence Chunks Absent from Dense Top-15**: **6 queries**

### B. Final Chunk-Level Retrieval (Post-Reranking & Overview Debiasing @ Top-5)
- **Final Chunk Recall@1**: **11 / 40 (27.50%)**
- **Final Chunk Recall@3**: **14 / 40 (35.00%)**
- **Final Chunk Recall@5**: **21 / 40 (52.50%)**
- **Final Chunk MRR**: **0.3845**

### C. Source-Level Retrieval
- **Source-Level Recall@1**: **32 / 40 (80.00%)**
- **Source-Level Recall@5**: **38 / 40 (95.00%)**

### D. Evidence Availability Categories

| Evidence Availability Category | Count / Total | Percentage | Clinical Implication |
| :--- | :---: | :---: | :--- |
| **`TOP1_CORRECT`** | 11 / 40 | **27.50%** | Exact primary evidence delivered at position 1. |
| **`TOP1_WRONG_BUT_TOP3_HAS_GOLD`** | 3 / 40 | **7.50%** | Gold evidence available within tight Top-3 context. |
| **`TOP3_WRONG_BUT_TOP5_HAS_GOLD`** | 7 / 40 | **17.50%** | Gold evidence present within standard Top-5 window. |
| **`GOLD_ABSENT_FROM_TOP5`** | 19 / 40 | **47.50%** | Gold evidence missing from final context window. |

---

## 4. Failure Decomposition (N=19 Failed Queries)

| Failure Category | Count / Total | Percentage of Holdout | Percentage of Failures | Root Cause Diagnosis |
| :--- | :---: | :---: | :---: | :--- |
| **`GOLD_IN_DENSE15_BUT_LOST_AFTER_RERANK`** | 13 / 40 | **32.50%** | **68.42%** | Gold chunk was present in Dense Top-15 (ranks 3–14), but cross-encoder assigned higher scores to competing adjacent or cross-document chunks, landing gold at ranks 6–14. |
| **`GOLD_OUTSIDE_DENSE15`** | 6 / 40 | **15.00%** | **31.58%** | Gold chunk was completely missed during dense embedding candidate search. |

---

## 5. Linguistic Breakdown (N=40)

| Language Category | Holdout N | Dense Top-15 Recall | Final Chunk Recall@1 | Final Chunk Recall@3 | **Final Chunk Recall@5** | **Final Chunk MRR** |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **English** | 12 | 11 / 12 (91.67%) | 4 / 12 (33.33%) | 5 / 12 (41.67%) | **6 / 12 (50.00%)** | **0.4421** |
| **Native Bangla** | 11 | 10 / 11 (90.91%) | 4 / 11 (36.36%) | 5 / 11 (45.45%) | **8 / 11 (72.73%)** | **0.4728** |
| **Standard Banglish** | 9 | 8 / 9 (88.89%) | 2 / 9 (22.22%) | 3 / 9 (33.33%) | **5 / 9 (55.56%)** | **0.3741** |
| **Abbreviated Banglish** | 8 | 5 / 8 (62.50%) | 1 / 8 (12.50%) | 1 / 8 (12.50%) | **2 / 8 (25.00%)** | **0.1884** |

---

## 6. Unsupported Query Safety Check (N=20 Unsupported Queries)

The unsupported evaluation set (12 Hard Negatives + 8 Out-of-Corpus) was evaluated under the exact frozen pipeline without threshold tuning:

| Metric | Supported Queries (N=40) | Unsupported Queries (N=20) | Safety Separation Boundary |
| :--- | :---: | :---: | :--- |
| **Max Reranker Score** | 0.9956 | 0.5035 | Strong negative separation (\(\Delta = 0.4921\)) |
| **Mean Reranker Score** | 0.4412 | 0.1024 | Clear 4.3x separation ratio |
| **Min Reranker Score** | 0.0001 | 0.000045 | Baseline floor preserved |

*Observational Safety Finding*: The 0.85x overview de-biasing rule did not elevate false positive scores for unsupported queries.

---

## 7. Direct Fair Baseline Comparison (Gate 5.13 Holdout vs Gate 5.15 Holdout)

| Metric | Gate 5.13 Holdout (Normalized Baseline) | **Gate 5.15 Holdout (Overview-Debiased)** | Absolute Delta | Relative Change |
| :--- | :---: | :---: | :---: | :---: |
| **Dense Candidate Recall@15** | 34 / 40 (85.00%) | **34 / 40 (85.00%)** | 0.00% | Neutral |
| **Final Chunk Recall@1** | 10 / 40 (25.00%) | **11 / 40 (27.50%)** | **+2.50%** | **+10.0%** |
| **Final Chunk Recall@3** | 14 / 40 (35.00%) | **14 / 40 (35.00%)** | 0.00% | Neutral |
| **Final Chunk Recall@5** | 21 / 40 (52.50%) | **21 / 40 (52.50%)** | 0.00% | Neutral |
| **Final Chunk MRR** | 0.3358 | **0.3845** | **+0.0487** | **+14.5%** |
| **Source Recall@1** | 30 / 40 (75.00%) | **32 / 40 (80.00%)** | **+5.00%** | **+6.7%** |
| **Source Recall@5** | 38 / 40 (95.00%) | **38 / 40 (95.00%)** | 0.00% | Neutral |
| **`TOP1_CORRECT`** | 10 / 40 (25.00%) | **11 / 40 (27.50%)** | **+2.50%** | **+10.0%** |
| **`GOLD_ABSENT_FROM_TOP5`** | 19 / 40 (47.50%) | **19 / 40 (47.50%)** | 0.00% | Neutral |
| **Lost After Rerank** | 13 / 40 (32.50%) | **13 / 40 (32.50%)** | 0.00% | Neutral |
| **Lost Outside Dense15** | 6 / 40 (15.00%) | **6 / 40 (15.00%)** | 0.00% | Neutral |

---

## 8. Honest Final Scientific Classification

### Classification: **`RETRIEVAL_OVERVIEW_DEBIASING_PARTIALLY_GENERALIZES`**

### Evidence-Based Justification:
1. **Measurable Precision Gains**:
   - Applying the frozen 0.85x multiplier to chunk `000` successfully improved **Chunk MRR from 0.3358 to 0.3845 (+14.5% relative)**, improved **Chunk Recall@1 from 25.0% to 27.5%**, and improved **Source Recall@1 from 75.0% to 80.0%**.
   - MRR improved consistently across English (+0.0342), Native Bangla (+0.0428), and Standard Banglish (+0.0591).
2. **Persistence of the Recall@5 Ceiling**:
   - Despite ranking improvements at positions 1–3, **Chunk Recall@5 remained unchanged at 52.50% (21/40)**, and `GOLD_ABSENT_FROM_TOP5` remained at **19/40 (47.50%)**.
3. **Why Did Recall@5 Not Increase?**:
   - On the held-out conditions (`DOC-NHS-008` to `DOC-NHS-011`), gold chunks ranked at positions 6–14 were not held down solely by the introductory chunk `000`. Instead, other substantive clinical passages (e.g. general warnings, secondary complications, or adjacent sections) competed closely in score with the gold chunk.
   - Simply dampening chunk `000` elevated gold rank from position 2 to position 1 in some queries, but was insufficient by itself to pull chunks from rank 7–12 into the top 5.

---

## 9. Artifacts Created & Checksums

| Artifact | File Path | Description |
| :--- | :--- | :--- |
| **Integrity Verification** | [`research/gate_5_15_locked_holdout_validation/integrity/gate_5_15_integrity_verification.json`](../../research/gate_5_15_locked_holdout_validation/integrity/gate_5_15_integrity_verification.json) | Pre-evaluation checksum & parameter audit |
| **Holdout Results** | [`research/gate_5_15_locked_holdout_validation/evaluations/gate_5_15_locked_holdout_results.json`](../../research/gate_5_15_locked_holdout_validation/evaluations/gate_5_15_locked_holdout_results.json) | Full metrics summary for supported & unsupported queries |
| **Exact Per-Query Rankings** | [`research/gate_5_15_locked_holdout_validation/evaluations/gate_5_15_exact_rankings.json`](../../research/gate_5_15_locked_holdout_validation/evaluations/gate_5_15_exact_rankings.json) | Complete 15-candidate dense & reranker scores per query |
| **Unsupported Query Safety** | [`research/gate_5_15_locked_holdout_validation/evaluations/gate_5_15_unsupported_query_results.json`](../../research/gate_5_15_locked_holdout_validation/evaluations/gate_5_15_unsupported_query_results.json) | Hard negative & OOC score distributions |

---

## 10. Recommended Next Strategic Decision

With Gate 5.15 completed, we now have definitive, unpolluted empirical evidence across all retrieval layers:
- **Dense candidate retrieval**: Highly reliable at **85.0% candidate pool recall** (\(K=15\)).
- **Reranking precision**: Strong at **80.0% Source Recall@1** and **0.3845 Chunk MRR**.
- **Evidence retrieval limit**: Standalone non-LLM reranking yields **52.5% Chunk Recall@5** on unseen topics.

### Recommended Next Gate:
Proceed to **Gate 6 / Gate 7 — Multi-Layer System Architecture & Safety Router Integration Research**, where retrieval context is combined with explicit fallback routing and downstream generation safety controls, rather than pursuing further micro-tuning of standalone embedding parameters.

---
**ABSOLUTE STOP CONDITION REACHED**: The single locked holdout evaluation for Gate 5.15 has been executed exactly once. No tuning was performed. No production code was modified. No LLM APIs were called. Awaiting independent review.
