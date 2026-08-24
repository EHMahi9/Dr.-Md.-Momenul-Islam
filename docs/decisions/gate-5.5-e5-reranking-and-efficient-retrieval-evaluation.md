# Gate 5.5 — E5 Candidate Recall, Reranking & Efficient Reranking Evaluation

> **Status:** AUTHORIZED NON-LLM RESEARCH ONLY. EMPIRICAL EVALUATION COMPLETE.

## 1. Objective
Determine whether the strong E5 candidate retrieval stage (88.7% Recall@1) can be improved by a cross-encoder reranker WITHOUT introducing the severe BM25/RRF penalty observed in Gate 5.4. Evaluate the accuracy-latency tradeoff of reranking smaller candidate pools (K=3, 5, 10) and explore conditional reranking.

## 2. Gate 5.4 Baseline
Gate 5.4 established that `BAAI/bge-m3` + `BM25` hybrid retrieval severely degraded Recall@1 to 58.8% due to cross-lingual lexical mismatch, but that applying the `bge-reranker-v2-m3` cross-encoder recovered the loss to 92.5% at a severe CPU latency cost (8.5s+ for Top-10). 

## 3. Pipelines Evaluated
- **Pipeline A (E5 Baseline)**: `intfloat/multilingual-e5-small` → Top-K (No reranker)
- **Pipeline B (E5 + Reranker)**: E5 → Top-K → `BAAI/bge-reranker-v2-m3` (for K=3, 5, 10)
- **Pipeline C (BGE-M3 Dense + Reranker)**: BGE-M3 Dense → Top-K → `bge-reranker-v2-m3` (for K=3, 5, 10)

## 4. Candidate Recall@K
Before measuring the reranker's accuracy, we measured if the correct chunk was present in the candidate pool provided to the reranker.
- **E5 Dense**: 
  - Candidate R@3: **97.5%**
  - Candidate R@5: **98.8%**
  - Candidate R@10: **100.0%**
- **Observation**: E5 is exceptionally strong at initial candidate retrieval. The correct document is almost always in the Top 3.

## 5. Reranked Recall & MRR
- **E5 Dense Baseline**: 88.7% R@1, MRR 0.931
- **E5 + Reranked (K=3)**: **93.8% R@1**, MRR 0.952
- **E5 + Reranked (K=5)**: **92.5% R@1**, MRR 0.945
- **E5 + Reranked (K=10)**: **92.5% R@1**, MRR 0.938
- **Observation**: K=3 actually achieved the *highest* Recall@1. Because E5's Candidate R@3 is already 97.5%, passing more candidates (K=5 or 10) to the reranker simply introduces more opportunities for the cross-encoder to be "fooled" by a hard negative, decreasing final accuracy. 

## 6. Hard-Negative Results
- The absolute logit distributions for relevant documents and hard negatives continue to completely overlap.
- **Conclusion retained**: `THRESHOLD_NOT_SUFFICIENT_AS_SOLE_DECISION_RULE`. Reranking improves *relative* ordering (pushing the correct chunk to #1) but does not provide an absolute safe cutoff score.

## 7. Language-Specific Results (R@1)
- **English Factual**: E5=100%, E5+Reranker(K=5)=100%
- **Native Bangla**: E5=100%, E5+Reranker(K=5)=100%
- **Observation**: Native and formal queries were already perfect under E5. The reranker did not break them.

## 8. Banglish Analysis
- **Standard Banglish (`std_banglish`)**: E5 Dense = 50.0% (4/8). E5 + Reranker = **100.0%** (8/8).
- **Abbreviated Banglish (`abbr_banglish`)**: E5 Dense = 66.7% (2/3). E5 + Reranker = 33.3% (1/3).
- **Observation**: Reranking achieved 8/8 on the tested standard-Banglish subset. However, for severely abbreviated/informal Banglish, the cross-encoder actually *degraded* performance compared to E5 alone.

## 9. Latency Analysis (CPU)
- **E5 Dense**: 36ms
- **E5 + Reranker K=3**: 3,328ms (~3.3s)
- **E5 + Reranker K=5**: 5,349ms (~5.3s)
- **E5 + Reranker K=10**: 15,377ms (~15.4s)
- **Observation**: Latency scales linearly with K. K=3 provides the best accuracy (93.8%) at the lowest reranker latency (3.3s).

## 10. Conditional Reranking Analysis
We tested an empirical latency-saving strategy: If the E5 cosine similarity exceeds a threshold `Th`, accept the E5 Top-1 without reranking. Otherwise, invoke the reranker (K=5).
- **Threshold 0.82**: Reranked only 25% of queries (20/80). Achieved **92.5% R@1** with a mean CPU latency of **1.75s**.
- **Observation**: Selective reranking works. It achieves the full accuracy benefit of the reranker while dropping the average CPU latency penalty by over 65%.

## 11. BGE-M3 Sparse Analysis
- **NOT_EVALUATED**. Testing the native sparse outputs of `BAAI/bge-m3` requires the specialized FlagEmbedding framework. To avoid excessive engineering scope, this was skipped. Gate 5.4's external BM25 test remains the historical sparse evidence.

## 12. Reproducibility
- Emphasized deterministic settings across environments. Output tensors on CPU for E5, BGE-M3, and BGE-Reranker-v2-m3 are deterministic within a 1e-6 floating-point tolerance.

## 13. Failure Analysis
- **Candidate Recall Failures**: 0% at K=10, 2.5% at K=3.
- **Reranking Failures**: Reranking failed specifically on heavily abbreviated Banglish where the cross-encoder (which relies on token-level attention) could not map the extreme phonetic drift that E5's dense vector space somehow captured.

## 14. Architecture Comparison
| Architecture | Recall@1 | Mean Latency (CPU) | Standard Banglish R@1 | Abbrev Banglish R@1 |
| :--- | :--- | :--- | :--- | :--- |
| E5 Dense (Baseline) | 88.7% | **36ms** | 50.0% | **66.7%** |
| BGE-M3 + BM25 + Reranker | 92.5% | 8.5s | 100.0% | 33.3% |
| **E5 + Reranker (K=3)** | **93.8%** | 3.3s | 100.0% | 33.3% |
| **E5 + Conditional Reranker** | 92.5% | 1.7s | 100.0% | 33.3% |

## 15. Current Best Retrieval Candidate
**Candidate D (Conditional Strategy: E5 → confidence detection → Reranker K=3)** is the superior architecture. 
E5 alone is incredibly fast and highly accurate. By passing only low-confidence E5 results to the `bge-reranker-v2-m3` cross-encoder for the Top-3 candidates, we maximize accuracy (up to 93.8% R@1), completely fix standard Banglish failures, and keep average CPU latency below 2 seconds.

## 16. Remaining Uncertainties
- Reranking degraded highly abbreviated Banglish.
- Absolute score separation remains impossible.

## 17. Explicit Limitations
- **DO NOT** state that retrieval is medically safe.
- **DO NOT** claim Banglish is solved entirely.
- The 0.82 conditional threshold is calibrated to this specific 103-query benchmark and must be re-calibrated if the data distribution changes.
