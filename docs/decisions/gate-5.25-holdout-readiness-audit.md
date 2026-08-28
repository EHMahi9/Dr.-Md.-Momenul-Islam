# Decision Record: Gate 5.25 — Fresh Holdout Availability & Evaluation-Readiness Audit

**Gate Reference:** GATE 5.25  
**Date:** 2026-08-28  
**Status:** `NO_UNTOUCHED_HOLDOUT_EXISTS_EXPANDED_INGESTION_AND_BENCHMARK_REQUIRED`  
**Classification:** REPOSITORY AUDIT & METHODOLOGICAL READINESS ASSESSMENT COMPLETE  

---

## 1. Executive Summary & Objective

Following Gate 5.24.1, which established that **`STRATEGY_5_DUAL_TOPICAL_LEXICAL_ANCHOR`** is the top-performing development candidate on `DEV-24` ($90.0\%$ R@5, $82.5\%$ R@3, $0.7698$ MRR), Gate 5.25 conducted an exhaustive repository-wide audit to determine whether an untouched, independent holdout currently exists to evaluate this candidate.

**Core Findings of the Audit:**
1. **Zero Untouched Holdout Datasets Exist**: Every existing benchmark in the repository has either been evaluated against repeatedly, locked in prior gates, or used for development.
2. **All 8 Active Corpus Documents Are Exposed**: Every document in the active 68-chunk retrieval index (`DOC-NHS-004` to `DOC-NHS-011`) has been subjected to at least 20 historical query evaluations.
3. **To Establish True Source-Level Generalization**: Merely authoring new queries on the same 8 documents tests query paraphrase robustness within known topics, but **cannot prove generalizability to unseen clinical conditions**. A truly defensible holdout requires ingesting new, unseen NHS clinical documents.

---

## 2. Status of Strategy 5 Frozen Development Candidate

- **Candidate Name:** `STRATEGY_5_DUAL_TOPICAL_LEXICAL_ANCHOR`
- **Config Path:** [`research/gate_5_24_reranker_development_research/candidate/strategy_5_dev_candidate_configuration.json`](file:///d:/my-ai-project/Dr.%20Md.%20Momenul%20Islam/research/gate_5_24_reranker_development_research/candidate/strategy_5_dev_candidate_configuration.json)
- **Architecture:**
  - Track A Unicode-Safe Procedural Normalization (9 concept dictionaries)
  - Dense Model: `intfloat/multilingual-e5-small` (Candidate Depth $K=15$)
  - Cross-Encoder: `BAAI/bge-reranker-v2-m3`
  - Overview Debiasing: $0.85\times$ for `-HYB-000` chunks
  - **Dual Anchor Fusion:** $\text{FinalScore} = \text{RerankScore} + (0.10 \times \text{DenseCosineScore}) + (0.03 \times \text{LexicalOverlap})$
- **Current Status:** **Development Candidate Selected on DEV-24; Completely Unvalidated on Locked Holdout Data.**

---

## 3. Comprehensive Inventory of Datasets

### A. Consumed Datasets (Cannot Be Reused)

| Dataset / Benchmark File | Total Queries | Sources Targeted | Evaluation History / Purpose | Current Status |
|---|---|---|---|---|
| `gate_4c_ingestion/benchmark.json` & `expanded_benchmark.json` | 31 queries | `DOC-NHS-001` to `003` | Early feasibility & translation comparison | **Consumed (Historical)** |
| `gate_5_3_real_retrieval/benchmark_expanded_5_1.json` | 103 queries | `DOC-NHS-001` to `005` | Early retrieval pipeline testing | **Consumed (Historical)** |
| `gate_5_8_retrieval_validation/benchmark/frozen_benchmark.json` (DEV split) | 40 queries | `DOC-NHS-004` to `007` | Used for iterative optimization across Gates 5.9–5.21 | **Consumed (DEV Set)** |
| `gate_5_8_retrieval_validation/benchmark/frozen_benchmark.json` (TEST split) | 40 queries | `DOC-NHS-008` to `011` | Evaluated **4 separate times** (Gates 5.11, 5.13, 5.15, 5.20) | **Contaminated & Retired** |
| `gate_5_8_retrieval_validation/benchmark/frozen_benchmark.json` (UNSUP split) | 20 queries | `NONE` | Evaluated 4 times (HN & OOC queries) | **Contaminated & Retired** |
| `gate_5_22_fresh_benchmark/benchmark/fresh_locked_benchmark.json` | 50 queries | `DOC-NHS-004` to `011` | Evaluated in Gate 5.23 single-shot locked test | **Permanently Locked** |
| `gate_5_24_reranker_development_research/benchmark/dev24_benchmark.json` | 40 queries | `DOC-NHS-004` to `011` | Used to evaluate and select Strategy 5 | **Consumed (DEV Set)** |

### B. Untouched Datasets
- **Active Holdouts in Repository:** **NONE (0).**

---

## 4. Document-Level Exposure Analysis

All 8 documents in the active `HYBRID_600` corpus index have been repeatedly queried across previous development and test sets:

| Document ID | Medical Topic | Chunks in Index | Total Historical Query Evaluations | Splits Used In |
|---|---|---|---|---|
| `DOC-NHS-004` | Asthma | 18 | 20 queries | Gate 5.8 DEV, Gate 5.22 FRESH, Gate 5.24 DEV-24 |
| `DOC-NHS-005` | Burns and scalds | 5 | 20 queries | Gate 5.8 DEV, Gate 5.22 FRESH, Gate 5.24 DEV-24 |
| `DOC-NHS-006` | Cuts and grazes | 7 | 20 queries | Gate 5.8 DEV, Gate 5.22 FRESH, Gate 5.24 DEV-24 |
| `DOC-NHS-007` | Dehydration | 8 | 20 queries | Gate 5.8 DEV, Gate 5.22 FRESH, Gate 5.24 DEV-24 |
| `DOC-NHS-008` | Diarrhoea and vomiting | 8 | 20 queries | Gate 5.8 TEST (4x), Gate 5.22 FRESH, Gate 5.24 DEV-24 |
| `DOC-NHS-009` | Headaches | 5 | 20 queries | Gate 5.8 TEST (4x), Gate 5.22 FRESH, Gate 5.24 DEV-24 |
| `DOC-NHS-010` | High temperature (fever) in children | 7 | 20 queries | Gate 5.8 TEST (4x), Gate 5.22 FRESH, Gate 5.24 DEV-24 |
| `DOC-NHS-011` | Anaphylaxis | 10 | 20 queries | Gate 5.8 TEST (4x), Gate 5.22 FRESH, Gate 5.24 DEV-24 |

---

## 5. Epistemic Separation of Audit Evidence

### VERIFIED FACTS
1. There are **0 untouched, un-evaluated holdout benchmark files** in the project repository.
2. The active 68-chunk retrieval corpus consists of 8 NHS condition documents, all of which have been evaluated across multiple optimization and testing iterations.
3. Strategy 5's hyper-parameters ($\lambda=0.10, \alpha=0.03$) and Track A normalization dictionaries were developed using queries from these exact 8 documents.
4. Gate 5.23 fresh benchmark (`fresh_locked_benchmark.json`, SHA-256: `a0267355...`) was evaluated in Gate 5.23 and is permanently locked.

### OBSERVATIONS
1. If we author new queries only targeting the same 8 documents (`DOC-NHS-004` to `DOC-NHS-011`), the evaluation will test *intra-document query paraphrasing and section discrimination*, but **will not test whether the system generalizes to unseen clinical domains** (e.g. cardiovascular, neurological, infection, or trauma conditions not currently in the index).
2. Early documents `DOC-NHS-001` (Heat exhaustion/heatstroke), `DOC-NHS-002` (Paracetamol), and `DOC-NHS-003` (Child choking) were parsed in Gate 4c but were never integrated into the canonical `HYBRID_600` index used in Gates 5.8–5.24.

### RECOMMENDATIONS
1. **Do NOT reuse the 8 existing documents alone for final holdout claims**: To achieve true clinical generalizability, the holdout must evaluate topics outside the 8 familiar documents.
2. **Execute Ingestion Expansion (Gate 5.26)**:
   - Ingest 4 to 8 new clinical NHS condition documents (e.g., Chest pain / Heart attack, Stroke, Sepsis, Meningitis, Nosebleeds, Allergic rhinitis, Head injury).
   - Ingest using the established provenance and hybrid chunking pipeline.
3. **Construct Locked Independent Generalization Benchmark (Gate 5.27)**:
   - Author a pristine, locked multi-lingual benchmark across both the expanded unseen documents and existing corpus.
   - Lock with SHA-256 hash.
4. **Single-Shot Locked Holdout Evaluation (Gate 5.28)**:
   - Execute Strategy 5 exactly once on the pristine holdout.

---

## 6. Final Status & Conclusion

$$\mathbf{NO\_UNTOUCHED\_HOLDOUT\_EXISTS\_EXPANDED\_INGESTION\_AND\_BENCHMARK\_REQUIRED}$$

- **Strategy 5 Status:** Frozen development candidate (unvalidated on holdout).
- **Holdout Status:** 0 untouched datasets available; new corpus ingestion and benchmark construction required before single-shot validation can proceed.
- **Model Execution:** Enforced (0 model inference calls executed during Gate 5.25).
