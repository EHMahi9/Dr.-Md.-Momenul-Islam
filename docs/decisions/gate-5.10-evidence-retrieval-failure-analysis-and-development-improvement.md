# Gate 5.10 — Evidence Retrieval Failure Analysis & Development-Only Improvement Design

> **Status:** EVIDENCE_RETRIEVAL_IMPROVEMENT_CANDIDATE_SELECTED

---

## 1. Executive Summary & Objective

In Gate 5.9.2, an independent audit revealed that the frozen `HYBRID_600` pipeline suffered from severe evidence starvation: on the locked holdout, **65.0% (26/40) of queries had the ground-truth clinical evidence chunk completely absent from the Top-5 retrieved context**.

The objective of Gate 5.10 was an isolated root-cause investigation and development-only improvement search conducted **exclusively on the 40 development queries and documents (`DOC-NHS-004` to `DOC-NHS-007`)**.

The locked holdout (`DOC-NHS-008` to `DOC-NHS-011` and test queries `TEST-*`) remained **100% untouched and uninspected** throughout this gate.

---

## 2. Absolute Experimental Boundaries Verification

- **Development Split Used**: `DOC-NHS-004` (Asthma), `DOC-NHS-005` (Burns), `DOC-NHS-006` (Cuts), `DOC-NHS-007` (Dehydration) + 40 DEV queries.
- **Locked Holdout Status**: **UNTOUCHED, UNSEEN, AND UNTUNED**. No test queries were evaluated, no holdout errors were inspected, and no parameters were fitted to holdout data.
- **Production Status**: 0 modifications to production codebase.
- **LLM Status**: 0 LLM calls made.

---

## 3. Phase 1 — Baseline Reproduction

The frozen Gate 5.9 baseline (`multilingual-e5-small` \(\rightarrow\) Dense Top-5 \(\rightarrow\) `bge-reranker-v2-m3` Top-5) was reproduced on the 40 DEV queries:

- **Baseline Mismatches**: **0 / 40 (100% deterministic reproduction)**.
- **Dense Chunk Recall**: Recall@1 = 32.50%, Recall@3 = 47.50%, Recall@5 = 65.00%, MRR = 0.4287.
- **Reranked Chunk Recall**: Recall@1 = 45.00%, Recall@3 = 62.50%, Recall@5 = 65.00%, MRR = 0.5217.
- **Reproduced Baseline Artifact**: [`research/gate_5_10_evidence_retrieval_improvement/baseline/dev_baseline_reproduced.json`](../../research/gate_5_10_evidence_retrieval_improvement/baseline/dev_baseline_reproduced.json).

---

## 4. Phase 2 — DEV Failure Taxonomy

Categorizing all 40 DEV queries against the baseline retrieval pipeline:

| Category | Description | Count | Percentage |
| :--- | :--- | :---: | :---: |
| **`GOLD_TOP1`** | Gold evidence chunk ranked at Rank 1 after reranking | 18 | 45.00% |
| **`GOLD_TOPK_NOT_TOP1`** | Gold chunk present in Top-5 dense candidate pool, but ranked at Ranks 2–5 | 8 | 20.00% |
| **`GOLD_NOT_IN_DENSE_TOP5`** | Dense retriever completely failed to include gold chunk in Top-5 | 14 | 35.00% |
| **`GOLD_PRESENT_BUT_RERANK_DEMOTED`** | Dense retriever had gold at Rank 1, but reranker demoted it | 0 | 0.00% |

### Diagnostic Candidate Depth Analysis:
Evaluating how deeply the dense retriever ranks the gold chunk across expanded candidate depths on DEV:
- **Dense Top-5 Recall**: 26 / 40 (65.00%)
- **Dense Top-10 Recall**: 27 / 40 (67.50%)
- **Dense Top-15 Recall**: **33 / 40 (82.50%)** \(\leftarrow\) **+17.50% jump in candidate recall**
- **Dense Top-20 Recall**: **34 / 40 (85.00%)** \(\leftarrow\) **+20.00% jump in candidate recall**

---

## 5. Phase 3 — Root Cause Diagnostics

Diagnostic inspection of the 14 `GOLD_NOT_IN_DENSE_TOP5` failure cases revealed three primary failure drivers:

1. **Rigid Candidate Window Bottleneck (\(K=5\))**:
   - In 7 out of the 14 failures (50%), the gold evidence chunk was ranked by `multilingual-e5-small` at positions 6 through 15. The rigid \(K=5\) truncation dropped these evidence chunks before the cross-encoder reranker ever had an opportunity to evaluate them.
2. **Top-Level Heading Alignment Bias**:
   - The dense embedding model disproportionately favors generic introductory sections (e.g., `About Asthma`, `Overview of Burns`) over specific clinical sub-rules (e.g., `Do not apply butter or ice`), pushing specific sub-rule chunks down into ranks 6–15.
3. **Banglish Lexical Disconnect**:
   - Queries with phonetic Banglish phrases (e.g. `patla paykhana`, `buk chap lage`) have lower cosine similarity against English clinical terms, requiring wider candidate windows or hybrid lexical matching to enter the candidate pool.

---

## 6. Phase 4 & 5 — Strategy Evaluation & Comparison

We evaluated 7 comparative strategies on the DEV split across candidate pool generation and cross-encoder reranking:

### Pre-Defined Selection Rule:
1. **Primary Metric**: Chunk-level Recall@5
2. **Secondary Metric**: Chunk-level Recall@3
3. **Tertiary Metric**: Chunk-level MRR
4. **Quaternary Metric**: Chunk-level Recall@1
5. **Tie-Breaker**: Engineering complexity and latency

### Comprehensive DEV Strategy Comparison Table:
| Strategy Name | Passage Mode | Candidate Depth \(K\) | Candidate R@5 | Post-Rerank R@1 | Post-Rerank R@3 | **Post-Rerank R@5** | **Post-Rerank MRR** | Failure Movement (Net) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`BASELINE_STANDARD_K5`** | Standard | 5 | 26/40 (65.0%) | 18/40 (45.0%) | 25/40 (62.5%) | **26/40 (65.0%)** | 0.5217 | Baseline (\(\pm 0\)) |
| **`STRATEGY_EXPANDED_DEPTH_K10`** | Standard | 10 | 26/40 (65.0%) | 19/40 (47.5%) | 24/40 (60.0%) | **26/40 (65.0%)** | 0.5398 | +1 (1 F\(\rightarrow\)S) |
| **`STRATEGY_CONTEXTUAL_K10`** | Contextual | 10 | 27/40 (67.5%) | 19/40 (47.5%) | 24/40 (60.0%) | **27/40 (67.5%)** | 0.5512 | +1 (1 F\(\rightarrow\)S) |
| **`STRATEGY_HYBRID_BM25_K10`** | Hybrid RRF | 10 | 23/40 (57.5%) | 18/40 (45.0%) | 25/40 (62.5%) | **27/40 (67.5%)** | 0.5452 | 0 (1 F\(\rightarrow\)S, 1 S\(\rightarrow\)F) |
| **`STRATEGY_SYNERGISTIC_COMBO_K10`** | Context+BM25 | 10 | 24/40 (60.0%) | 18/40 (45.0%) | 26/40 (65.0%) | **27/40 (67.5%)** | 0.5528 | 0 (1 F\(\rightarrow\)S, 1 S\(\rightarrow\)F) |
| **`STRATEGY_SYNERGISTIC_COMBO_K15`** | Context+BM25 | 15 | 24/40 (60.0%) | 17/40 (42.5%) | 24/40 (60.0%) | **27/40 (67.5%)** | 0.5427 | -1 (1 S\(\rightarrow\)F) |
| **`STRATEGY_EXPANDED_DEPTH_K15`** 🏆 | Standard | 15 | 26/40 (65.0%) | 18/40 (45.0%) | 24/40 (60.0%) | **30/40 (75.0%)** | **0.5524** | 0 (1 F\(\rightarrow\)S, 1 S\(\rightarrow\)F) |

---

## 7. Linguistic Breakdown for Selected Strategy (`STRATEGY_EXPANDED_DEPTH_K15`)

| Language Category | DEV N | Baseline R@1 | **Selected R@1** | Baseline R@5 | **Selected R@5** | Baseline MRR | **Selected MRR** |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **English** | 12 | 8/12 (66.67%) | **8/12 (66.67%)** | 11/12 (91.67%) | **11/12 (91.67%)** | 0.7528 | **0.7620** |
| **Native Bangla** | 10 | 4/10 (40.00%) | **5/10 (50.00%)** | 6/10 (60.00%) | **9/10 (90.00%)** | 0.4833 | **0.6150** |
| **Standard Banglish** | 10 | 3/10 (30.00%) | **2/10 (20.00%)** | 5/10 (50.00%) | **6/10 (60.00%)** | 0.3667 | **0.3467** |
| **Abbreviated Banglish** | 8 | 3/8 (37.50%) | **3/8 (37.50%)** | 4/8 (50.00%) | **4/8 (50.00%)** | 0.4167 | **0.4167** |

### Key Improvements in Selected Configuration:
- **Chunk Recall@5** on DEV increased from **65.0% (26/40) to 75.0% (30/40)** (+10.0%).
- **Native Bangla Chunk Recall@5** increased dramatically from **60.0% (6/10) to 90.0% (9/10)** (+30.0%).
- **Chunk MRR** improved from **0.5217 to 0.5524**.
- Zero modification of chunk text or passage schemas required, maintaining maximum simplicity and zero pipeline bloat.

---

## 8. Frozen Candidate Configuration

The winning configuration has been formally frozen in [`frozen_candidate_configuration.json`](../../research/gate_5_10_evidence_retrieval_improvement/frozen_candidate/frozen_candidate_configuration.json):

```json
{
  "candidate_strategy_name": "STRATEGY_EXPANDED_DEPTH_K15",
  "selection_rule_applied": "1. Chunk R@5 > 2. Chunk R@3 > 3. Chunk MRR > 4. Chunk R@1 > 5. Complexity",
  "parameters": {
    "embedding_model": "intfloat/multilingual-e5-small",
    "reranker_model": "BAAI/bge-reranker-v2-m3",
    "chunking_algorithm": "HYBRID_600",
    "passage_representation": "standard",
    "use_bm25_rrf": false,
    "candidate_depth_k": 15,
    "similarity_metric": "cosine_dot_product_normalized",
    "reranker_scoring_input": "raw_clean_chunk_text"
  },
  "dev_benchmark_metrics": {
    "n_queries": 40,
    "chunk_recall_at_1": "18/40 (45.00%)",
    "chunk_recall_at_3": "24/40 (60.00%)",
    "chunk_recall_at_5": "30/40 (75.00%)",
    "chunk_mrr": 0.5524
  },
  "locked_holdout_status": "UNTOUCHED_AND_UNSEEN",
  "configuration_hash": "a58194bf0fd52871a3bdd10945609c4132c09a88fb8f6a0771ac294b30edaa1f"
}
```

---

## 9. Final Decision

**`EVIDENCE_RETRIEVAL_IMPROVEMENT_CANDIDATE_SELECTED`**

---

## 10. Next Step Recommendation

Now that a strictly development-evaluated candidate has been selected, justified, and frozen, the project should proceed to:

> **Gate 5.11 — Single Locked Holdout Re-Evaluation of the Frozen Evidence Retrieval Configuration**

Under Gate 5.11, the frozen configuration (`multilingual-e5-small` \(\rightarrow\) Dense Depth \(K=15\) \(\rightarrow\) `bge-reranker-v2-m3` Top-5) will be evaluated **exactly once** on the untouched 40 locked holdout queries without further tuning.

---
**ABSOLUTE STOP CONDITION REACHED**: Gate 5.10 is fully completed. The locked holdout remains untouched. No LLMs were called, and no production code was modified. Awaiting review.
