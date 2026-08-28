# Benchmark Specification: Gate 5.28 Independent Multi-Lingual Benchmark

**Locked Benchmark SHA-256:** `464612e733aeb1496c1dcdc5674e01d9504bd4ccd1244190e487c6e957dcc722`  
**Date Created:** 2026-08-29  
**Status:** `LOCKED_FOR_SINGLE_SHOT_EVALUATION`  

---

## 1. Distribution & Scope

- **Total Queries:** 50
- **Supported Queries:** 40 (10 English, 10 Native Bangla, 10 Standard Banglish, 10 Abbreviated Banglish)
- **Hard Negatives:** 5
- **Out-of-Corpus:** 5

### Target Source Distribution (Supported Queries):
- `DOC-NHS-012` (Chest pain): 6 queries
- `DOC-NHS-013` (Stroke): 6 queries
- `DOC-NHS-014` (Sepsis): 7 queries
- `DOC-NHS-015` (Meningitis): 8 queries
- `DOC-NHS-016` (Nosebleed): 7 queries
- `DOC-NHS-017` (Allergic rhinitis): 6 queries

---

## 2. Integrity Assurances

1. **Zero Contamination**: 0 historical queries reused across all prior gates.
2. **Strict Gold Mapping**: Every gold chunk ID is verified in `research/gate_5_27_ingestion/provenance_manifest.json`.
3. **No Model Execution**: No embeddings, retrieval, or reranking executed during construction.
