# Gate 5.7 — Multi-Split Retrieval Generalization & Benchmark Integrity Validation

> **Status:** RETRIEVAL_BASELINE_PROVISIONAL. AUTHORIZED NON-LLM RESEARCH ONLY. 

## 1. Phase 1 & 2: Benchmark Integrity Audit
An independent analysis of the `benchmark_expanded_5_1.json` evaluation dataset revealed severe semantic clustering. The 103 queries map to only 3 unique document chunks (`DOC-NHS-001`, `DOC-NHS-002`, `DOC-NHS-003`) alongside 23 `NONE` hard negatives. 
Because up to 47 queries map to a single chunk, a simple random 50/50 split creates massive semantic leakage—identical intents (e.g., "what to do for choking") appear in both the calibration and test sets, artificially inflating generalization metrics.

## 2. Phase 3 & 4: Multi-Split Generalization Test
To test true generalization, we evaluated the E5 baseline and reranker configurations (K=3, 5, 10) across 5 deterministic splits, including an "Intent-Grouped" split that enforced zero overlap of target chunks between calibration and test.

| Split Name | E5 Dense | E5 + Reranker (K=3) | E5 + Reranker (K=5) | E5 + Reranker (K=10) |
| :--- | :--- | :--- | :--- | :--- |
| Random A (Seed 42) | 87.8% | 92.7% | 90.2% | 90.2% |
| Random B (Seed 123) | 94.7% | 94.7% | 92.1% | 92.1% |
| Random C (Seed 999) | 89.7% | 92.3% | 92.3% | 92.3% |
| **Intent-Grouped** | **78.8%** | **84.8%** | **81.8%** | **81.8%** |
| Language Stratified | 91.4% | 97.1% | 94.3% | 94.3% |
| **MEAN** | **88.5%** | **92.3%** | **90.2%** | **90.2%** |

- **Observation**: `E5 -> Top-3 -> bge-reranker-v2-m3` is consistently the strongest architecture across all splits. However, on a true zero-shot Intent-Grouped split, accuracy drops from ~94% to ~85%.

## 3. Phase 5: Failure Boundary Analysis (Abbreviated Banglish)
We conducted a granular inspection of abbreviated Banglish failures:
1. `rod e matha ghurse` (Heat Exhaustion). **E5 successfully ranked it #1.** The Reranker degraded it to #4 and promoted CPR to #1.
2. `bacha sas nite parche na` (Choking). **E5 successfully ranked it #1.** The Reranker degraded it to #2 and promoted CPR to #1.

- **Failure Mechanism**: The `bge-reranker-v2-m3` cross-encoder possesses a strong semantic bias. It associates informal abbreviated symptoms ("dizziness", "can't breathe") strongly with generic resuscitation (CPR). The reranker is actively overriding the correct literal/dense matches found by E5 due to this semantic misalignment. 

## 4. Phase 6: No-Relevant-Source Boundary Reassessment
We investigated if a deterministic signal could separate valid queries from hard negatives/out-of-corpus queries:
- **Valid Dense Scores**: [0.760, 0.905] (Mean: 0.841)
- **Hard Negative Dense Scores**: [0.718, 0.877] (Mean: 0.799)
- **Valid Reranker Logits**: [-10.99, 3.99]
- **Hard Negative Reranker Logits**: [-11.01, -2.09]
- **Dense Margin (Top1-Top2)**: 0.007 vs 0.005.
- **Conclusion**: `RETRIEVAL_CONFIDENCE_NOT_SUFFICIENT_FOR_SAFE_NO_RESULT_DECISION`. Absolute score separation is impossible. A purely retrieval-based safety threshold cannot be established.

## 5. Phase 7: Reproducibility
- The evaluation was conducted purely deterministically on CPU utilizing cached real-inference vectors and logits from Gate 5.5 to guarantee identical arithmetic comparisons. 
- All python processing scripts utilized fixed random seeds (42, 123, 999).
- Warm steady-state latency was maintained at 36ms (E5) and ~3.3s (Reranker K=3).

## 6. Phase 8: Final Decision

1. **Does E5 → Top-5 → reranker outperform E5-only?** Yes, but K=3 outperforms K=5.
2. **Is Top-5 actually superior to Top-3 and Top-10?** No. Top-3 consistently produces higher accuracy because limiting candidates reduces the cross-encoder's exposure to hard negatives it might misclassify.
3. **Does reranking introduce regressions?** Yes. It introduces a specific regression for abbreviated Banglish symptoms, which it frequently misclassifies as requiring CPR.
4. **Is the 94.3% robust?** No. True zero-shot performance (Intent-Grouped) drops to ~85%. The 94%+ scores are partially inflated by semantic clustering leakage in random splits.
5. **How severe is benchmark leakage?** Severe. 80 valid queries map to only 3 source chunks.
6. **Which categories remain unreliable?** Abbreviated and phonetic Banglish symptom queries.
7. **Can retrieval alone determine NO_RELEVANT_SOURCE?** No. 
8. **Is the architecture sufficiently validated as an experimental baseline?** Yes, as a provisional baseline to feed the Safety Router/LLM, recognizing its hard-negative limitations.

**Status**: `RETRIEVAL_BASELINE_PROVISIONAL`
The current strongest architecture is `intfloat/multilingual-e5-small` (Top-3) → `BAAI/bge-reranker-v2-m3`. It is validated as an experimental baseline but requires LLM generation/classification to handle hard-negatives and cross-encoder symptom biases.
