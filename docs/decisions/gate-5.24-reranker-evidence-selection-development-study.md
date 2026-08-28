# Decision Record: Gate 5.24 — New Development Benchmark for Reranker Evidence-Selection Research

**Gate Reference:** GATE 5.24  
**Date:** 2026-08-28  
**Status:** `NO_SUFFICIENT_RERANKER_IMPROVEMENT`  
**Classification:** RERANKER DEVELOPMENT STUDY COMPLETE — FROZEN BASELINE RETAINED  

---

## 1. Objective & Permanent Holdout Lock Statement

Following Gate 5.23, which validated that dense candidate retrieval achieved 100% recall while all remaining failures stemmed from cross-encoder ranking demotions, Gate 5.24 constructed a **new, independent development benchmark (`DEV-24`)** across all 8 corpus documents to study reranker behavior and test evidence-selection hypotheses.

> [!IMPORTANT]
> **Permanent Holdout Lock Verification**:
> The `Gate 5.23` fresh locked benchmark (`fresh_locked_benchmark.json`, SHA-256: `a0267355...`) and the `Gate 5.20` holdout remain **permanently locked and untouched**. No tuning, parameter selection, or experimentation was conducted against any locked evaluation set.

---

## 2. DEV-24 Benchmark Specification & Integrity

- **Benchmark File**: [`research/gate_5_24_reranker_development_research/benchmark/dev24_benchmark.json`](file:///d:/my-ai-project/Dr.%20Md.%20Momenul%20Islam/research/gate_5_24_reranker_development_research/benchmark/dev24_benchmark.json)
- **Benchmark SHA-256**: `4d28ccfc59be69e2e790fb89ad71fc47479e8d92889c61a069d0af238750e485`
- **Total Queries**: 40 supported queries (5 per document across `DOC-NHS-004` through `DOC-NHS-011`)
- **Query Overlap Audit**: **0 duplicate or near-duplicate queries** against all 150 historical queries across Gates 5.8 through 5.23.
- **Linguistic Distribution**: 16 English, 8 Native Bangla, 8 Standard Banglish, 8 Abbreviated Banglish.
- **Design Focus**: Intra-document section discrimination (e.g. distinguishing specific aftercare vs. emergency escalation vs. clinical treatments within the same condition).

---

## 3. Epistemic Separation of Evidence

### VERIFIED FACTS
1. On `DEV-24` (N=40), the baseline frozen configuration (`STRATEGY_1_CONTROL_BASELINE`, SHA-256: `07f031da...`) achieved **Dense Recall@15 = 40/40 (100.0%)**, **Final Chunk Recall@5 = 36/40 (90.0%)**, **Chunk Recall@1 = 27/40 (67.5%)**, and **Chunk MRR = 0.7581**.
2. All 4 baseline failures on `DEV-24` were instances of `GOLD_IN_DENSE15_BUT_RERANKED_OUT`.
3. Dense-reranker score fusion (`STRATEGY_2`, $\lambda=0.15$) promoted 2 queries into Top-5 (`DEV24-AST-04` from Rank 7 to 5; `DEV24-BUR-05` from Rank 12 to 1), but simultaneously demoted 2 queries out of Top-5 (`DEV24-BUR-04` Rank 3 to 6; `DEV24-CUT-05` Rank 1 to 8).
4. Lexical overlap weighting (`STRATEGY_4`, $\alpha=0.05$) degraded Chunk Recall@5 from 90.0% to 85.0% (34/40), causing 2 regressions (`DEV24-DEH-04` Rank 4 to 6; `DEV24-FEV-05` Rank 3 to 6).
5. Dominant-source topical gating (`STRATEGY_3`, $\beta=1.20$) produced 0 net changes in Top-5 membership (36/40, MRR 0.7602).

### OBSERVATIONS
1. In `DEV24-BUR-05` ("pora jaygay borof lagale problem ki?"), cross-encoder scores for all candidates were below $0.0003$. In this low-confidence regime, cross-document generic emergency passages (`DOC-NHS-010-HYB-005`, `DOC-NHS-011-HYB-002`) out-scored the burn contraindication chunk. Dense score fusion successfully resolved this by leveraging the dense model's high topical confidence.
2. However, in `DEV24-CUT-05` ("wound e skin glue ba stitch lagbe kina kivabe jane?"), dense score fusion caused a severe regression (Rank 1 $\to$ Rank 8) because the dense retriever scored broad wound cleaning passages higher than the specific stitches/glue chunk, overriding the cross-encoder's accurate Rank-1 assessment.
3. Cross-encoder models exhibit an inherent saliency bias toward high-urgency keywords ("emergency", "Call 999", "seizure") over nuanced non-emergency procedural steps.

### HYPOTHESES
1. Score-level blending (dense fusion or lexical weighting) operates as an uncalibrated linear approximation that risks trading off fine-grained semantic comprehension for coarse topical alignment.
2. In single-topic medical QA where the candidate pool is already restricted to Top-15, cross-encoder ranking cannot be universally improved by static heuristic score adjustments without introducing collateral regressions.

---

## 4. Experimental Strategy Comparison (DEV-24, N=40)

| Strategy ID | Strategy Description | Chunk R@1 | Chunk R@3 | Chunk R@5 | Chunk MRR | Top-5 Movement |
|---|---|---|---|---|---|---|
| **STRATEGY_1** | **Control Baseline** (Track A + 0.85x Overview Debiasing) | **27/40 (67.5%)** | **32/40 (80.0%)** | **36/40 (90.0%)** | **0.7581** | **BASELINE** |
| STRATEGY_2 | Dense-Reranker Score Fusion ($\lambda=0.15$) | 27/40 (67.5%) | 32/40 (80.0%) | 36/40 (90.0%) | 0.7602 | +2 / -2 |
| STRATEGY_3 | Dominant-Source Topical Gating ($\beta=1.20$) | 27/40 (67.5%) | 32/40 (80.0%) | 36/40 (90.0%) | 0.7602 | +0 / -0 |
| STRATEGY_4 | Exact-Entity Lexical Overlap Anchoring ($\alpha=0.05$) | 27/40 (67.5%) | 31/40 (77.5%) | 34/40 (85.0%) | 0.7565 | +0 / -2 (Degraded) |
| STRATEGY_5 | Dual Topical-Lexical Anchor ($\lambda=0.10, \alpha=0.03$) | 27/40 (67.5%) | 33/40 (82.5%) | 36/40 (90.0%) | 0.7698 | +2 / -2 |

---

## 5. Decision & Scientific Justification

In accordance with Phase 8 of the pre-registered protocol:
> *"If no approach clearly improves the development data: Do NOT force a winner."*

None of the tested reranker post-processing or fusion strategies demonstrated Pareto superiority over the baseline. While Strategies 2 and 5 rescued 2 queries, they introduced equal numbers of severe regressions (e.g. `DEV24-CUT-05` dropping from Rank 1 to Rank 8). Strategy 4 actively degraded Recall@5.

Therefore, the formal decision is:
**`NO_SUFFICIENT_RERANKER_IMPROVEMENT`**

The frozen Gate 5.21 candidate configuration (`07f031da533d47666fb5abd242f8db47b90dc584a92c0b3f399abaaf51c02736`) is **retained without modification**.

---

## 6. Artifact Manifest

1. `research/gate_5_24_reranker_development_research/benchmark/dev24_benchmark.json` (SHA-256: `4d28ccfc...`)
2. `research/gate_5_24_reranker_development_research/benchmark/dev24_benchmark_spec.md`
3. `research/gate_5_24_reranker_development_research/diagnostics/baseline_dev24_results.json`
4. `research/gate_5_24_reranker_development_research/diagnostics/reranker_diagnostic_breakdown.json`
5. `research/gate_5_24_reranker_development_research/comparisons/gate_5_24_strategy_comparison.json`
6. `research/gate_5_24_reranker_development_research/candidate/frozen_baseline_retained.json`
7. `docs/decisions/gate-5.24-reranker-evidence-selection-development-study.md`
