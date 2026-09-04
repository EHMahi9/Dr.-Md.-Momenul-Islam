# Gate 5.19 — Development-Only Dual Failure Mitigation Study

> **Final Status:** `DUAL_MITIGATION_CANDIDATE_SELECTED`
> **Frozen Candidate Configuration SHA-256:** `5a6840ff9a4d1956a913ab85f3972c4d7481c01bfe0c7a8fe7b2d9110017621e`

---

## 1. Executive Summary & Objective

In **Gate 5.16–5.18**, systematic failure decomposition and diagnostic experiments identified two primary bottlenecks on the Development set (`DOC-NHS-004` to `DOC-NHS-007`):
1. **Track A (Dense Retrieval Misses due to Transliteration / Unicode Boundary Gaps)**: 3/5 DEV Top-5 failures (`DEV-BUR-02`, `DEV-BUR-03`, `DEV-CUT-04`) were caused by brittle word-boundary matching (`\b`) on Unicode Bengali script and overly rigid phrase-level patterns (e.g. `pure geche` vs `pure gele`, `kete geche` vs `kete`, `rokto` vs `rokt`).
2. **Track B (Substantive Same-Document Section Competition)**: 2/5 DEV Top-5 failures (`DEV-CUT-08`, `DEV-BUR-07`) were caused by adjacent sections within the same document scoring above specific factual guidance chunks.

The objective of **Gate 5.19** was to conduct a **controlled, development-only failure mitigation study** evaluating targeted procedural normalization improvements, dense-reranker score fusion, and overview debiasing adjustments on the 40 Development queries.

The locked holdout split (`DOC-NHS-008` to `DOC-NHS-011` and 40 `TEST-*` queries) remained **100% UNTOUCHED AND UNSEEN**.

---

## 2. Phase 1 — DEV Baseline Reproduction

The Gate 5.14 / Gate 5.15 baseline was reproduced with exact numerical match on the 40 DEV queries:

| Metric | Target Frozen Baseline | Reproduced Actual | Status |
| :--- | :---: | :---: | :---: |
| **Dense Candidate Pool Recall@15** | 37 / 40 (92.50%) | **37 / 40 (92.50%)** | **PASS** |
| **Final Chunk Recall@1** | 19 / 40 (47.50%) | **19 / 40 (47.50%)** | **PASS** |
| **Final Chunk Recall@3** | 27 / 40 (67.50%) | **27 / 40 (67.50%)** | **PASS** |
| **Final Chunk Recall@5** | 35 / 40 (87.50%) | **35 / 40 (87.50%)** | **PASS** |
| **Final Chunk MRR** | 0.6150 | **0.6150** | **PASS** |

---

## 3. Phase 2 — Track A: Diagnosis of Dense Transliteration & Unicode Regex Failures

Diagnostic inspection revealed the exact mechanical reasons for the 3 Dense misses on DEV:
1. **Python Regex `\b` Boundary Limitation on Unicode Bengali**:
   - In Python `re`, `\b` fails around Bengali Unicode script (e.g. `\bপুড়ে\b` fails on `হাত পুড়ে গেলে...`) because non-ASCII characters are treated as non-word characters, making the boundary check evaluate to `False`.
2. **Brittle Multi-word Phrase Matching**:
   - `DEV-BUR-03` (`pure gele thanda pani koto minute dhalbo?`): The baseline dictionary required `pure geche`, so `pure gele` received zero expansion.
   - `DEV-CUT-04` (`angul kete rokt porche chap diye dhorbo kina`): The baseline dictionary required `kete geche` and `rokto`, so `kete` and `rokt` received zero expansion.
   - `DEV-BUR-07` (`pora jaygay butter ba tel lagano thik naki?`): The baseline dictionary had `pura`, missing standard transliteration `pora`.

### Mitigation: Unicode-Aware Procedural Normalization
We implemented Unicode-safe boundary matching `(?:\b|(?<=^)|(?<=\s))` combined with root-token expansions for procedural medical terms (burns, scalds, cuts, bleeding, dehydration, asthma, diarrhoea, painkillers).

**Result on Dense Retrieval**:
- Dense Candidate Pool Recall@15 on DEV reached **40 / 40 (100.00%)** (up from 37/40 = 92.50%).

---

## 4. Phase 3 & 4 — Controlled Multi-Strategy Comparison (DEV N=40)

Four controlled strategies were evaluated across the 40 DEV queries:

| Strategy | Strategy Description | Dense Recall@15 | Final Chunk Recall@1 | Final Chunk Recall@3 | Final Chunk Recall@5 (PRIMARY) | Final Chunk MRR |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **Strategy 1 (Control Baseline)** | Gate 5.14 baseline normalization + 0.85x debias | 37 / 40 (92.5%) | 19 / 40 (47.5%) | 27 / 40 (67.5%) | 35 / 40 (87.5%) | 0.6150 |
| **Strategy 2 (Track A: Robust Normalization)** | **Unicode-aware procedural norm + 0.85x debias** | **40 / 40 (100.0%)** | **22 / 40 (55.0%)** | **31 / 40 (77.5%)** | **39 / 40 (97.5%)** | **0.6908** |
| **Strategy 3 (Track A + Dense Fusion)** | Track A + (0.85x debias + 0.10x dense score) | 40 / 40 (100.0%) | 22 / 40 (55.0%) | 31 / 40 (77.5%) | 37 / 40 (92.5%) | 0.6822 |
| **Strategy 4 (Track A + 0.75x Debiasing)** | Track A + 0.75x overview debias | 40 / 40 (100.0%) | 22 / 40 (55.0%) | 31 / 40 (77.5%) | 39 / 40 (97.5%) | 0.6850 |

### Winning Candidate: **Strategy 2**
- **Primary Metric (Chunk Recall@5)**: **39 / 40 (97.50%)** (+10.00% absolute gain vs baseline).
- **Secondary Metric (Chunk MRR)**: **0.6908** (+12.3% relative gain vs baseline).
- **Secondary Metric (Chunk Recall@1)**: **22 / 40 (55.00%)** (+7.50% gain).
- **Secondary Metric (Chunk Recall@3)**: **31 / 40 (77.50%)** (+10.00% gain).

---

## 5. Phase 5 — Language Breakdown for Winning Strategy 2 (DEV N=40)

| Language Category | DEV N | Dense Recall@15 | Final Chunk Recall@1 | Final Chunk Recall@3 | Final Chunk Recall@5 | Final Chunk MRR | DEV Evidence Availability |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **English** | 12 | 12 / 12 (100.0%) | 8 / 12 (66.67%) | 10 / 12 (83.33%) | 11 / 12 (91.67%) | 0.7611 | 91.67% |
| **Native Bangla** | 10 | 10 / 10 (100.0%) | 6 / 10 (60.00%) | 8 / 10 (80.00%) | **10 / 10 (100.0%)** | **0.7067** | **100.00%** |
| **Standard Banglish** | 10 | 10 / 10 (100.0%) | 5 / 10 (50.00%) | 7 / 10 (70.00%) | **10 / 10 (100.0%)** | **0.6650** | **100.00%** |
| **Abbreviated Banglish** | 8 | 8 / 8 (100.0%) | 3 / 8 (37.50%) | 6 / 8 (75.00%) | **8 / 8 (100.0%)** | **0.5979** | **100.00%** |
| **All Non-English (Combined)** | **28** | **28 / 28 (100.0%)** | **14 / 28 (50.00%)** | **21 / 28 (75.00%)** | **28 / 28 (100.0%)** | **0.6607** | **100.00%** |

Across all **28 non-English queries on DEV**, evidence availability reached **100.00% (28/28)**.

---

## 6. Phase 6 — Unsupported Query Safety Evaluation (N=20)

Safety was verified on the 20 Unsupported queries (12 Hard Negatives + 8 Out-of-Corpus):
- **Maximum Cross-Encoder Reranker Score**: **0.5035** (comfortably below the 0.60 safety rejection boundary).
- **Mean Maximum Score**: **0.1023**.
- **Safety Rejection Boundary**: **100% PRESERVED**.

---

## 7. Remaining Failure Analysis on DEV (1 / 40 Queries)

With Strategy 2, exactly **1 query out of 40** remains outside Top-5 on DEV:
- **`DEV-CUT-08` (English)**: *"When to go to A&E for a cut with non-stop bleeding?"*
  - Expected Gold: `DOC-NHS-006-HYB-002` ("What to do if the wound is bleeding a lot").
  - Result: Gold chunk entered Dense Top-15 at Rank 7, but was ranked at Rank 10 by the cross-encoder because `DOC-NHS-006-HYB-005` contains explicit `Call 999 or go to A&E if: you have a cut and cannot stop the bleeding` and received Rank 1 score (`0.9461`).

---

## 8. Frozen Candidate Architecture & Checksum

```
User Query
    ↓
Deterministic Unicode-Aware Procedural Normalization
    ↓
multilingual-e5-small Dense Retrieval (K=15)
    ↓
BAAI/bge-reranker-v2-m3 Cross-Encoder (raw chunk text)
    ↓
0.85x Same-Document Overview Debiasing (on -HYB-000)
    ↓
Top-5 Delivered Evidence Context
```

- **Configuration File**: [`research/gate_5_19_dual_failure_mitigation/candidate/frozen_candidate_configuration.json`](../../research/gate_5_19_dual_failure_mitigation/candidate/frozen_candidate_configuration.json)
- **Configuration SHA-256 Checksum**: `5a6840ff9a4d1956a913ab85f3972c4d7481c01bfe0c7a8fe7b2d9110017621e`

---

## 9. Final Decision & Status

### Final Status: **`DUAL_MITIGATION_CANDIDATE_SELECTED`**

Strategy 2 decisively resolves the primary candidate starvation failure mode on DEV while improving all precision and availability metrics without compromising unsupported safety.

---
**ABSOLUTE STOP CONDITION REACHED**: Gate 5.19 is complete. The locked holdout remained 100% untouched. No production code was modified. No LLM APIs were called. Awaiting independent review before any single holdout validation gate.
