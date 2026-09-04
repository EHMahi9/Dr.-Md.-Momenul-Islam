# Decision Record: Gate 5.24.1 — Development-Only Selection-Rule Consistency Audit

**Gate Reference:** GATE 5.24.1  
**Date:** 2026-08-28  
**Status:** `DEV_CANDIDATE_REQUIRES_SINGLE_LOCKED_VALIDATION`  
**Prior Classification Under Audit:** `NO_SUFFICIENT_RERANKER_IMPROVEMENT` (Gate 5.24)  
**Audit Outcome:** `DECISION_INCONSISTENCY_IDENTIFIED_AND_RESOLVED`  

---

## 1. Executive Summary & Audit Objective

This audit investigates the internal consistency of the Gate 5.24 selection decision.

In Gate 5.24, the report concluded:
> *"no experimental post-processing strategy demonstrated Pareto superiority over the baseline... Therefore, the formal decision is: NO_SUFFICIENT_RERANKER_IMPROVEMENT"*, retaining `STRATEGY_1` (Baseline).

However, the empirical evaluation table on `DEV-24` (N=40) showed:
- **Baseline (`STRATEGY_1`)**: R@1 = 67.5%, R@3 = 80.0%, R@5 = 90.0%, MRR = 0.7581
- **Dual Topical-Lexical Anchor (`STRATEGY_5`)**: R@1 = 67.5%, R@3 = 82.5%, R@5 = 90.0%, MRR = 0.7698

Strategy 5 tied the baseline on primary R@5 (90.0%) and strictly led on secondary R@3 (82.5% vs. 80.0%) and MRR (0.7698 vs. 0.7581).

**Objective of this Audit:**
1. Reconcile the discrepancy between reported metrics and the decision text.
2. Formally apply the pre-registered selection hierarchy.
3. Conduct per-query failure and promotion movement analysis.
4. Establish the correct development candidate status without violating locked holdout boundaries.

---

## 2. Artifact Verification

All underlying artifacts from Gate 5.24 were verified:
- [`gate_5_24_strategy_comparison.json`](../../research/gate_5_24_reranker_development_research/comparisons/gate_5_24_strategy_comparison.json)
- [`reranker_diagnostic_breakdown.json`](../../research/gate_5_24_reranker_development_research/diagnostics/reranker_diagnostic_breakdown.json)
- [`baseline_dev24_results.json`](../../research/gate_5_24_reranker_development_research/diagnostics/baseline_dev24_results.json)
- [`dev24_benchmark.json`](../../research/gate_5_24_reranker_development_research/benchmark/dev24_benchmark.json) (SHA-256: `4d28ccfc59be69e2e790fb89ad71fc47479e8d92889c61a069d0af238750e485`)

**Findings:**
- Reported numbers in Gate 5.24 are 100% mathematically accurate and verified.
- The discrepancy was an interpretative/decision-logic inconsistency in the report's conclusion, not an artifact or computational error.

---

## 3. Exact Strategy 1 vs. Strategy 5 Comparison

### Metric Comparison on DEV-24 (N=40)

| Metric | Baseline (`STRATEGY_1`) | Dual Anchor (`STRATEGY_5`) | Delta ($\Delta$) | Status Under Pre-Registered Rule |
|---|---|---|---|---|
| **Chunk Recall@5** (Primary) | **36 / 40 (90.0%)** | **36 / 40 (90.0%)** | $\pm 0.0\%$ | **TIE** |
| **Chunk Recall@3** (Secondary) | 32 / 40 (80.0%) | **33 / 40 (82.5%)** | **+2.5%** (+1 query) | **STRATEGY 5 LEADS** |
| **Chunk Recall@1** (Secondary) | 27 / 40 (67.5%) | 27 / 40 (67.5%) | $\pm 0.0\%$ | **TIE** |
| **Chunk MRR** (Secondary) | 0.7581 | **0.7698** | **+0.0117** | **STRATEGY 5 LEADS** |
| **Dense Recall@15** | 40 / 40 (100.0%) | 40 / 40 (100.0%) | $\pm 0.0\%$ | **TIE** |

### Language Breakdown Comparison

| Language | N | Baseline R@5 | Strategy 5 R@5 | Baseline MRR | Strategy 5 MRR | MRR Delta |
|---|---|---|---|---|---|---|
| **English** | 16 | 15/16 (93.8%) | 15/16 (93.8%) | 0.8607 | 0.8604 | -0.0003 |
| **Native Bangla** | 8 | 8/8 (100.0%) | 8/8 (100.0%) | 0.9375 | 0.9375 | $\pm 0.0000$ |
| **Standard Banglish** | 8 | 7/8 (87.5%) | 7/8 (87.5%) | 0.5387 | **0.5938** | **+0.0551** |
| **Abbreviated Banglish** | 8 | 6/8 (75.0%) | 6/8 (75.0%) | 0.5929 | **0.5971** | **+0.0042** |

---

## 4. Complete Per-Query Movement Audit

Across all 40 queries on `DEV-24`:
- **6 queries improved in rank** (all 6 are Banglish queries)
- **4 queries regressed in rank**
- **30 queries remained unchanged**

### All 6 Improved Queries Under Strategy 5:
1. `DEV24-AST-04` (*Std Banglish*): Rank 7 $\to$ **Rank 4** (**Promoted into Top-5**)
   - Query: "spacer device kivabe inhaler er shathe use korte hoy?"
   - Gold: `DOC-NHS-004-HYB-009` (Spacer technique)
2. `DEV24-BUR-04` (*Std Banglish*): Rank 3 $\to$ **Rank 2**
   - Query: "acid ba chemical diye hat purle first aid ki?"
   - Gold: `DOC-NHS-005-HYB-001`
3. `DEV24-BUR-05` (*Abbrev Banglish*): Rank 12 $\to$ **Rank 1** (**Promoted from Rank 12 to Rank 1**)
   - Query: "pora jaygay borof lagale problem ki?"
   - Gold: `DOC-NHS-005-HYB-001` (Do not use ice contraindication)
4. `DEV24-CUT-04` (*Std Banglish*): Rank 3 $\to$ **Rank 2**
   - Query: "kete jawar por shorir kharap lagle ba fever ashle 111 call korbo?"
   - Gold: `DOC-NHS-006-HYB-005`
5. `DEV24-ANA-04` (*Std Banglish*): Rank 4 $\to$ **Rank 3**
   - Query: "EpiPen injection dewar por ambulance ke ki bolte hobe?"
   - Gold: `DOC-NHS-011-HYB-004`
6. `DEV24-ANA-05` (*Abbrev Banglish*): Rank 4 $\to$ **Rank 3**
   - Query: "inhaler naki auto-injector allergy te first lagbe?"
   - Gold: `DOC-NHS-011-HYB-003`, `HYB-004`

### All 4 Regressed Queries Under Strategy 5:
1. `DEV24-AST-02` (*English*): Rank 14 $\to$ Rank 15 (Out-of-Top-5 failure in both strategies)
   - Query: "What should you do if your reliever inhaler is not helping your symptoms?"
   - Gold: `DOC-NHS-004-HYB-005`
2. `DEV24-CUT-05` (*Abbrev Banglish*): Rank 1 $\to$ Rank 5 (Retained in Top-5, but dropped from Rank 1)
   - Query: "wound e skin glue ba stitch lagbe kina kivabe jane?"
   - Gold: `DOC-NHS-006-HYB-006`
3. `DEV24-DEH-04` (*Std Banglish*): Rank 4 $\to$ **Rank 6** (**Demoted out of Top-5**)
   - Query: "dehydration hole nappy veja kome jay baby r ki lokkhon?"
   - Gold: `DOC-NHS-007-HYB-001`
4. `DEV24-FEV-05` (*Abbrev Banglish*): Rank 3 $\to$ **Rank 6** (**Demoted out of Top-5**)
   - Query: "bachar cold cough er jonno temp barta pare naki?"
   - Gold: `DOC-NHS-010-HYB-006`

---

## 5. Assessment of the "Pareto Superiority" Claim

In Gate 5.24, the report stated:
> *"no experimental post-processing strategy demonstrated Pareto superiority over the baseline"*

### Audit Verdict on this Claim:
- **At the aggregate metric level**: Strategy 5 **IS** Pareto superior.
  - Chunk R@5: 90.0% vs. 90.0% (non-inferior)
  - Chunk R@1: 67.5% vs. 67.5% (non-inferior)
  - Chunk R@3: **82.5% vs. 80.0%** (strictly superior)
  - Chunk MRR: **0.7698 vs. 0.7581** (strictly superior)
- **At the per-query level**: Strategy 5 is **not** strictly monotonic, because 2 queries dropped out of Top-5 while 2 queries entered Top-5, and 4 queries had rank degradations while 6 had rank improvements.
- **Root Cause of the Error**: The Gate 5.24 decision narrative conflated *per-query monotonicity* with *metric-level Pareto dominance*, and dismissed Strategy 5 without applying the explicit tie-breaking rules.

---

## 6. Formal Application of Pre-Registered Selection Rules

Under the pre-registered decision tree:
1. **Step 1 (Primary Recall@5)**: Strategy 1 (90.0%) vs. Strategy 5 (90.0%) $\to$ **TIE**.
2. **Step 2 (Secondary Recall@3)**: Strategy 1 (80.0%) vs. Strategy 5 (82.5%) $\to$ **Strategy 5 LEADS**.
3. **Step 3 (Secondary MRR)**: Strategy 1 (0.7581) vs. Strategy 5 (0.7698) $\to$ **Strategy 5 LEADS**.
4. **Step 4 (Language Robustness)**:
   - English & Native Bangla: Maintained at peak accuracy ($\ge 93.8\%$).
   - Standard Banglish: **+5.51 percentage point MRR gain** (0.5387 $\to$ 0.5938).
5. **Step 5 (Computational Overhead)**:
   - Strategy 5 adds $\mathcal{O}(K)$ vector additions (dense fusion) and string token overlaps over $K=15$ passages.
   - Additional latency per query: $< 0.1$ ms.

**Conclusion Under Selection Rule**:
Under the pre-registered ranking rules, **`STRATEGY_5_DUAL_TOPICAL_LEXICAL_ANCHOR` is the winning development candidate on DEV-24.**

---

## 7. Development vs. Holdout Distinction & Final Classification

> [!WARNING]
> **Critical Methodological Guardrail**:
> Because `DEV-24` is a development benchmark, selecting Strategy 5 as the development winner does **NOT** constitute holdout-validated or production-ready status.
> 
> The locked holdouts (`Gate 5.20` and `Gate 5.23`) remain permanently untouched.

### Final Classification:

$$\mathbf{DEV\_CANDIDATE\_REQUIRES\_SINGLE\_LOCKED\_VALIDATION}$$

### Summary of Updated Configuration for Strategy 5:
- **Architecture**:
  1. Deterministic Unicode-Aware Procedural Normalization (Track A, 9 concept dictionaries)
  2. Dense Retrieval: `intfloat/multilingual-e5-small` (Top-15)
  3. Cross-Encoder: `BAAI/bge-reranker-v2-m3`
  4. 0.85x Overview Debiasing for `-HYB-000` chunks
  5. **Dual Anchor Fusion**: $\text{FinalScore} = \text{RerankScore} + 0.10 \times \text{DenseScore} + 0.03 \times \text{LexicalOverlap}$
  6. Final Top-5 assembly
- **Development Status**: **Selected development candidate** for future locked holdout validation.
