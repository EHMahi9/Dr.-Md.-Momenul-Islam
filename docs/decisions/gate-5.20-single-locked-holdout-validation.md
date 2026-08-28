# Gate 5.20 — Single Locked Holdout Validation of the Frozen Dual-Mitigation Retrieval Pipeline

> **Final Status:** `RETRIEVAL_DUAL_MITIGATION_PARTIALLY_GENERALIZES`
> **Frozen Configuration SHA-256:** `5a6840ff9a4d1956a913ab85f3972c4d7481c01bfe0c7a8fe7b2d9110017621e`

---

## 1. Executive Summary & Objective

In **Gate 5.19**, a dual-mitigation retrieval pipeline was developed and frozen using strictly the 40 Development queries (`DOC-NHS-004` to `DOC-NHS-007`). On the DEV set, this configuration achieved **40/40 (100%) Dense Candidate Recall@15**, **39/40 (97.5%) Final Chunk Recall@5**, and an **MRR of 0.6908**, with 100% Top-5 evidence availability across all 28 non-English queries.

The objective of **Gate 5.20** was to execute a **single, locked, un-tuned holdout validation** of this exact frozen configuration on the untouched holdout corpus (`DOC-NHS-008` to `DOC-NHS-011`), 40 supported `TEST-*` queries, and 20 unsupported queries (12 Hard Negatives + 8 Out-of-Corpus).

---

## 2. Phase 1 — Cryptographic Integrity Verification: PASS

Prior to executing any retrieval or inference, all cryptographic checksums were verified against the frozen benchmark artifacts:

| Artifact | Verified Checksum (SHA-256) | Status |
| :--- | :--- | :---: |
| **Frozen Configuration** | `5a6840ff9a4d1956a913ab85f3972c4d7481c01bfe0c7a8fe7b2d9110017621e` | **PASS** |
| **Locked Benchmark File** | `7debd4b7d804938d4c7ecf8f414f51d936830b5a6d9d62ebfcaedde1874c8a81` | **PASS** |
| **HYBRID_600 Corpus Manifest** | `71dca400059f624042fd5a1cc8be94010ce9553e3bde1428e73ad236ed79da3f` | **PASS** |
| **Chunk Gold Labels** | `df881fa676d38d46c78e6ade1e9e69c0b2cf676b33c6b655981f673f123844ae` | **PASS** |

Integrity report saved to [`research/gate_5_20_locked_holdout_validation/integrity/gate_5_20_integrity_verification.json`](file:///d:/my-ai-project/Dr.%20Md.%20Momenul%20Islam/research/gate_5_20_locked_holdout_validation/integrity/gate_5_20_integrity_verification.json).

---

## 3. Phase 2 & 3 — Single Holdout Run Results (TEST N=40)

The exact frozen pipeline was executed once on the 40 supported holdout queries:

### Primary Evidence Availability Metrics (Holdout N=40):
- **Dense Candidate Pool Recall@15**: **34 / 40 (85.00%)**
- **Final Chunk Recall@1**: **11 / 40 (27.50%)**
- **Final Chunk Recall@3**: **13 / 40 (32.50%)**
- **Final Chunk Recall@5 (PRIMARY)**: **20 / 40 (50.00%)**
- **Final Chunk MRR**: **0.3797**

### Secondary Source-Level Metrics (Holdout N=40):
- **Source Recall@1**: **31 / 40 (77.50%)**
- **Source Recall@5**: **38 / 40 (95.00%)**

### Evidence Availability Categories:
| Category | Count / Total | Percentage | Definition |
| :--- | :---: | :---: | :--- |
| `TOP1_CORRECT` | 11 / 40 | 27.50% | Gold chunk ranked at Rank 1 |
| `TOP1_WRONG_BUT_TOP3_HAS_GOLD` | 2 / 40 | 5.00% | Gold chunk present in Top-3 (Rank 2–3) |
| `TOP3_WRONG_BUT_TOP5_HAS_GOLD` | 7 / 40 | 17.50% | Gold chunk present in Top-5 (Rank 4–5) |
| `GOLD_ABSENT_FROM_TOP5` | **20 / 40** | **50.00%** | Exact gold chunk missing from Top-5 delivered context |

---

## 4. Phase 4 — Dense vs Reranker Failure Decomposition (20 Failures)

Of the 40 holdout queries, exactly 20 queries failed to place their gold evidence chunk in Top-5 context. Every failure was decomposed:

| Failure Taxonomy | Count | % of Failures | Primary Mechanism |
| :--- | :---: | :---: | :--- |
| **`GOLD_OUTSIDE_DENSE15`** | 6 / 20 | 30.0% | Dense model failed to retrieve gold chunk into Top-15 candidate pool. |
| **`GOLD_IN_DENSE15_BUT_RERANKED_OUT`** | **14 / 20** | **70.0%** | Dense model retrieved gold into Top-15, but cross-encoder demoted it below Rank 5. |

### Key Diagnostic Findings on Failures:
1. **Dense Misses (`GOLD_OUTSIDE_DENSE15`, N=6)**:
   - 4 out of 6 dense misses occurred on `TEST-ANA-01` to `TEST-ANA-04` (Anaphylaxis symptoms queries across English, Bangla, and Banglish). The specific symptoms chunk (`DOC-NHS-011-HYB-001`) was ranked at ranks 16–31 by E5 dense retriever.
   - 2 dense misses occurred on abbreviated Banglish fever/headache queries (`TEST-HEA-04`, `TEST-FEV-10`).
2. **Reranker Demotions (`GOLD_IN_DENSE15_BUT_RERANKED_OUT`, N=14)**:
   - In 11 out of 14 cases, the gold chunk was demoted by **intra-document substantive section competition**. For example:
     - For diarrhoea queries (`TEST-DIA-08`, `TEST-DIA-09`, `TEST-DIA-10`), `DOC-NHS-008-HYB-005` (emergency A&E section) scored 0.97+ and outranked `DOC-NHS-008-HYB-003` (bloody vomit warning).
     - For headache queries (`TEST-HEA-05`, `TEST-HEA-07`, `TEST-HEA-08`), `DOC-NHS-009-HYB-003` outranked `DOC-NHS-009-HYB-002`.
     - For fever queries (`TEST-FEV-08`, `TEST-FEV-09`), `DOC-NHS-010-HYB-004` outranked `DOC-NHS-010-HYB-003`.

Diagnostics data saved to [`research/gate_5_20_locked_holdout_validation/diagnostics/gate_5_20_failure_decomposition.json`](file:///d:/my-ai-project/Dr.%20Md.%20Momenul%20Islam/research/gate_5_20_locked_holdout_validation/diagnostics/gate_5_20_failure_decomposition.json).

---

## 5. Phase 5 — Language Breakdown on Holdout (TEST N=40)

| Language Category | N | Dense Recall@15 | Final Chunk Recall@1 | Final Chunk Recall@3 | Final Chunk Recall@5 | Final Chunk MRR |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **English** | 12 | 11 / 12 (91.67%) | 4 / 12 (33.33%) | 5 / 12 (41.67%) | 6 / 12 (50.00%) | 0.4421 |
| **Native Bangla** | 11 | 10 / 11 (90.91%) | 4 / 11 (36.36%) | 4 / 11 (36.36%) | 7 / 11 (63.64%) | 0.4555 |
| **Standard Banglish** | 9 | 8 / 9 (88.89%) | 2 / 9 (22.22%) | 3 / 9 (33.33%) | 5 / 9 (55.56%) | 0.3741 |
| **Abbreviated Banglish** | 8 | 5 / 8 (62.50%) | 1 / 8 (12.50%) | 1 / 8 (12.50%) | 2 / 8 (25.00%) | 0.1884 |
| **Total / Overall** | **40** | **34 / 40 (85.00%)** | **11 / 40 (27.50%)** | **13 / 40 (32.50%)** | **20 / 40 (50.00%)** | **0.3797** |

---

## 6. Phase 6 — Unsupported Query Safety Observations (N=20)

Evaluation on the 20 Unsupported queries (12 Hard Negatives + 8 Out-of-Corpus):
- **Maximum Cross-Encoder Reranker Score**: **0.5035** (`HN-06`)
- **Mean Score**: **0.1023**
- **Minimum Score**: **0.0000**
- **Observed Score Range**: `[0.0000, 0.5035]`

> **Important Boundary Rule**:
> In accordance with safety protocol, 0.60 is **NOT** a clinically validated safety threshold. The observed score separation in this benchmark demonstrates that unsupported queries scored below 0.5035 under this experimental scoring rule. Any production rejection threshold remains **UNKNOWN** pending formal calibration.

---

## 7. Phase 7 — Direct Comparison Across All Locked Holdout Gates

| Metric | Gate 5.11 (Raw HYB-600) | Gate 5.13 (Normalized Baseline) | Gate 5.15 (0.85x Overview Debiased) | Gate 5.20 (Dual Mitigation Pipeline) | Delta (5.20 vs 5.15) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Dense Candidate Recall@15** | 33 / 40 (82.5%) | 34 / 40 (85.0%) | 34 / 40 (85.0%) | **34 / 40 (85.0%)** | 0.0% |
| **Final Chunk Recall@1** | 10 / 40 (25.0%) | 10 / 40 (25.0%) | 11 / 40 (27.5%) | **11 / 40 (27.5%)** | 0.0% |
| **Final Chunk Recall@3** | 13 / 40 (32.5%) | 14 / 40 (35.0%) | 14 / 40 (35.0%) | **13 / 40 (32.5%)** | -2.5% |
| **Final Chunk Recall@5 (PRIMARY)** | 20 / 40 (50.0%) | 21 / 40 (52.5%) | 21 / 40 (52.5%) | **20 / 40 (50.0%)** | **-2.5%** |
| **Final Chunk MRR** | 0.3278 | 0.3358 | 0.3845 | **0.3797** | -0.0048 |
| **Source Recall@1** | 31 / 40 (77.5%) | 31 / 40 (77.5%) | 31 / 40 (77.5%) | **31 / 40 (77.5%)** | 0.0% |
| **Source Recall@5** | 38 / 40 (95.0%) | 38 / 40 (95.0%) | 38 / 40 (95.0%) | **38 / 40 (95.0%)** | 0.0% |
| **GOLD_ABSENT_FROM_TOP5** | 20 / 40 (50.0%) | 19 / 40 (47.5%) | 19 / 40 (47.5%) | **20 / 40 (50.0%)** | +1 query |

---

## 8. Phase 8 — Language Generalization Analysis

- **Standard Banglish Generalization**:
  - DEV Recall@5: 10 / 10 (100.0%)
  - Holdout Recall@5: **5 / 9 (55.56%)** (Dense Recall@15 was 8/9 = 88.89%)
  - *Analysis*: Standard Banglish queries successfully retrieved the correct source document in 8/9 cases, but reranker cross-section competition caused 3 queries to fall to ranks 6–10.
- **Abbreviated Banglish Generalization**:
  - DEV Recall@5: 8 / 8 (100.0%)
  - Holdout Recall@5: **2 / 8 (25.00%)** (Dense Recall@15 was 5/8 = 62.50%)
  - *Analysis*: Abbreviated queries without clear transliterated keywords (e.g. `muk fule geche...`, `bacha ghum theke jagena...`) failed dense retrieval (Rank 20–31), while procedural queries with keywords (e.g. `TEST-DIA-10`, `TEST-HEA-08`) entered Dense Top-15 but were demoted by the reranker.

---

## 9. Final Decision & Classification

### Final Status: **`RETRIEVAL_DUAL_MITIGATION_PARTIALLY_GENERALIZES`**

### Rationale:
1. **Dense Normalization Generalization**: The Unicode-aware procedural normalization maintained a strong source recall on unseen documents (95.0% Source Recall@5, 85.0% Dense Candidate Recall@15), successfully pulling gold documents into the top pool.
2. **Chunk-Level Top-5 Availability Limitation**: However, **Final Chunk Recall@5 remained at 50.0% (20/40)** on the locked holdout. 70% of the failures (14/20) were caused by cross-encoder section competition where adjacent emergency/action sections within the same document outranked specific clinical guidance chunks.
3. **Safety & Integrity**: No production code was modified, no LLMs were invoked, and no clinical safety claims are made.

---
**ABSOLUTE STOP CONDITION REACHED**: Gate 5.20 single locked holdout evaluation is complete. Awaiting independent review.
