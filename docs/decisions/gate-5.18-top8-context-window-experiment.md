# Gate 5.18 — Development-Only Top-8 Context Window Experiment

> **Final Status:** `TOP8_CONTEXT_REJECTED`

---

## 1. Executive Summary & Experimental Objective

Following the rejection of heading-aware reranking in **Gate 5.17**, the remaining structural hypothesis formulated in Gate 5.16 was:

> *"Some correct evidence chunks may be ranked 6–8 rather than <=5. Increasing the delivered context window from Top-5 to Top-8 may therefore improve evidence availability without changing retrieval or reranker scoring."*

The objective of **Gate 5.18** was to execute a **strictly isolated, development-only context window expansion experiment** on the 40 Development queries (`DOC-NHS-004` to `DOC-NHS-007`) comparing delivered **Top-5 context** against delivered **Top-8 context**.

The locked holdout (`DOC-NHS-008` to `DOC-NHS-011` and 40 `TEST-*` queries) remained **100% UNTOUCHED AND UNSEEN**.

---

## 2. Phase 1 — Baseline Reproduction

The Gate 5.16 / Gate 5.17 frozen pipeline baseline was reproduced with exact numerical match on DEV:

| Metric | Target Frozen Baseline | Reproduced Actual | Status |
| :--- | :---: | :---: | :---: |
| **Dense Candidate Pool Recall@15** | 37 / 40 (92.50%) | **37 / 40 (92.50%)** | **PASS** |
| **Final Chunk Recall@1** | 19 / 40 (47.50%) | **19 / 40 (47.50%)** | **PASS** |
| **Final Chunk Recall@3** | 27 / 40 (67.50%) | **27 / 40 (67.50%)** | **PASS** |
| **Final Chunk Recall@5** | 35 / 40 (87.50%) | **35 / 40 (87.50%)** | **PASS** |
| **Final Chunk MRR** | 0.6150 | **0.6150** | **PASS** |

*Verification Artifact*: [`research/gate_5_18_top8_context_experiment/baseline/dev_baseline_top5_results.json`](../../research/gate_5_18_top8_context_experiment/baseline/dev_baseline_top5_results.json)

---

## 3. Phase 2 — Pre-Computed Top-8 Feasibility Analysis (DEV N=40)

An audit of the rank distribution across all 40 DEV queries established the theoretical upper bound of expanding the context window from Top-5 to Top-8:

| Rank Category | Definition | Query Count | Percentage |
| :--- | :--- | :---: | :---: |
| **`GOLD_IN_TOP1`** | Gold evidence at Rank 1 | 19 / 40 | 47.50% |
| **`GOLD_IN_TOP3`** | Gold evidence at Rank 1–3 | 27 / 40 | 67.50% |
| **`GOLD_IN_TOP5`** | Gold evidence at Rank 1–5 | 35 / 40 | 87.50% |
| **`GOLD_IN_TOP8`** | Gold evidence at Rank 1–8 | 35 / 40 | 87.50% |
| **Rank 6–8 Increment** | **Gold evidence at Rank 6, 7, or 8** | **0 / 40** | **0.00%** |
| **`GOLD_IN_TOP15`** | Gold evidence at Rank 1–15 | 37 / 40 | 92.50% |
| **Rank 9–15 Count** | Gold evidence at Rank 9–15 | 2 / 40 | 5.00% |
| **`GOLD_OUTSIDE_DENSE15`** | Gold evidence absent from Dense Top-15 | 3 / 40 | 7.50% |

### Key Feasibility Finding:
On the Development dataset, **exactly ZERO queries (0/40) have gold evidence located at Rank 6, 7, or 8**.
All 35 queries with gold in Top-8 already had gold in Top-5.

---

## 4. Phase 3 & 4 — Controlled Top-8 Delivery Evaluation & Primary Metrics

| Metric | Top-5 Baseline Context | Top-8 Experimental Context | Absolute Delta | Relative Gain |
| :--- | :---: | :---: | :---: | :---: |
| **Final Chunk Recall@1** | 19 / 40 (47.50%) | 19 / 40 (47.50%) | +0.00% | Unchanged |
| **Final Chunk Recall@3** | 27 / 40 (67.50%) | 27 / 40 (67.50%) | +0.00% | Unchanged |
| **Final Chunk Recall@5** | 35 / 40 (87.50%) | 35 / 40 (87.50%) | +0.00% | Unchanged |
| **Final Chunk Recall@8 (PRIMARY)** | **35 / 40 (87.50%)** | **35 / 40 (87.50%)** | **+0.00%** | **0 / 40 queries rescued** |
| **Final Chunk MRR** | 0.6150 | 0.6150 | +0.0000 | Unchanged |

---

## 5. Phase 5 — Language Breakdown (DEV N=40)

| Language Category | DEV N | Chunk Recall@1 | Chunk Recall@3 | Chunk Recall@5 | Chunk Recall@8 | Chunk MRR | Evidence Gain |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **English** | 12 | 8 / 12 (66.67%) | 10 / 12 (83.33%) | 11 / 12 (91.67%) | **11 / 12 (91.67%)** | 0.7611 | **+0.0%** |
| **Native Bangla** | 10 | 5 / 10 (50.00%) | 6 / 10 (60.00%) | 9 / 10 (90.00%) | **9 / 10 (90.00%)** | 0.6150 | **+0.0%** |
| **Standard Banglish** | 10 | 3 / 10 (30.00%) | 6 / 10 (60.00%) | 8 / 10 (80.00%) | **8 / 10 (80.00%)** | 0.4867 | **+0.0%** |
| **Abbreviated Banglish** | 8 | 3 / 8 (37.50%) | 5 / 8 (62.50%) | 7 / 8 (87.50%) | **7 / 8 (87.50%)** | 0.5563 | **+0.0%** |

---

## 6. Phase 6 — Context Cost & Downstream Tradeoff Analysis

| Context Parameter | Top-5 Baseline Context | Top-8 Experimental Context | Expansion Overhead |
| :--- | :---: | :---: | :---: |
| **Delivered Chunks per Query** | 5.0 chunks | 8.0 chunks | **+60.0% (+3 chunks)** |
| **Average Context Characters** | 2,971.9 chars | 4,745.7 chars | **+59.7% (+1,773.8 chars)** |
| **Average Estimated Tokens** | 781.7 tokens | 1,248.3 tokens | **+59.7% (+466.7 tokens)** |
| **Reranking Latency** | 514.03s | 514.03s | **0.00% (Unchanged)** |
| **Downstream LLM Impact** | Baseline prompt size | +60% token bloat | **High cost/latency penalty for 0% gain** |

*Note on Latency*: Reranker inference latency is unchanged because `bge-reranker-v2-m3` already scores all \(K=15\) candidates before truncation. However, delivering 8 chunks instead of 5 increases the downstream LLM generation context window by ~60% (+467 tokens per user turn).

---

## 7. Phase 7 — Remaining Failure Classification on Top-8 (5 / 40 Queries)

All 5 failures on DEV remain completely unaddressed by Top-8 context delivery:

| Query ID | Language | Raw Query Text | Gold Chunk ID | Rerank Rank | Failure Classification |
| :--- | :--- | :--- | :--- | :---: | :--- |
| **`DEV-BUR-02`** | Native Bangla | হাত পুড়ে গেলে কতক্ষণ ঠাণ্ডা পানির নিচে রাখতে হবে? | `DOC-NHS-005-HYB-000` | 0 | `GOLD_OUTSIDE_DENSE15` |
| **`DEV-BUR-03`** | Standard Banglish | pure gele thanda pani koto minute dhalbo? | `DOC-NHS-005-HYB-000` | 0 | `GOLD_OUTSIDE_DENSE15` |
| **`DEV-CUT-04`** | Abbreviated Banglish | angul kete rokt porche chap diye dhorbo kina | `DOC-NHS-006-HYB-000`, `001` | 0 | `GOLD_OUTSIDE_DENSE15` |
| **`DEV-CUT-08`** | English | When to go to A&E for a cut with non-stop bleeding? | `DOC-NHS-006-HYB-002` | 10 | `GOLD_RANK_9_TO_15` |
| **`DEV-BUR-07`** | Standard Banglish | pora jaygay butter ba tel lagano thik naki? | `DOC-NHS-005-HYB-001` | 12 | `GOLD_RANK_9_TO_15` |

### Failure Breakdown:
- **`GOLD_OUTSIDE_DENSE15`**: **3 / 5 (60.0%)** — The gold chunk never entered the Top-15 candidate pool due to dense transliteration gaps.
- **`GOLD_RANK_9_TO_15`**: **2 / 5 (40.0%)** — The gold chunk entered Dense Top-15 but was ranked at positions 10 and 12, well beyond Rank 8.
- **`RERANKED_INTO_TOP6_TO_8`**: **0 / 5 (0.0%)**.

---

## 8. Interpretation & Scientific Conclusion

### [VERIFIED FACT]
1. Increasing the delivered context window from Top-5 to Top-8 yields **exactly 0.00% gain in evidence availability on DEV** (**35 / 40 = 87.50% Chunk Recall@8 vs 87.50% Chunk Recall@5**).
2. The remaining DEV failure cases are split between **dense candidate pool misses (3 queries)** and **rerankings at ranks 10–12 (2 queries)**.
3. Top-8 context expansion introduces an unacceptable **+59.7% token overhead (+467 tokens/query)** with zero evidence benefit.

---

## 9. Final Decision & Status

### Final Status: **`TOP8_CONTEXT_REJECTED`**

The hypothesis that expanding the context delivery window from Top-5 to Top-8 improves evidence availability is **empirically disproven on DEV and rejected**.

The active development retrieval configuration remains:
- **Chunking**: `HYBRID_600`
- **Dense Model**: `intfloat/multilingual-e5-small` (Top-15)
- **Reranker**: `BAAI/bge-reranker-v2-m3` on raw chunk text (`{chunk_text}`)
- **Debiasing Rule**: 0.85x on `-HYB-000` overview chunks
- **Delivered Context Window**: **Top-5**

---
**ABSOLUTE STOP CONDITION REACHED**: Gate 5.18 is complete. No holdout evaluations were conducted, no production code was modified, and no LLMs were invoked. Awaiting independent review.
