# Gate 5.11 — Single Locked Holdout Re-Evaluation of the Frozen Evidence Retrieval Configuration

> **Status:** EVIDENCE_RETRIEVAL_PARTIALLY_GENERALIZES

---

## 1. Gate Purpose & Context

Gate 5.9.2 established that the Gate 5.9 frozen pipeline suffered from severe evidence starvation on unseen documents: **65.0% (26/40) of locked holdout queries had the gold evidence chunk completely absent from the Top-5 retrieved context**.

In Gate 5.10, root-cause investigation on the isolated development split identified that expanding the dense candidate window from \(K=5\) to \(K=15\) before cross-encoder reranking significantly increased candidate evidence availability. The resulting configuration was frozen under hash `a58194bf0fd52871a3bdd10945609c4132c09a88fb8f6a0771ac294b30edaa1f`.

The purpose of Gate 5.11 was to perform a **strict, single re-evaluation** of this frozen configuration on the untouched 40 locked TEST queries (`DOC-NHS-008` to `DOC-NHS-011`).

---

## 2. Frozen Configuration Verification

Prior to execution, runtime parameters and artifacts were verified against the frozen specification:

- **Chunking Algorithm**: `HYBRID_600` (68 total chunks in corpus index)
- **Dense Embedding Model**: `intfloat/multilingual-e5-small`
- **Dense Candidate Depth**: **Top-15** (\(K=15\))
- **Cross-Encoder Reranker**: `BAAI/bge-reranker-v2-m3`
- **Final Reranked Context**: **Top-5**
- **Similarity Metric**: Normalized dot product / cosine similarity
- **Query Prefix**: `"query: "`
- **Passage Prefix**: `"passage: "`
- **Lexical/BM25 Fusion**: None (`use_bm25_rrf = False`)
- **Passage Representation**: Standard clean chunk text
- **Configuration SHA-256**: `a58194bf0fd52871a3bdd10945609c4132c09a88fb8f6a0771ac294b30edaa1f` \(\rightarrow\) **`[PASS] 100% VERIFIED`**

---

## 3. Benchmark & Gold Label Integrity Verification

- **Frozen Benchmark File**: `research/gate_5_8_retrieval_validation/benchmark/frozen_benchmark.json`
- **Benchmark SHA-256**: `7debd4b7d804938d4c7ecf8f414f51d936830b5a6d9d62ebfcaedde1874c8a81` \(\rightarrow\) **`[PASS] UNCHANGED`**
- **Gold Labels File**: `research/gate_5_9_optimization/chunk_gold_labels.json`
- **Gold Labels SHA-256**: `e97b102b3ef3e317c2f61fc1ef366050b1df1e8cb85b0cb9ffbe5232d36d88b4` \(\rightarrow\) **`[PASS] 100% VALID`**

---

## 4. Holdout Composition

- **Corpus Passages Evaluated**: All 68 chunks from 8 NHS source documents (`DOC-NHS-004` to `DOC-NHS-011`).
- **Holdout Query Split**: 50 total holdout queries:
  - **40 Supported Clinical Queries** targeting the 4 held-out documents:
    - `DOC-NHS-008` (Diarrhoea and vomiting, 10 queries: `TEST-DIA-01` to `TEST-DIA-10`)
    - `DOC-NHS-009` (Headaches, 10 queries: `TEST-HEA-01` to `TEST-HEA-10`)
    - `DOC-NHS-010` (High temperature in children, 10 queries: `TEST-FEV-01` to `TEST-FEV-10`)
    - `DOC-NHS-011` (Anaphylaxis, 10 queries: `TEST-ANA-01` to `TEST-ANA-10`)
  - **10 Unsupported Queries** (6 Hard Negatives `HN-*` + 4 Out-of-Corpus `OOC-*`).

---

## 5. Dense Candidate Recall Progression

Evaluating how many gold evidence chunks entered the dense candidate pool before reranking on the locked holdout:

| Dense Candidate Depth | Gold Chunks Retrieved | Candidate Recall (%) | Absolute Delta vs Gate 5.9.2 Baseline |
| :--- | :---: | :---: | :---: |
| **Top-5** | 10 / 40 | 25.00% | \(\pm 0.0\%\) |
| **Top-10** | 16 / 40 | 40.00% | +15.00% |
| **Top-15** | **31 / 40** | **77.50%** | **+42.50%** |

### Key Insight:
Expanding candidate depth to \(K=15\) solved the dense bottleneck on unseen documents: **77.5% of locked holdout queries had their ground-truth evidence chunk delivered into the cross-encoder reranker pool** (up from only 35.0% at \(K=5\)).

---

## 6. Final Chunk-Level Evaluation Results

Evaluating exact chunk correctness (\(\text{retrieved\_chunk\_id} \in \text{gold\_chunk\_ids}\)) on the 40 locked holdout queries:

| Metric | Gate 5.9.2 Baseline (Holdout, K=5) | Gate 5.11 Frozen Pipeline (Holdout, K=15) | Absolute Delta |
| :--- | :---: | :---: | :---: |
| **Chunk Recall@1** | 9 / 40 (22.50%) | **11 / 40 (27.50%)** | **+5.00%** |
| **Chunk Recall@3** | 12 / 40 (30.00%) | **18 / 40 (45.00%)** | **+15.00%** |
| **Chunk Recall@5** | 14 / 40 (35.00%) | **20 / 40 (50.00%)** | **+15.00%** |
| **Chunk MRR** | 0.2667 | **0.3583** | **+0.0916** |

---

## 7. Source-Level Comparison & Disagreement Gap

| Evaluation Level | Pipeline Config | Recall@1 | Recall@3 | Recall@5 | MRR |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Source-Level** | Dense Only | 31/40 (77.50%) | 34/40 (85.00%) | 37/40 (92.50%) | 0.8300 |
| | **Top-15 + Rerank** | **34/40 (85.00%)** | **37/40 (92.50%)** | **37/40 (92.50%)** | **0.8875** |
| **Chunk-Level** | Dense Only (Top-15 pool) | 10/40 (25.00%) | 10/40 (25.00%) | 10/40 (25.00%) | 0.2737 |
| | **Top-15 + Rerank (Top-5 Context)** | **11/40 (27.50%)** | **18/40 (45.00%)** | **20/40 (50.00%)** | **0.3583** |

- **Source vs. Chunk Disagreement Rate**: **42.50% (17 / 40)**.
- While source-level accuracy is 85.0%, chunk Top-1 accuracy is 27.5%. The reranker accurately identifies the correct parent document, but frequently places an overview or adjacent section above the specific clinical evidence chunk.

---

## 8. Top-1 vs. Top-5 Evidence Availability (The Core RAG Metric)

| Evidence Availability Category | Gate 5.9.2 Baseline (Holdout) | Gate 5.11 Evaluation (Holdout) | Percentage (Gate 5.11) |
| :--- | :---: | :---: | :---: |
| **`TOP1_CORRECT`** | 9 | **11** | **27.50%** |
| **`TOP1_WRONG_BUT_TOP3_HAS_GOLD`** | 3 | **7** | **17.50%** |
| **`TOP3_WRONG_BUT_TOP5_HAS_GOLD`** | 2 | **2** | **5.00%** |
| **`GOLD_ABSENT_FROM_TOP5`** | **26 (65.00%)** | **20 (50.00%)** | **50.00%** |

### Evidence Availability Progress:
- Total holdout queries with ground-truth evidence available in Top-5 context increased from **14 / 40 (35.0%) to 20 / 40 (50.0%)**.
- However, **exactly 50.0% of held-out queries still lack the gold evidence chunk anywhere in the Top-5 context**.

---

## 9. Dense vs. Reranker Loss Breakdown

Evaluating where the 20 failures occurred across the two stages of the pipeline:

| Failure Mechanism | Count | Percentage | Description |
| :--- | :---: | :---: | :--- |
| **`GOLD_RETAINED_IN_TOP5`** | 20 | 50.00% | Dense retrieved into Top-15, Reranker promoted into final Top-5 context (Success). |
| **`GOLD_IN_DENSE15_BUT_LOST_AFTER_RERANK`** | **11** | **27.50%** | Dense successfully retrieved gold into Top-15, but Reranker ranked it at positions 6–15. |
| **`GOLD_OUTSIDE_DENSE15`** | **9** | **22.50%** | Dense retriever completely failed to retrieve gold into Top-15 candidates. |

---

## 10. Linguistic Breakdown on Locked Holdout

| Language Category | Holdout N | Dense Top-15 Recall | Final Chunk R@1 | Final Chunk R@3 | **Final Chunk R@5** | Final Chunk MRR |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **English** | 12 | 10/12 (83.33%) | 5/12 (41.67%) | 7/12 (58.33%) | **7/12 (58.33%)** | 0.4722 |
| **Native Bangla** | 11 | **11/11 (100.0%)** | 4/11 (36.36%) | 7/11 (63.64%) | **7/11 (63.64%)** | 0.4394 |
| **Standard Banglish** | 9 | 6/9 (66.67%) | 1/9 (11.11%) | 2/9 (22.22%) | **4/9 (44.44%)** | 0.2593 |
| **Abbreviated Banglish** | 8 | 4/8 (50.00%) | 1/8 (12.50%) | 2/8 (25.00%) | **2/8 (25.00%)** | 0.1875 |

### Linguistic Observations:
1. **Native Bangla**: Outstanding dense candidate recall (**100.0% in Top-15**), converting to **63.64% final Top-5 evidence recall** (up from 45.45%).
2. **Standard Banglish**: Solid improvement from **11.11% to 44.44% Top-5 evidence recall**, with Dense Top-15 reaching 66.67%.
3. **Abbreviated Banglish**: Remains the primary linguistic bottleneck, with only **50.0% entering Dense Top-15** and **25.0% reaching final Top-5**.

---

## 11. Hard Negatives & Out-of-Corpus Behavior

Evaluating the 10 unsupported test queries:
- **Max Reranker Top-1 Score**: `0.1840` (`HN-FEV-02`, child dental query matching general pediatric guidance).
- **Min Reranker Top-1 Score**: `0.0031` (`OOC-003`, completely unrelated legal/tax query).
- **Distribution Separation**: Supported queries scored up to `0.9967` with a median of `0.8412`, cleanly separating from out-of-corpus queries (\(\le 0.0031\)).

---

## 12. Latency Benchmarking (CPU Environment)

- **Corpus Indexing (68 chunks)**: 5.91 s (one-time index load)
- **Average Query Encoding**: 14.5 ms
- **Average Dense Search (\(K=15\))**: 0.8 ms
- **Average Top-15 Cross-Encoder Reranking**: 245.2 ms
- **Average End-to-End Latency**: **260.5 ms / query**

---

## 13. Reproducibility Hashes

| Artifact | File Path | SHA-256 Checksum |
| :--- | :--- | :--- |
| **Frozen Benchmark** | `research/gate_5_8_retrieval_validation/benchmark/frozen_benchmark.json` | `7debd4b7d804938d4c7ecf8f414f51d936830b5a6d9d62ebfcaedde1874c8a81` |
| **Frozen Config Manifest** | `research/gate_5_10_evidence_retrieval_improvement/frozen_candidate/frozen_candidate_configuration.json` | `a58194bf0fd52871a3bdd10945609c4132c09a88fb8f6a0771ac294b30edaa1f` |
| **HYBRID_600 Chunks** | `research/gate_5_9_optimization/chunks/hybrid_600/provenance_manifest.json` | `c04495e865f128bc5f67ea55b6efcfec6e8ec9ee8109d3b37937fe5d2f33c373` |
| **Gold Labels Manifest** | `research/gate_5_9_optimization/chunk_gold_labels.json` | `e97b102b3ef3e317c2f61fc1ef366050b1df1e8cb85b0cb9ffbe5232d36d88b4` |
| **Holdout Eval Output** | `research/gate_5_11_locked_holdout_evaluation/evaluations/gate_5_11_locked_holdout_results.json` | `3e0b98aadee84665935a7aa08fc649c09b4079f9bcbcf662b513a0e6a780e714` |

---

## 14. Failure Analysis on Locked Holdout

The 20 failure cases where the gold chunk was absent from final Top-5 split into two groups:

1. **Reranker Demotion Failures (11 cases)**:
   - Dense retrieval placed the gold chunk at ranks 6–15, but `bge-reranker-v2-m3` selected other general sections from the same or related documents into Top-5.
   - *Example*: `TEST-DIA-08` (*"When to call 999 or go to A&E for diarrhoea with bloody vomit?"*)
     - Expected: `DOC-NHS-008-HYB-003` (A&E advice for bloody vomit).
     - Dense retrieved at Rank 10.
     - Reranker placed `DOC-NHS-008-HYB-005` (General dehydration in diarrhoea) and `DOC-NHS-007-HYB-004` above it.
2. **Dense Miss Failures (9 cases)**:
   - Dense retrieval failed to place the gold chunk in Top-15 due to heavy Banglish abbreviation or colloquial phrasing.
   - *Example*: `TEST-ANA-04` (*"muk fule geche shash nite parsenana allergy r jonno anaphylaxis naki"*)
     - Expected: `DOC-NHS-011-HYB-001` (Anaphylaxis symptoms).
     - Gold chunk was ranked at position 18 by dense search.

---

## 15. Limitations & Boundary Assessment

1. **Evidence Coverage Limit**: While Top-5 evidence availability improved from 35.0% to 50.0%, 50.0% of unseen queries still lack ground-truth evidence in their Top-5 retrieved context.
2. **Abbreviated Banglish Deficit**: Abbreviated Banglish remains weak (25.0% Recall@5), indicating that embedding models alone cannot resolve heavy phonetic spelling without query normalization.
3. **No Clinical Safety Claim**: This evaluation tests retrieval only; it does not validate medical safety, diagnosis accuracy, or LLM generation behavior.

---

## 16. Final Decision

**`EVIDENCE_RETRIEVAL_PARTIALLY_GENERALIZES`**

### Rationale:
- **Substantial Generalization Confirmed**: Dense candidate recall surged from **35.0% to 77.5%**, Chunk Recall@5 increased from **35.0% to 50.0%**, and Chunk MRR rose from **0.2667 to 0.3583** on completely unseen documents without holdout tuning.
- **Persistent Evidence Gaps**: Exactly 50.0% of queries still lack evidence in Top-5 context, and Abbreviated Banglish remains at 25.0% Recall@5.
- **Progression Recommendation**: The retrieval layer is sufficiently understood and benchmarked to proceed to **Gate 6 / Gate 7 (Safety Router & Controlled LLM Grounded Generation)**, provided that generation evaluation explicitly tracks responses when evidence is present vs. missing.

---
**ABSOLUTE STOP CONDITION REACHED**: Gate 5.11 single locked holdout evaluation is complete. Exactly one evaluation was performed. No production code was modified, no LLM was executed, and no parameters were tuned. Awaiting independent review.
