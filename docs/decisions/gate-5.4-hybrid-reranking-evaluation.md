# Gate 5.4 — Hybrid Retrieval & Multilingual Reranking Evaluation

> **Status:** EMPIRICAL EVALUATION COMPLETE (NON-LLM)

## 1. Objective
Determine whether a multi-stage retrieval architecture (Dense + Sparse Hybrid + Multilingual Reranking) can meaningfully separate relevant chunks from hard-negative/out-of-corpus queries compared to dense retrieval alone, and evaluate its robustness on the Banglish frontier.

## 2. Gate 5.3 Findings Carried Forward
- **E5 Benchmark Baseline**: E5 achieves 88.7% Recall@1 natively without translation.
- **Threshold Limitation**: Gate 5.3 established that a threshold-only rule (e.g. cosine > 0.65) is structurally dangerous, as hard negative similarity overlaps significantly with true positive similarity.
- **Banglish Barrier**: Both dense embedding models (E5 and BGE) severely degrade on phonetic, abbreviated Banglish text.
- **Translation License Restriction**: The previously utilized NLLB translation model operates under a CC-BY-NC-4.0 license, relegating it to research-only evidence. It is excluded from the direct production pipeline consideration in this gate.

## 3. Model Identities and Licenses
- **Multilingual Dense Baseline (`intfloat/multilingual-e5-small`)**: MIT License. Dimension 384.
- **Multilingual Dense + Sparse (`BAAI/bge-m3`)**: MIT License. Dimension 1024.
- **Multilingual Reranker (`BAAI/bge-reranker-v2-m3`)**: Apache-2.0 License. Cross-encoder architecture.
- **Lexical/Sparse (`BM25Okapi`)**: Python `rank_bm25` module using standard tokenization.

## 4. Pipeline Definitions
Evaluated against the frozen 103-query benchmark (`benchmark_expanded_5_1.json`):
- **Pipeline A (E5 Dense Baseline)**: `intfloat/multilingual-e5-small` alone.
- **Pipeline B (BGE-M3 Dense Baseline)**: `BAAI/bge-m3` dense vectors alone.
- **Pipeline C (Hybrid BGE-M3 + BM25)**: Dense ranking fused with BM25 ranking via Reciprocal Rank Fusion (RRF, k=60).
- **Pipeline D (Hybrid + Reranker)**: The top 10 candidates from Pipeline C passed through the `bge-reranker-v2-m3` cross-encoder for final scoring and sorting.

## 5. Benchmark
The exact 103-query benchmark was strictly frozen and reused. No labels were modified.

## 6. Dense Retrieval Results
- **Pipeline A (E5)**: Recall@1 = 88.7%, MRR = 0.931
- **Pipeline B (BGE-M3)**: Recall@1 = 87.5%, MRR = 0.901
- **Observation**: BGE-M3 natively performs comparably to E5.

## 7. Hybrid Retrieval Results
- **Pipeline C (Hybrid BGE-M3 + BM25)**: Recall@1 collapsed to **58.8%** (MRR = 0.765).
- **Observation**: Because the corpus is English and queries are largely Bengali/Banglish, the purely lexical BM25 algorithm cannot map vocabulary. It actively penalizes semantically valid cross-lingual candidates in the RRF merge.

## 8. Reranker Results
- **Pipeline D (Hybrid + Reranker)**: Recall@1 surged to **92.5%** (MRR = 0.960).
- **Observation**: The cross-encoder successfully recovered candidates buried by BM25 and pushed overall accuracy higher than any single dense baseline.

## 9. Hard-Negative Analysis
| Pipeline | Relevant Top-1 Mean | Hard Negative Top-1 Mean | Overlap Status |
| :--- | :--- | :--- | :--- |
| **E5 Dense (Cosine)** | 0.841 | 0.846 | ⚠️ Severe (Hard Negatives score higher) |
| **BGE-M3 (Cosine)** | 0.517 | 0.551 | ⚠️ Severe (Hard Negatives score higher) |
| **Reranker (Logits)** | -5.159 | -5.773 | ⚠️ Unresolved (Complete boundary overlap) |

*Note: Reranker outputs unbounded logits, not cosine similarities. The range for Relevant was [-10.99, +3.99] and Hard Negative was [-7.75, -2.08].*

## 10. Banglish Analysis
Recall@1 by category for Standard Banglish (`std_banglish`):
- E5 Dense: 50.0% (4/8)
- BGE-M3 Dense: 37.5% (3/8)
- Hybrid Reranked: **100.0%** (8/8)

**Observation**: The cross-encoder drastically improves standard Banglish comprehension, but extreme abbreviated Banglish (`abbr_banglish`) still fails across all pipelines (33-67% R@1).

## 11. Threshold Analysis
**THRESHOLD_NOT_SUFFICIENT_AS_SOLE_DECISION_RULE**
While the reranker excels at relative ordering (Recall/MRR), its absolute logit scores for True Positives completely intermix with Hard Negatives. A static threshold cannot safely filter hard negatives out before LLM generation. The system must rely on an LLM-based Safety Router or generation-layer grounding to catch these edge cases.

## 12. Latency (CPU)
- **E5 Dense Pipeline**: ~100ms / query
- **BGE-M3 Dense Pipeline**: ~420ms / query
- **Hybrid Reranked Pipeline**: ~8,500ms (8.5s) / query
- **Observation**: The cross-encoder requires ~10 forward passes per query (Top-10), making it prohibitively slow for real-time CPU deployment.

## 13. Reproducibility
- `test_reproducibility.py` confirmed that BGE-M3 embeddings, BM25 scores, and BGE-Reranker logits are deterministic under CPU execution. Maximum absolute vector differences across consecutive runs were < 1e-6.

## 14. Failure Analysis
Failures persisting after reranking include:
- `baccar golay khabar atke gese` (Expected Choking, Got CPR)
- `rod e matha ghurse` (Expected Heat exhaustion, Got CPR)
- **Reason**: The cross-encoder cannot resolve highly ambiguous phonetic drift or cases where multiple life-threatening protocols share semantic clinical overlap.

## 15. Comparison Matrix

| Metric | E5 Baseline | BGE-M3 Baseline | Hybrid (BM25) | Hybrid + Reranker |
| :--- | :--- | :--- | :--- | :--- |
| **Recall@1** | 88.7% | 87.5% | 58.8% | **92.5%** |
| **Recall@5** | 98.8% | 91.2% | **100.0%** | **100.0%** |
| **Avg Latency** | **100ms** | 420ms | 420ms | 8,500ms |
| **Threshold Safe?** | No | No | No | No |
| **Banglish R@1** | 50.0% | 37.5% | 12.5% | **100.0%** |

## 16. Corrections / Limitations
- Hybrid BM25 fusion is detrimental for cross-lingual tasks without a translation layer.
- CPU inference for a 2.2GB cross-encoder is too slow for production constraints (8.5s latency).

## 17. Recommended Retrieval Architecture
**E5 Dense Baseline** remains the most practical production candidate for CPU-bound environments due to its 100ms latency and 88.7% R@1. If a GPU becomes available, the `BGE-M3 -> BGE-Reranker` pipeline offers superior semantic ordering (92.5% R@1).

## 18. Remaining Uncertainties
The inability to establish a structural hard-negative threshold means the retrieval layer cannot guarantee medical safety on its own. Safety must be enforced at the Router or Generation layers.
