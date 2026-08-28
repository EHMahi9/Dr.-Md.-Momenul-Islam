# Decision Record: Gate 5.28 — Independent Multilingual Benchmark Construction on Newly Ingested NHS Sources

**Gate Reference:** GATE 5.28  
**Date:** 2026-08-29  
**Status:** `BENCHMARK_LOCKED`  
**Classification:** PRISTINE HOLDOUT BENCHMARK CONSTRUCTED & LOCKED — RETRIEVAL MODEL NOT EXECUTED  

---

## 1. Executive Summary & Objective

Gate 5.28 constructed and frozen a pristine, independent multilingual benchmark targeting the **6 newly ingested NHS documents** (`DOC-NHS-012` through `DOC-NHS-017`) from Gate 5.27.

> [!IMPORTANT]
> **Strict Research Separation & Zero Model Execution:**
> This benchmark was constructed purely from clinical source content without invoking any dense embedding, cross-encoder, LLM, or retrieval components. The benchmark is frozen and locked with SHA-256 digest for single-shot validation in Gate 5.29.

---

## 2. Locked Benchmark Identity

- **Benchmark File:** `research/gate_5_28_independent_benchmark/benchmark/new_locked_benchmark.json`
- **Locked SHA-256 Digest:**
  `464612e733aeb1496c1dcdc5674e01d9504bd4ccd1244190e487c6e957dcc722`
- **Lock Status:** `LOCKED_FOR_SINGLE_SHOT_EVALUATION`

---

## 3. Query Taxonomy & Language Slices

| Query Category | English | Native Bangla | Standard Banglish | Abbreviated Banglish | Total |
|---|---|---|---|---|---|
| **Supported Queries** | 10 | 10 | 10 | 10 | **40** |
| **Hard Negatives** | 2 | 1 | 1 | 1 | **5** |
| **Out-of-Corpus (OOC)** | 2 | 1 | 1 | 1 | **5** |
| **TOTAL** | **14** | **12** | **12** | **12** | **50** |

### Target Source Coverage (Supported Queries):
- `DOC-NHS-012` (Chest pain): 6 queries
- `DOC-NHS-013` (Stroke - Symptoms): 6 queries
- `DOC-NHS-014` (Sepsis): 7 queries
- `DOC-NHS-015` (Meningitis): 8 queries
- `DOC-NHS-016` (Nosebleed): 7 queries
- `DOC-NHS-017` (Allergic rhinitis): 6 queries

---

## 4. Integrity & Deduplication Audit

1. **Gold Chunk Validity:**
   - 100% of gold chunk IDs (65 total reference citations) were verified directly against `research/gate_5_27_ingestion/provenance_manifest.json`.
   - Zero orphan chunk references.
2. **Historical Deduplication Audit:**
   - All 50 queries were compared against the historical query inventory (Gate 4C, Gate 5.3, Gate 5.8, Gate 5.22, Gate 5.23, Gate 5.24 DEV-24).
   - **Verdict:** `ZERO_DUPLICATES` (0 exact or semantic near-duplicate matches).
3. **Model Non-Contamination:**
   - 0 embeddings generated, 0 reranking calls, 0 LLM inferences.

---

## 5. Final Status & Next Steps

$$\mathbf{BENCHMARK\_LOCKED}$$

**Recommendation for Gate 5.29:**  
Execute a single-shot frozen validation of `STRATEGY_5_DUAL_TOPICAL_LEXICAL_ANCHOR` against this locked benchmark (`SHA-256: 464612e7...`) over the expanded corpus.
