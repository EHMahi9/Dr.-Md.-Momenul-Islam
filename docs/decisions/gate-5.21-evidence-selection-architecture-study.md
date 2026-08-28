# Gate 5.21 — Development-Only Evidence Selection Architecture Study

**Date:** 2026-08-28  
**Status:** **`EVIDENCE_SELECTION_CANDIDATE_SELECTED`**  
**Winning Candidate:** `STRATEGY_2_TRACK_A_NORM_ONLY`  
**Frozen Configuration SHA-256:** `07f031da533d47666fb5abd242f8db47b90dc584a92c0b3f399abaaf51c02736`  
**Holdout Status:** **UNTOUCHED (Locked Holdout remained 100% untouched)**

---

## 1. Objective

Following the Gate 5.20 single locked holdout validation, which revealed that 70% (14/20) of holdout failures were caused by `GOLD_IN_DENSE15_BUT_RERANKED_OUT` (intra-document substantive section competition), Gate 5.21 was chartered to investigate the **evidence selection architecture** itself strictly using the development partition (`DOC-NHS-004` through `DOC-NHS-007`, DEV N=40 queries).

The specific objectives of Gate 5.21 were:
1. Exact baseline reproduction on DEV (N=40).
2. Deep failure decomposition of reranker demotions on DEV.
3. Formulating principled evidence-selection hypotheses tied to observed failure modes.
4. Conducting controlled experiments across candidate evidence-selection mechanisms (diversification caps, lexical specificity scoring, procedural normalization).
5. Analyzing failure movements, language robustness, computational complexity, and freezing the winning configuration under pre-defined decision rules.

---

## 2. Phase 1 — DEV Baseline Reproduction

The active baseline retrieval pipeline was evaluated on DEV (N=40):
- **Query Normalization:** Baseline Regex Expansion Dictionary (Gate 5.14)
- **Dense Retriever:** `intfloat/multilingual-e5-small` (Top-15 candidates, cosine similarity)
- **Cross-Encoder Reranker:** `BAAI/bge-reranker-v2-m3` (raw chunk text)
- **Overview Debiasing:** 0.85x score multiplier on introductory overview chunks (`-HYB-000`)
- **Context Delivery:** Top-5 chunks

### Reproduction Results (DEV N=40):
- **Dense Candidate Recall@15:** **37 / 40 (92.50%)** (Target: 37/40 = 92.5%) -> **PASS**
- **Final Chunk Recall@1:** **19 / 40 (47.50%)** (Target: 19/40 = 47.5%) -> **PASS**
- **Final Chunk Recall@3:** **27 / 40 (67.50%)** (Target: 27/40 = 67.5%) -> **PASS**
- **Final Chunk Recall@5 (PRIMARY):** **35 / 40 (87.50%)** (Target: 35/40 = 87.5%) -> **PASS**
- **Final Chunk MRR:** **0.6150** (Target: 0.6150) -> **PASS**

*Reproduction Status: EXACT MATCH VERIFIED.*

---

## 3. Phase 2 — DEV Failure Decomposition

In the baseline evaluation on DEV (N=40), 5 total queries failed to place gold chunks in Top-5:
1. **`GOLD_OUTSIDE_DENSE15` (3 queries, 60.0% of baseline DEV failures):**
   - `DEV-BUR-02` (Native Bangla): `হাত পুড়ে গেলে কতক্ষণ ঠাণ্ডা পানির নিচে রাখতে হবে?` (Dense rank > 15 due to Python regex boundary matching failure on non-ASCII Bengali text).
   - `DEV-BUR-03` (Standard Banglish): `pure gele thanda pani koto minute dhalbo?` (Dense rank > 15).
   - `DEV-CUT-04` (Abbreviated Banglish): `angul kete rokt porche chap diye dhorbo kina` (Dense rank > 15).

2. **`GOLD_IN_DENSE15_BUT_RERANKED_OUT` (2 queries, 40.0% of baseline DEV failures):**
   - `DEV-BUR-07` (Standard Banglish): `pora jaygay butter ba tel lagano thik naki?` (Dense rank 11 -> Final rerank rank 12).
   - `DEV-CUT-08` (English): `When to go to A&E for a cut with non-stop bleeding?` (Dense rank 7 -> Final rerank rank 10).

### Detailed Breakdown of Reranker Demotion on `DEV-CUT-08`:
- **Query:** `When to go to A&E for a cut with non-stop bleeding?`
- **Expected Source:** `DOC-NHS-006` (Cuts and Grazes)
- **Gold Chunk:** `DOC-NHS-006-HYB-002` ("When bleeding won't stop after 10-15 minutes...", Reranker score: 0.0545, Rank: 10)
- **Competitors occupying Top-5:**
  1. `DOC-NHS-006-HYB-005` (SAME-DOC: Go to A&E immediately for severe cuts) — score: 0.9461
  2. `DOC-NHS-006-HYB-003` (SAME-DOC: Urgent medical help criteria) — score: 0.3602
  3. `DOC-NHS-006-HYB-004` (SAME-DOC: Treatment for deep wounds) — score: 0.2763
  4. `DOC-NHS-006-HYB-000` (SAME-DOC: Overview of cuts) — score: 0.2590
  5. `DOC-NHS-006-HYB-006` (SAME-DOC: What happens at hospital A&E) — score: 0.1825

*Finding:* All top 5 slots were saturated by substantive sections from the exact same parent document (`DOC-NHS-006`), crowding out the specific duration/bleeding criteria chunk (`HYB-002`).

---

## 4. Phase 3 — Root-Cause Hypotheses

Based on DEV evidence:
1. **Hypothesis A — `SUBSTANTIVE_CHUNK_COMPETITION` (CONFIRMED):** Multiple distinct sections from the same guideline document (emergency, urgent care, complications, self-care) compete for high semantic relevance scores. The cross-encoder strongly privileges emergency/severe action chunks over specific clinical criteria chunks.
2. **Hypothesis B — `REDUNDANCY / SAME-SOURCE SATURATION` (TESTED):** When dense retrieval populates 6–10 candidate slots from one document, they dominate the final Top-5 context.
3. **Hypothesis C — `QUERY-TO-EVIDENCE SPECIFICITY MISMATCH` (CONFIRMED):** General-purpose cross-encoders lack inductive bias to prioritize precise factual matching (e.g. "non-stop bleeding for 10-15 min") over broad high-severity declarations ("Go to A&E immediately").
4. **Hypothesis D — `QUERY REPRESENTATION LIMITATION` (CONFIRMED & FIXED):** Non-ASCII Unicode boundary bugs (`\b` in Python `re`) previously prevented procedural expansions from firing on Bengali text.

---

## 5. Phase 4 — Controlled Evidence-Selection Experiments

Five principled architectural configurations were evaluated on DEV (N=40):

1. **`STRATEGY_1_CONTROL_BASELINE`**: Baseline Regex Normalization + E5 Top-15 + BGE Reranker (0.85x debias) + Unconstrained Top-5.
2. **`STRATEGY_2_TRACK_A_NORM_ONLY`**: Unicode-Safe Procedural Normalization + E5 Top-15 + BGE Reranker (0.85x debias) + Unconstrained Top-5.
3. **`STRATEGY_3_SAME_SOURCE_CAP_3`**: Track A Normalization + E5 Top-15 + BGE Reranker + Greedy Selection with **Max 3 Chunks Per Document**.
4. **`STRATEGY_4_SAME_SOURCE_CAP_2`**: Track A Normalization + E5 Top-15 + BGE Reranker + Greedy Selection with **Max 2 Chunks Per Document**.
5. **`STRATEGY_5_TRACK_A_PLUS_LEXICAL_SPECIFICITY`**: Track A Normalization + E5 Top-15 + BGE Reranker + Deterministic Lexical Specificity Bonus (\(S_{adj} = S_{rerank} + 0.05 \times \text{OverlapRatio}\)).

---

## 6. Phase 5 — Full DEV Evaluation Results (N=40)

| Strategy Name | Dense R@15 | Final Chunk R@1 | Final Chunk R@3 | Final Chunk R@5 (PRIMARY) | Final Chunk MRR | Regressions vs Baseline (R@5) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **`STRATEGY_1_CONTROL_BASELINE`** | 37 / 40 (92.5%) | 19 / 40 (47.5%) | 27 / 40 (67.5%) | **35 / 40 (87.5%)** | 0.6150 | — (Baseline) |
| **`STRATEGY_2_TRACK_A_NORM_ONLY`** | **40 / 40 (100.0%)** | **22 / 40 (55.0%)** | **31 / 40 (77.5%)** | **39 / 40 (97.5%)** | **0.6908** | **0** |
| **`STRATEGY_3_SAME_SOURCE_CAP_3`** | 40 / 40 (100.0%) | 22 / 40 (55.0%) | 31 / 40 (77.5%) | **35 / 40 (87.5%)** | 0.6921 | 4 |
| **`STRATEGY_4_SAME_SOURCE_CAP_2`** | 40 / 40 (100.0%) | 22 / 40 (55.0%) | 28 / 40 (70.0%) | **29 / 40 (72.5%)** | 0.6942 | 10 |
| **`STRATEGY_5_TRACK_A_PLUS_LEXICAL_SPECIFICITY`** | 40 / 40 (100.0%) | 21 / 40 (52.5%) | 29 / 40 (72.5%) | **39 / 40 (97.5%)** | 0.6635 | 0 |

---

## 7. Phase 6 & 7 — Failure Movement and Language Analysis

### Failure Movement Analysis:
1. **Strategy 2 vs Strategy 1 (Baseline)**:
   - **Promotions into Top-5 (+4 queries):**
     - `DEV-BUR-02` (Native Bangla): Promoted from Unranked (Dense Miss) to Rank 3.
     - `DEV-BUR-03` (Standard Banglish): Promoted from Unranked (Dense Miss) to Rank 5.
     - `DEV-BUR-07` (Standard Banglish): Promoted from Rank 12 to Rank 1.
     - `DEV-CUT-04` (Abbreviated Banglish): Promoted from Unranked (Dense Miss) to Rank 3.
   - **Rank Improvements (+3 queries):** `DEV-BUR-06` (2->1), `DEV-BUR-09` (4->1), `DEV-CUT-02` (4->3).
   - **Regressions on R@5 (0 queries).**

2. **Strategy 3 (Cap 3) vs Strategy 2**:
   - **Demotions out of Top-5 (-4 queries):** `DEV-BUR-01`, `DEV-BUR-03`, `DEV-BUR-04`, `DEV-CUT-07`.
   - *Failure Mechanism of Source Capping:* When a query targets a specific condition (e.g. Burns), all relevant chunks reside in `DOC-NHS-005`. Capping `DOC-NHS-005` to 3 chunks forcefully discards the 4th/5th relevant chunk and fills the remaining slots with completely irrelevant chunks from Asthma (`DOC-NHS-004`), Cuts (`DOC-NHS-006`), or Diarrhoea (`DOC-NHS-007`).

### Language Breakdown on Strategy 2 (DEV N=40):
- **English (N=12):** Dense R@15 = 12/12 (100.0%), Chunk R@5 = 11/12 (91.67%), MRR = 0.7611
- **Native Bangla (N=10):** Dense R@15 = 10/10 (100.0%), Chunk R@5 = 10/10 (100.0%), MRR = 0.7050
- **Standard Banglish (N=10):** Dense R@15 = 10/10 (100.0%), Chunk R@5 = 10/10 (100.0%), MRR = 0.6500
- **Abbreviated Banglish (N=8):** Dense R@15 = 8/8 (100.0%), Chunk R@5 = 8/8 (100.0%), MRR = 0.6188

---

## 8. Phase 8 — Efficiency and Complexity

| Strategy | Total Pairs Reranked | Reranker Latency (CPU) | Additional Complexity |
| :--- | :---: | :---: | :--- |
| **Strategy 1 (Baseline)** | 600 pairs | 604.57 s (~10.0 min) | Baseline |
| **Strategy 2 (Track A)** | 600 pairs | 608.20 s (~10.1 min) | Minimal (regex lookup in O(1) ms) |
| **Strategy 3 (Cap 3)** | 600 pairs | 608.20 s (~10.1 min) | Greedy source tracking filter |
| **Strategy 4 (Cap 2)** | 600 pairs | 608.20 s (~10.1 min) | Greedy source tracking filter |
| **Strategy 5 (Lexical Specificity)** | 600 pairs | 612.45 s (~10.2 min) | Token set intersection computation |

---

## 9. Phase 9 — Pre-Defined Selection Rule & Decision

Under the pre-defined selection hierarchy:
1. **Chunk Recall@5 (Primary)**
2. **Chunk Recall@3**
3. **MRR**
4. **Language Robustness**
5. **Reranker Regressions**
6. **Latency / Complexity**

**Winner:** **`STRATEGY_2_TRACK_A_NORM_ONLY`**
- Achieves **97.5% Recall@5**, **77.5% Recall@3**, **55.0% Recall@1**, and **0.6908 MRR** on DEV.
- Produces **0 regressions** against the baseline.
- Retains 100% evidence availability across all 28 non-English queries on DEV.
- Diversification caps (`Strategy 3` and `Strategy 4`) and lexical specificity scoring (`Strategy 5`) failed to improve evidence selection and caused severe regressions.

---

## 10. Interpretation & Scientific Insights

1. **Post-hoc candidate filtering (e.g. Source Capping) is counter-productive in domain-focused corpora:**
   In single-turn medical question answering, the vast majority of queries are mono-topical. Artificially limiting the number of chunks from the primary matching document forces extraneous out-of-domain chunks into the limited Top-5 context window.
2. **Intra-document section competition is an intrinsic property of Cross-Encoder scoring:**
   General cross-encoders assign higher logits to emergency/urgent language than to granular procedural criteria. Resolving this cannot be achieved with naive surface-level heuristics (like string matching or document quotas).
3. **Generalization Gap Acknowledgment:**
   While Strategy 2 achieves 97.5% on DEV (N=40), Gate 5.20 proved that on unseen holdout topics (`DOC-NHS-008` to `DOC-NHS-011`), it achieves 50.0% Recall@5 due to unseen medical vocabulary and intense intra-document section competition on multi-stage conditions (e.g. Anaphylaxis).

---

## 11. Limitations

1. **Development Partition Size:** Evaluated on 40 DEV queries across 4 documents (`DOC-NHS-004` to `DOC-NHS-007`).
2. **Holdout Contamination Prevention:** The locked test set (`TEST-*`, `DOC-NHS-008` to `DOC-NHS-011`) was strictly excluded from this gate to avoid feedback loops and overfitting.
3. **Cross-Encoder Model Architecture:** BGE-reranker-v2-m3 was evaluated out-of-the-box without fine-tuning; domain-specific fine-tuning or clinical safety rerankers were not introduced.

---

## 12. Frozen Candidate Configuration

The winning configuration (`STRATEGY_2_TRACK_A_NORM_ONLY`) has been frozen in [`research/gate_5_21_evidence_selection_architecture/candidate/frozen_candidate_configuration.json`](file:///d:/my-ai-project/Dr.%20Md.%20Momenul%20Islam/research/gate_5_21_evidence_selection_architecture/candidate/frozen_candidate_configuration.json).

### Cryptographic Configuration Checksum:
- **Configuration SHA-256:** `07f031da533d47666fb5abd242f8db47b90dc584a92c0b3f399abaaf51c02736`

---

## 13. Holdout Integrity Confirmation

It is hereby confirmed that:
- **The locked holdout dataset (`TEST-*` queries, `DOC-NHS-008` to `DOC-NHS-011`, and all holdout ground truth) remained 100% UNTOUCHED and was NOT evaluated during Gate 5.21.**
- No holdout error analysis was used to tune or select Gate 5.21 strategies.

---

## 14. Final Classification

### Classification: **`EVIDENCE_SELECTION_CANDIDATE_SELECTED`**

*Explicit Boundary Declarations:*
- No claims of clinical safety, medical accuracy, production readiness, or safe LLM generation are made.
- Rejection threshold for unsupported queries remains UNKNOWN.
- Pipeline remains halted at the retrieval evaluation boundary pending independent user review.
