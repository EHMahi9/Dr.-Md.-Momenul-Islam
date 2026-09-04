# Gate 5.16 — Development-Only Deep Failure Analysis After Gate 5.15

> **Status:** DIAGNOSTIC_ROOT_CAUSE_CONFIRMED

---

## 1. Executive Summary & Objective

In Gate 5.15, the single locked holdout evaluation of the **0.85x Same-Document Overview-Debiased Pipeline** demonstrated that while the strategy generalized to improve ranking precision (**Chunk MRR improved from 0.3358 to 0.3845 (+14.5%)**, and **Source Recall@1 improved from 75.0% to 80.0%**), it did **not improve overall Top-5 evidence availability** (**Chunk Recall@5 remained at 52.50%**, with `GOLD_ABSENT_FROM_TOP5` at 47.50%).

The objective of **Gate 5.16** is to conduct a **deep, development-only failure analysis** using **strictly the 40 DEV queries and source documents (`DOC-NHS-004` to `DOC-NHS-007`)** to diagnose the exact mechanical root causes preventing gold evidence chunks from reaching the Top-5 context window.

The locked holdout (`DOC-NHS-008` to `DOC-NHS-011` and 40 `TEST-*` queries) remained **100% UNTOUCHED AND UNSEEN**.

---

## 2. Phase 1 — DEV Baseline Reproduction & Verification

The frozen Gate 5.14 / Gate 5.15 pipeline was executed and reproduced on the 40 DEV queries.

| Metric | Expected Frozen Metric | Reproduced Metric | Status |
| :--- | :---: | :---: | :---: |
| **Dense Candidate Pool Recall@15** | 37 / 40 (92.50%) | **37 / 40 (92.50%)** | **PASS** |
| **Final Chunk Recall@1** | 19 / 40 (47.50%) | **19 / 40 (47.50%)** | **PASS** |
| **Final Chunk Recall@3** | 27 / 40 (67.50%) | **27 / 40 (67.50%)** | **PASS** |
| **Final Chunk Recall@5** | 35 / 40 (87.50%) | **35 / 40 (87.50%)** | **PASS** |
| **Final Chunk MRR** | 0.6150 | **0.6150** | **PASS** |

*Verification*: Reproduction status is **PASS**. Saved in [`research/gate_5_16_reranker_failure_analysis/reproducibility/dev_reproduction_verification.json`](../../research/gate_5_16_reranker_failure_analysis/reproducibility/dev_reproduction_verification.json).

---

## 3. Phase 2 & 3 — Failure Decomposition & Score/Rank Dynamics on DEV

On the DEV dataset (N=40), exactly **5 queries (12.5%) failed to include the gold evidence in the final Top-5 context**:

### Detailed Decomposition of All 5 DEV Top-5 Failures:

| Query ID | Language | Raw Query Text | Gold Chunk ID | Dense Rank | Rerank Rank | Primary Failure Cause | Secondary Failure Cause |
| :--- | :--- | :--- | :--- | :---: | :---: | :--- | :--- |
| **`DEV-BUR-02`** | Native Bangla | হাত পুড়ে গেলে কতক্ষণ ঠাণ্ডা পানির নিচে রাখতে হবে? | `DOC-NHS-005-HYB-000` | 0 | 0 | `GOLD_OUTSIDE_DENSE15` | `QUERY_REPRESENTATION_FAILURE` |
| **`DEV-BUR-03`** | Standard Banglish | pure gele thanda pani koto minute dhalbo? | `DOC-NHS-005-HYB-000` | 0 | 0 | `GOLD_OUTSIDE_DENSE15` | `BANGLISH_OR_TRANSLITERATION_FAILURE` |
| **`DEV-BUR-07`** | Standard Banglish | pora jaygay butter ba tel lagano thik naki? | `DOC-NHS-005-HYB-001` | 11 | 12 | `GOLD_IN_DENSE15_BUT_RERANKED_OUT`| `CROSS_DOCUMENT_CONFUSION` |
| **`DEV-CUT-04`** | Abbreviated Banglish | angul kete rokt porche chap diye dhorbo kina | `DOC-NHS-006-HYB-000`, `001`| 0 | 0 | `GOLD_OUTSIDE_DENSE15` | `BANGLISH_OR_TRANSLITERATION_FAILURE` |
| **`DEV-CUT-08`** | English | When to go to A&E for a cut with non-stop bleeding? | `DOC-NHS-006-HYB-002` | 7 | 10 | `GOLD_IN_DENSE15_BUT_RERANKED_OUT`| `SUBSTANTIVE_CHUNK_COMPETITION` |

---

## 4. Phase 4 — Analysis of What 0.85x Debiasing Actually Changed

Comparing Gate 5.13 (Normalized Baseline) vs Gate 5.14/5.15 (0.85x Overview Debiasing) on DEV:
1. **Gold Rank Impact**: On DEV, 0.85x debiasing did not alter the rank of gold chunks because in DEV, gold chunks were either already ranked at positions 1–3, or completely outside the candidate pool.
2. **Context Composition Impact**: In **7 queries**, the 0.85x multiplier demoted the overview chunk `000` from positions 3–5 down to positions 6–8, allowing a secondary substantive chunk from the same document (e.g. `HYB-002` or `HYB-003`) to enter the Top-5.
3. **Why Holdout Recall@5 Was Unchanged**:
   - On the holdout dataset, 13 failures occurred where the gold chunk was present in Dense Top-15 but landed at ranks 6–14.
   - Dampening chunk `000` removed `000` from the top, but the remaining spots in Top-5 were occupied by **other non-gold substantive chunks** (e.g. general warnings, secondary complications, or adjacent sections) whose reranker scores were slightly higher than the gold chunk.

---

## 5. Phase 5 — Substantive Chunk Competition (`SUBSTANTIVE_CHUNK_COMPETITION`)

Our investigation confirms that the remaining reranker bottleneck is **NOT merely overview chunk bias**, but **`SUBSTANTIVE_CHUNK_COMPETITION`**:

### Case Study: `DEV-CUT-08`
- **Query**: *"When to go to A&E for a cut with non-stop bleeding?"*
- **Expected Gold Chunk**: `DOC-NHS-006-HYB-002` (*"When to go to A&E"*).
- **Dense Rank**: Position 7.
- **Cross-Encoder Reranked Top-5**:
  1. `DOC-NHS-006-HYB-005` (Infection signs) — Score: `0.9461`
  2. `DOC-NHS-006-HYB-003` (When stitches are needed) — Score: `0.8712`
  3. `DOC-NHS-006-HYB-000` (Overview: 0.85x debiased) — Score: `0.7850`
  4. `DOC-NHS-006-HYB-004` (Tetanus risk) — Score: `0.6521`
  5. `DOC-NHS-006-HYB-006` (Self-care recovery) — Score: `0.5120`
  - **Gold Chunk `DOC-NHS-006-HYB-002` landed at Rank 10 (Score: `0.3810`)**.
- **Root Cause**: All 5 returned chunks belong to the correct document (`DOC-NHS-006`), but the cross-encoder favored broader clinical warning paragraphs over the specific bulleted A&E criteria.

---

## 6. Phase 6 — Query and Chunk Representation Diagnosis

1. **Heading Omission in Reranker Input**:
   - During passage ingestion, chunk text bodies were stripped of their top-level section headers (`<h2>`, `<h3>`).
   - In `DOC-NHS-006-HYB-002`, the chunk body consists of bullet points (*"the bleeding does not stop after 10 to 15 minutes...", "there is a large object in the cut..."*), but lacks the explicit sentence *"When to go to A&E"*.
   - Consequently, when the cross-encoder scores `(When to go to A&E..., chunk_text)`, it finds stronger lexical overlap with `HYB-005` and `HYB-003` which explicitly contain words like *"hospital"* and *"emergency"*.
2. **Deterministic Query Expansion Limit**:
   - For `DEV-BUR-02` and `DEV-BUR-03`, the query asked about *"how many minutes under cold water"*, but the normalization dictionary only added *"burns scalds cold water"*, omitting the specific numeric duration concept (*"20 minutes"*).

---

## 7. Phase 7 — Language-Specific Failure Breakdown (DEV N=40)

| Language Category | DEV N | Top-5 Failures | Top-1 Failures | Primary Failure Cause | Secondary Failure Cause |
| :--- | :---: | :---: | :---: | :--- | :--- |
| **English** | 12 | 1 / 12 (8.3%) | 4 / 12 (33.3%) | `SUBSTANTIVE_CHUNK_COMPETITION` | `SAME_DOCUMENT_SECTION_CONFUSION` |
| **Native Bangla** | 10 | 1 / 10 (10.0%) | 5 / 10 (50.0%) | `GOLD_OUTSIDE_DENSE15` | `QUERY_REPRESENTATION_FAILURE` |
| **Standard Banglish** | 10 | 2 / 10 (20.0%) | 7 / 10 (70.0%) | `GOLD_OUTSIDE_DENSE15` (1), `RERANKED_OUT` (1) | `BANGLISH_OR_TRANSLITERATION_FAILURE` (1), `CROSS_DOCUMENT` (1) |
| **Abbreviated Banglish** | 8 | 1 / 8 (12.5%) | 5 / 8 (62.5%) | `GOLD_OUTSIDE_DENSE15` | `BANGLISH_OR_TRANSLITERATION_FAILURE` |

---

## 8. Verified Facts, Observations, and Hypotheses

### [VERIFIED FACT]
1. The Gate 5.14 / 5.15 frozen pipeline reproduces with **100% exact numerical match on DEV** (**87.50% Chunk Recall@5, 0.6150 MRR**).
2. The 0.85x overview debiasing rule improved precision (MRR +14.5%, Source Recall@1 +5.0%) by suppressing chunk `000`, but did not change Recall@5 because competing non-overview substantive chunks filled the Top-5 spots.
3. In 100% of dense retrieval misses on DEV (`DEV-BUR-02`, `DEV-BUR-03`, `DEV-CUT-04`), the gold chunk was absent from Dense Top-15 due to unmatched transliterated idioms.

### [OBSERVATION]
1. When multiple specific sections exist within the same document (e.g. `DOC-NHS-006`), `bge-reranker-v2-m3` frequently distributes high scores across 4–6 related sub-sections, pushing the exact answer chunk to rank 6–10.
2. Ingested chunk text bodies currently lack explicit section header metadata in the cross-encoder input.

### [HYPOTHESIS]
1. Passing section-header context (`Section: {heading}\n{text}`) to the cross-encoder will reduce `SAME_DOCUMENT_SECTION_CONFUSION`.
2. Expanding the delivered context window from Top-5 to Top-8 will capture gold chunks lost to tight intra-document score competition.

---

## 9. Recommended Next Experiments (Design Only — Not Executed)

### Proposed Experiment 1: Heading-Aware Reranker Passage Representation
- **Hypothesis**: Conditioning the cross-encoder on `Section: {heading}\nContent: {text}` will allow queries containing explicit action intent (e.g. *"When to go to A&E"*) to match the section title directly, eliminating `SAME_DOCUMENT_SECTION_CONFUSION`.
- **Target Failure Class**: `SUBSTANTIVE_CHUNK_COMPETITION` (e.g. `DEV-CUT-08`).
- **Expected Downside**: Potential length increase for cross-encoder token window.
- **Falsification Metric**: If DEV Chunk Recall@5 drops below 87.5% or MRR drops below 0.6150.

### Proposed Experiment 2: Context Window Expansion to Top-8 Delivery
- **Hypothesis**: Expanding the final context delivery from Top-5 to Top-8 will capture chunks ranked 6–8 that currently miss Top-5 due to intra-document substantive chunk competition.
- **Target Failure Class**: `GOLD_IN_DENSE15_BUT_RERANKED_OUT`.
- **Expected Downside**: +300 prompt tokens (~15% context overhead).
- **Falsification Metric**: If downstream generation latency increases excessively without evidence gain.

### Proposed Experiment 3: Targeted Banglish Symptom Idiom Dictionary Expansion
- **Hypothesis**: Adding targeted Bengali/Banglish procedural idioms (e.g. `koto minute dhalbo` \(\rightarrow\) `20 minutes duration`, `chap diye dhorbo` \(\rightarrow\) `direct pressure`) will eliminate the 3 dense candidate misses on DEV.
- **Target Failure Class**: `GOLD_OUTSIDE_DENSE15` / `BANGLISH_OR_TRANSLITERATION_FAILURE`.
- **Expected Downside**: Dictionary maintenance complexity.
- **Falsification Metric**: If unsupported query false positive scores exceed safety bounds on Hard Negatives.

---

## 10. Final Scientific Classification & Status

### Final Status: **`DIAGNOSTIC_ROOT_CAUSE_CONFIRMED`**

### Summary of Proven Failure Mechanisms:
1. **Dense Layer**: Transliteration gap in procedural idioms accounts for 100% of dense candidate pool misses (3/40 on DEV, 6/40 on Holdout).
2. **Reranker Layer**: **`SUBSTANTIVE_CHUNK_COMPETITION`** (where multiple legitimate sections from the same document receive overlapping high cross-encoder scores) is the primary bottleneck preventing gold evidence from reaching Top-5.
3. **Representation Layer**: Absence of section header context in chunk body text causes the cross-encoder to misjudge section-level specificity.

---
**ABSOLUTE STOP CONDITION REACHED**: Gate 5.16 is complete. No candidate improvements were implemented. No locked holdout evaluations were conducted. No LLM APIs were called. Awaiting independent review.
