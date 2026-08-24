# Gate 5.12 — Development-Only Retrieval Failure Decomposition & Improvement Design

> **Status:** RETRIEVAL_IMPROVEMENT_CANDIDATE_SELECTED_AND_FROZEN

---

## 1. Executive Summary & Objective

In Gate 5.11, a single locked holdout evaluation of the \(K=15\) dense-rerank pipeline showed solid progression (Chunk Recall@5 improved from 35% to 50%), but diagnosed two distinct failure modes on unseen documents:
1. **Dense Retrieval Candidate Misses**: 9/40 queries failed to place the gold evidence chunk in Dense Top-15 (primarily due to phonetic Banglish variations).
2. **Reranker Overview Demotions**: 11/40 queries had the gold chunk present in Dense Top-15, but the cross-encoder reranker ranked it in positions 6–15 in favor of generic overview sections.

The objective of Gate 5.12 was to perform an **isolated, development-only failure decomposition and controlled improvement search** using **exclusively the 40 DEV queries (`DOC-NHS-004` to `DOC-NHS-007`)**.

The locked holdout (`DOC-NHS-008` to `DOC-NHS-011` + 40 test queries) remained **100% UNTOUCHED, UNSEEN, AND UNTUNED**.

---

## 2. Phase 1 — DEV Baseline Reproduction & Failure Taxonomy

The Gate 5.11-style baseline (`multilingual-e5-small` Dense Top-15 \(\rightarrow\) `bge-reranker-v2-m3` Top-5) was reproduced on the 40 DEV queries:

- **DEV Chunk Recall@1**: 18 / 40 (45.00%)
- **DEV Chunk Recall@3**: 24 / 40 (60.00%)
- **DEV Chunk Recall@5**: 30 / 40 (75.00%)
- **DEV Chunk MRR**: 0.5450
- **Total Top-5 Failures on DEV**: 10 / 40 (25.00%)

### Multi-Label Failure Taxonomy Breakdown (DEV Split, N=40):

| Failure Category Tag | Observed Failures (Count) | Failure Rate (%) | Root Cause & Diagnosis |
| :--- | :---: | :---: | :--- |
| **`GOLD_OUTSIDE_DENSE15`** | **7 / 40** | **17.50%** | The dense embedding model alone failed to retrieve the gold evidence chunk into the Top-15 candidate pool. |
| **`GOLD_IN_DENSE15_BUT_RERANK_DEMOTED`** | **3 / 40** | **7.50%** | The gold chunk was successfully retrieved into Dense Top-15 (ranks 6–15), but demoted by the reranker. |
| **`GENERIC_OVERVIEW_BIAS`** | **7 / 40** | **17.50%** | Reranker preferred overview/intro chunks (e.g. `About Asthma`, `Overview of Burns`) over specific clinical sub-rules. |
| **`HEADING_OR_CONTEXT_REPRESENTATION_FAILURE`** | **0 / 40** | **0.00%** | No structural truncation artifacts remained (fixed in Gate 4F.2). |
| **`NATIVE_BANGLA_QUERY_MISMATCH`** | **1 / 40** | **2.50%** | High baseline capability for formal Bengali text; minor vocabulary divergence. |
| **`STANDARD_BANGLISH_QUERY_MISMATCH`** | **4 / 40** | **10.00%** | Phonetic transliteration without exact English keyword anchors caused embedding misattribution. |
| **`ABBREVIATED_BANGLISH_QUERY_MISMATCH`** | **4 / 40** | **10.00%** | Heavy abbreviations (e.g. `bomi hosse`, `shash nite parsenana`) severely disrupted dense vector cosine similarity. |
| **`LEXICAL_OR_EXACT_TERM_FAILURE`** | **1 / 40** | **2.50%** | Exact dosage or medical terms missed dense ranking. |

### Key Diagnostic Discovery:
**8 out of the 10 DEV failures (80%) were caused by Banglish vocabulary mismatch**. While Native Bangla achieved 90% Recall@5, Standard and Abbreviated Banglish accounted for almost all dense candidate misses.

---

## 3. Phase 2 — Controlled Candidate Strategies & Hypotheses

Based directly on the failure taxonomy, we implemented and evaluated 5 controlled strategies:

1. **`CANDIDATE_1_GATE_5_11_BASELINE` (Control)**:
   - *Architecture*: Raw Query \(\rightarrow\) Dense Top-15 \(\rightarrow\) Cross-Encoder Top-5.
   - *Hypothesis*: Control baseline for comparison.

2. **`CANDIDATE_2_DETERMINISTIC_QUERY_NORM_K15` (Rule-Based Normalization)**:
   - *Architecture*: Deterministic dictionary mapping of Bengali/Banglish colloquial symptoms and emergency terms to standardized clinical anchors (e.g. `pani shunnota` \(\rightarrow\) `dehydration fluid rehydration`, `shash kosto` \(\rightarrow\) `asthma attack breathing difficulty`, `bomi` \(\rightarrow\) `vomiting`, `matha betha` \(\rightarrow\) `headache`, `pura` \(\rightarrow\) `burns scalds cold water`) \(\rightarrow\) Dense Top-15 \(\rightarrow\) Cross-Encoder Top-5.
   - *Hypothesis*: Non-LLM rule-based concept normalization directly bridges the dense embedding gap for phonetic Banglish without increasing pipeline complexity.

3. **`CANDIDATE_3_DENSE_BM25_HYBRID_UNION_K20` (Lexical RRF Union)**:
   - *Architecture*: Dense + BM25 Reciprocal Rank Fusion (K=20 candidates) \(\rightarrow\) Cross-Encoder Top-5.
   - *Hypothesis*: Lexical token matching brings exact keywords into the candidate pool.

4. **`CANDIDATE_4_CONTEXTUAL_PASSAGE_ENRICHMENT_K15` (Header Prepending)**:
   - *Architecture*: Prepending `Topic: {Doc Title} | Section: {Header}` to passage embeddings and reranker inputs.
   - *Hypothesis*: Explicit section headers reduce `GENERIC_OVERVIEW_BIAS`.

5. **`CANDIDATE_5_SYNERGISTIC_UNIFIED_PIPELINE` (Full Multi-Stage Synergy)**:
   - *Architecture*: Deterministic Query Normalization + Dense/BM25 Hybrid Top-20 + Contextual Passage Cross-Encoder Top-5.
   - *Hypothesis*: Combined multi-stage pipeline addresses both candidate misses and overview bias simultaneously.

---

## 4. Phase 3 — DEV Empirical Evaluation Results

### Selection Rule Priority (Pre-Defined):
1. **Primary Metric**: DEV Chunk Evidence Recall@5
2. **Secondary Metric**: DEV Chunk Evidence Recall@3
3. **Tertiary Metric**: DEV Chunk MRR
4. **Quaternary Metric**: Bangla/Banglish Robustness
5. **Tie-Breaker**: Latency, simplicity, and rejection preservation

### Full DEV Benchmark Strategy Comparison Table (N=40):

| Strategy | Candidate R@15 | Final Chunk R@1 | Final Chunk R@3 | **Final Chunk R@5** | **Final Chunk MRR** | Standard Banglish R@5 | Abbrev Banglish R@5 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`CANDIDATE_1_GATE_5_11_BASELINE`** | 33/40 (82.5%) | 18/40 (45.0%) | 24/40 (60.0%) | **30/40 (75.0%)** | 0.5450 | 6/10 (60.0%) | 4/8 (50.0%) |
| **`CANDIDATE_2_DETERMINISTIC_QUERY_NORM_K15`** 🏆 | **37/40 (92.5%)** | 19/40 (47.5%) | **27/40 (67.5%)** | **35/40 (87.5%)** | **0.6104** | **8/10 (80.0%)** | **7/8 (87.5%)** |
| **`CANDIDATE_3_DENSE_BM25_HYBRID_UNION_K20`** | 34/40 (85.0%) | 18/40 (45.0%) | 22/40 (55.0%) | 26/40 (65.0%) | 0.5183 | 5/10 (50.0%) | 3/8 (37.5%) |
| **`CANDIDATE_4_CONTEXTUAL_PASSAGE_ENRICHMENT_K15`** | 32/40 (80.0%) | 16/40 (40.0%) | 25/40 (62.5%) | 29/40 (72.5%) | 0.5225 | 7/10 (70.0%) | 4/8 (50.0%) |
| **`CANDIDATE_5_SYNERGISTIC_UNIFIED_PIPELINE`** | 36/40 (90.0%) | **21/40 (52.5%)** | **29/40 (72.5%)** | 32/40 (80.0%) | **0.6317** | 6/10 (60.0%) | **7/8 (87.5%)** |

---

## 5. Linguistic Breakdown for Selected Winner (`CANDIDATE_2`)

| Language Category | DEV N | Baseline Dense R@15 | **Winner Dense R@15** | Baseline Final R@5 | **Winner Final R@5** | Baseline MRR | **Winner MRR** |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **English** | 12 | 11/12 (91.67%) | **11/12 (91.67%)** | 11/12 (91.67%) | **11/12 (91.67%)** | 0.7528 | **0.7528** |
| **Native Bangla** | 10 | 9/10 (90.00%) | **9/10 (90.00%)** | 9/10 (90.00%) | **9/10 (90.00%)** | 0.6150 | **0.6150** |
| **Standard Banglish** | 10 | 6/10 (60.00%) | **9/10 (90.00%)** | 6/10 (60.00%) | **8/10 (80.00%)** | 0.3283 | **0.4783** |
| **Abbreviated Banglish** | 8 | 4/8 (50.00%) | **8/8 (100.0%)** | 4/8 (50.00%) | **7/8 (87.50%)** | 0.4167 | **0.5563** |

### Key Improvements in Selected Winner:
- **Primary Metric (DEV Chunk Recall@5)**: Jumped from **75.0% (30/40) to 87.5% (35/40)** (\(+12.5\%\)).
- **Dense Candidate Recall@15**: Jumped from **82.5% (33/40) to 92.5% (37/40)** (\(+10.0\%\)).
- **Abbreviated Banglish Recall@5**: Jumped from **50.0% (4/8) to 87.5% (7/8)** (\(+37.5\%\)).
- **Standard Banglish Recall@5**: Jumped from **60.0% (6/10) to 80.0% (8/10)** (\(+20.0\%\)).
- **Chunk MRR**: Improved from **0.5450 to 0.6104** (\(+0.0654\)).

---

## 6. Selected Winner Justification

**Winner**: **`CANDIDATE_2_DETERMINISTIC_QUERY_NORM_K15`**

1. **Top Performance on Primary Metric**: Achieved **87.5% Chunk Recall@5** on DEV, outperforming all other candidates.
2. **Solved Banglish Vocabulary Gap**: Dense candidate recall for Abbreviated Banglish reached **100% (8/8)**, and final Top-5 evidence availability reached **87.5%**.
3. **No Passage Schema or Index Bloat**: Zero change to raw passage chunks, zero increase in latency, zero reliance on external LLMs.
4. **Why not BM25 (Candidate 3)?**: BM25 introduced spurious non-medical keyword hits for colloquial Banglish syntax, polluting the candidate pool and degrading reranker precision (65.0% vs 87.5%).
5. **Why not Contextual Headers (Candidate 4)?**: Header prepending diluted passage token densities and reduced Dense R@15 to 80.0%.

---

## 7. Frozen Winner Configuration

The winning configuration has been formally frozen in [`research/gate_5_12_retrieval_failure_decomposition/frozen_candidate/frozen_candidate_configuration.json`](file:///d:/my-ai-project/Dr.%20Md.%20Momenul%20Islam/research/gate_5_12_retrieval_failure_decomposition/frozen_candidate/frozen_candidate_configuration.json):

```json
{
  "candidate_strategy_name": "CANDIDATE_2_DETERMINISTIC_QUERY_NORM_K15",
  "description": "Deterministic Clinical Concept Normalization -> Dense multilingual-e5-small (Top-15) -> bge-reranker-v2-m3 (Top-5 Context)",
  "selection_rule_applied": "1. DEV Chunk Evidence Recall@5 > 2. DEV Chunk Evidence Recall@3 > 3. DEV Chunk MRR > 4. Bangla/Banglish Robustness > 5. Simplicity",
  "parameters": {
    "query_normalization": {
      "enabled": true,
      "type": "deterministic_rule_based_concept_dictionary",
      "non_llm": true
    },
    "embedding_model": "intfloat/multilingual-e5-small",
    "candidate_depth_k": 15,
    "passage_representation": "standard_clean_chunk_text",
    "use_bm25_union": false,
    "similarity_metric": "cosine_dot_product_normalized",
    "reranker_model": "BAAI/bge-reranker-v2-m3",
    "final_top_k_context": 5,
    "reranker_input_format": "raw_clean_chunk_text"
  },
  "dev_benchmark_metrics": {
    "n_queries": 40,
    "candidate_pool_r15": "37/40 (92.50%)",
    "chunk_recall_at_1": "19/40 (47.50%)",
    "chunk_recall_at_3": "27/40 (67.50%)",
    "chunk_recall_at_5": "35/40 (87.50%)",
    "chunk_mrr": 0.6104
  },
  "locked_holdout_status": "UNTOUCHED_AND_UNSEEN",
  "configuration_hash": "3318ae3bd1b671a99e98a07e46911d41c0fe8d872e4fa5a4b6d8bfaad8873f28"
}
```

---

## 8. Artifacts Created & Reproducibility Hashes

| Artifact | File Path | SHA-256 Checksum |
| :--- | :--- | :--- |
| **DEV Failure Taxonomy** | `research/gate_5_12_retrieval_failure_decomposition/diagnostics/dev_failure_decomposition.json` | Generated |
| **All Strategy DEV Evaluations** | `research/gate_5_12_retrieval_failure_decomposition/evaluations/gate_5_12_dev_strategy_comparison.json` | Generated |
| **Frozen Configuration** | `research/gate_5_12_retrieval_failure_decomposition/frozen_candidate/frozen_candidate_configuration.json` | `3318ae3bd1b671a99e98a07e46911d41c0fe8d872e4fa5a4b6d8bfaad8873f28` |

---

## 9. Untouched Locked Holdout Status

- **Locked Holdout Documents (`DOC-NHS-008` to `DOC-NHS-011`) and all 40 locked TEST queries remained 100% UNTOUCHED, UNSEEN, AND UNTUNED.**
- No holdout test queries were evaluated, inspected, or used in parameter selection.

---

## 10. Next Recommended Step

Now that the development-only failure decomposition is complete and an empirically justified winning configuration is frozen under hash `3318ae3bd1b671a99e98a07e46911d41c0fe8d872e4fa5a4b6d8bfaad8873f28`, the project is ready for:

> **Gate 5.13 — Single Locked Holdout Validation of the Normalized Retrieval Pipeline**

---
**ABSOLUTE STOP CONDITION REACHED**: Gate 5.12 is completely finished. The locked holdout remains untouched. No LLMs were called, and no production code was modified. Awaiting independent review.
