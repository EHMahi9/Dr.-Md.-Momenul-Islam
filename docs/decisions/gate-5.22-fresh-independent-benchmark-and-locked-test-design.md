# Decision Record: Gate 5.22 — Fresh Independent Benchmark Construction & Locked Generalization Test Design

**Gate Reference:** GATE 5.22  
**Date:** 2026-08-28  
**Status:** `FRESH_BENCHMARK_LOCKED`  
**Classification:** BENCHMARK INTEGRITY & EXPERIMENTAL DESIGN COMPLETE  

---

## 1. Executive Summary & Rationale

Across Gates 5.11, 5.13, 5.15, and 5.20, the original 40-query test set (`TEST-DIA`, `TEST-HEA`, `TEST-FEV`, `TEST-ANA`) was evaluated **four separate times**. Repeated exposure rendered that holdout compromised for any further unbiased generalization testing.

Furthermore, empirical audit of the previous test annotations revealed a critical methodological vulnerability:
- **14 out of 40 (35.0%)** test queries were annotated with `HYB-000` (overview chunk) as their gold target.
- The 0.85x overview debiasing strategy (introduced in Gate 5.14) directly penalized overview chunks, creating an artificial tension between debiasing and holdout retrieval.

**Gate 5.22 resolves this by constructing a completely fresh, uncompromised, and strictly verified 50-query independent benchmark spanning all 8 corpus documents.**

---

## 2. Benchmark Artifacts & Integrity Hashes

- **Frozen Candidate Configuration (unchanged from Gate 5.21):**  
  SHA-256: `07f031da533d47666fb5abd242f8db47b90dc584a92c0b3f399abaaf51c02736`
- **Fresh Locked Benchmark:**  
  Path: [`research/gate_5_22_fresh_benchmark/benchmark/fresh_locked_benchmark.json`](../../research/gate_5_22_fresh_benchmark/benchmark/fresh_locked_benchmark.json)  
  SHA-256: `a0267355615d9094fd9698ff0bbb5d9aa69311a9c822e1cd47ac12fc08573ef6`
- **Corpus Independence Report:**  
  Path: [`research/gate_5_22_fresh_benchmark/corpus_audit/corpus_independence_report.json`](../../research/gate_5_22_fresh_benchmark/corpus_audit/corpus_independence_report.json)
- **Integrity Report:**  
  Path: [`research/gate_5_22_fresh_benchmark/integrity/benchmark_integrity_report.json`](../../research/gate_5_22_fresh_benchmark/integrity/benchmark_integrity_report.json)

---

## 3. Structural Analysis & Verification Metrics

| Criterion | Specification / Target | Audit Result | Status |
|---|---|---|---|
| Total Queries | 50 queries | 50 queries | ✅ PASS |
| Supported Queries | 40 queries across 8 documents | 40 queries (5/doc) | ✅ PASS |
| Hard Negatives | 5 queries | 5 queries | ✅ PASS |
| Out-of-Corpus | 5 queries | 5 queries | ✅ PASS |
| Language Diversity | 4 classes (EN, BN, Std Banglish, Abbrev Banglish) | 21 EN, 10 BN, 10 Std, 9 Abbrev | ✅ PASS |
| Duplicate / Overlap Check | 0 overlap with existing 80 DEV/TEST queries | 0 overlap | ✅ PASS |
| Gold Chunk Existence | 100% in HYBRID_600 corpus (68 chunks) | 100% verified | ✅ PASS |
| Overview-Only Gold Count | 0 queries mapped solely to `HYB-000` | **0 / 40 (0.0%)** | ✅ PASS |
| Unique Gold Chunks Targeted | Maximize corpus representation | **34 / 68 chunks (50.0%)** | ✅ PASS |
| Untested Chunks Covered | Target previously un-evaluated sections | **19 new chunks** | ✅ PASS |
| Average Gold Chunk Depth | Deep section targeting | **4.55 chunk index** | ✅ PASS |

---

## 4. Intent & Topic Distribution

### Supported Intents:
- **Emergency Escalation (999 / A&E)**: 6 queries
- **Home Treatment & Post-First-Aid**: 5 queries
- **Factoid / Measurement / Duration**: 5 queries
- **Contraindications ("Don't" rules)**: 5 queries
- **Professional Referral (GP / 111 / Pharmacy)**: 5 queries
- **Prevention & Lifestyle Habits**: 5 queries
- **Medication & Treatment Modalities**: 4 queries
- **Causal / Etiology Inquiries**: 2 queries
- **Life-Stage Specific (Infant, Elderly, Pregnancy)**: 3 queries

---

## 5. Pre-Registered Evaluation Protocol (Gate 5.23)

1. **Frozen Candidate Immobility**: Must use exact frozen config `07f031da533d47666fb5abd242f8db47b90dc584a92c0b3f399abaaf51c02736`.
2. **Single Evaluation Only**: The fresh benchmark shall be evaluated exactly once. No post-hoc tuning or re-running on this benchmark is permitted.
3. **Primary Success Metric**: `Final Chunk Recall@5`.
4. **Secondary Metrics**: `Final Chunk Recall@1`, `Final Chunk Recall@3`, `Final Chunk MRR`, `Dense Candidate Recall@15`.
5. **Language-Stratified Analysis**: Performance must be reported per language class.
6. **Guardrail Metric**: Reranker top-1 score logging for unsupported queries (recording empirical max without asserting unvalidated thresholds).

---

## 6. Sign-off

- **Gate Status:** `FRESH_BENCHMARK_LOCKED`
- **Execution Command Prohibition in Gate 5.22:** Enforced (0 model inference calls executed).
- **Ready for Gate 5.23 (Fresh Locked Holdout Evaluation):** YES.
