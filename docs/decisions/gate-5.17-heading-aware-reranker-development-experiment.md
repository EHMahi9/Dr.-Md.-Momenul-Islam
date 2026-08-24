# Gate 5.17 — Development-Only Heading-Aware Reranker Experiment

> **Final Status:** `HEADING_AWARE_RERANKER_REJECTED`

---

## 1. Executive Summary & Experimental Objective

In **Gate 5.16**, the failure decomposition identified **`SUBSTANTIVE_CHUNK_COMPETITION`** and the absence of explicit structural section headings in reranker passage representations as a candidate root cause for intra-document reranking errors (such as `DEV-CUT-08`).

The objective of **Gate 5.17** was to conduct a **strictly isolated, development-only controlled experiment** on the 40 Development queries (`DOC-NHS-004` to `DOC-NHS-007`) to test the single hypothesis:

> *"Adding the exact structural section heading to the reranker passage representation may reduce same-document section confusion."*

The locked holdout (`DOC-NHS-008` to `DOC-NHS-011` and 40 `TEST-*` queries) remained **100% UNTOUCHED AND UNSEEN**.

---

## 2. Experimental Setup & Heading Extraction Rule

### Pipeline Isolation & Control Parameters
All components were strictly identical between Control and Experimental pipelines:
- **Corpus**: `HYBRID_600` chunk set (`provenance_manifest.json`, 68 total chunks, 38 DEV chunks).
- **Dense Retriever**: `intfloat/multilingual-e5-small` at candidate depth \(K=15\).
- **Cross-Encoder**: `BAAI/bge-reranker-v2-m3` on CPU.
- **Debiasing Rule**: Frozen 0.85x multiplier applied to `-HYB-000` overview chunks.
- **Context Window**: Top-5 delivered evidence context.
- **Queries & Gold Labels**: 40 DEV queries and frozen chunk gold labels.

### Passage Representation Formats
1. **Control Baseline Representation**:
   ```
   {chunk_text}
   ```
2. **Experimental Heading-Aware Representation**:
   ```
   Section: {exact_section_heading}
   Content: {chunk_text}
   ```

### Exact Heading Extraction Rule
- For each chunk, the first structural lead-in or paragraph was parsed deterministically against NHS structural heading patterns (`Immediate action required:.*`, `Symptoms of .*`, `Treatments for .*`, `How .*`, `What to do .*`, etc.).
- If the first line/paragraph is a valid structural heading, it was extracted verbatim as `{exact_section_heading}`.
- If no heading pattern matched, the chunk fell back to the clean source title (e.g. `Asthma`, `Burns and scalds`, `Cuts and grazes`, `Dehydration`).

---

## 3. Baseline Reproduction (Phase 1)

The Gate 5.16 baseline was executed as the Control Baseline pipeline and verified:

| Metric | Gate 5.16 Target | Control Baseline Actual | Status |
| :--- | :---: | :---: | :---: |
| **Dense Candidate Pool Recall@15** | 37 / 40 (92.50%) | **37 / 40 (92.50%)** | **PASS** |
| **Final Chunk Recall@1** | 19 / 40 (47.50%) | **19 / 40 (47.50%)** | **PASS** |
| **Final Chunk Recall@3** | 27 / 40 (67.50%) | **27 / 40 (67.50%)** | **PASS** |
| **Final Chunk Recall@5** | 35 / 40 (87.50%) | **35 / 40 (87.50%)** | **PASS** |
| **Final Chunk MRR** | 0.6150 | **0.6150** | **PASS** |

---

## 4. Full Metric Comparison (DEV N=40)

| Metric | Control Baseline | Experimental Heading-Aware | Absolute Delta | Relative Change |
| :--- | :---: | :---: | :---: | :---: |
| **Final Chunk Recall@5 (PRIMARY)** | **35 / 40 (87.50%)** | **34 / 40 (85.00%)** | **-2.50%** | **-1 query loss** |
| **Final Chunk MRR** | **0.6150** | **0.5839** | **-0.0311** | **-5.06%** |
| **Final Chunk Recall@1** | **19 / 40 (47.50%)** | **18 / 40 (45.00%)** | **-2.50%** | **-5.26%** |
| **Final Chunk Recall@3** | **27 / 40 (67.50%)** | **26 / 40 (65.00%)** | **-2.50%** | **-3.70%** |

---

## 5. Language Breakdown (DEV N=40)

| Language Category | DEV N | Baseline Recall@5 | Experimental Recall@5 | Baseline MRR | Experimental MRR | Primary Effect |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **English** | 12 | 11 / 12 (91.67%) | 11 / 12 (91.67%) | 0.7611 | 0.7542 | Neutral (MRR -0.0069) |
| **Native Bangla** | 10 | 9 / 10 (90.00%) | 9 / 10 (90.00%) | 0.6150 | 0.5833 | Slight MRR drop (-0.0317) |
| **Standard Banglish** | 10 | 8 / 10 (80.00%) | 8 / 10 (80.00%) | 0.4867 | 0.3855 | Severe MRR drop (-0.1012, -20.8%) |
| **Abbreviated Banglish** | 8 | 7 / 8 (87.50%) | 6 / 8 (75.00%) | 0.5563 | 0.5771 | **Recall@5 degraded (-1 query)** |

---

## 6. Failure Movement & Rank Shift Analysis

Across the 40 DEV queries:
- **Total queries with rank or context differences**: **28 / 40 (70.0%)**
- **Improved queries**: **4 / 40 (10.0%)** (`DEV-BUR-09`, `DEV-CUT-06`, `DEV-DEH-04`, `DEV-DEH-09`)
- **Degraded queries**: **9 / 40 (22.5%)** (`DEV-AST-03`, `DEV-AST-04`, `DEV-AST-10`, `DEV-BUR-07`, `DEV-CUT-05`, `DEV-CUT-07`, `DEV-CUT-10`, `DEV-DEH-03`, `DEV-DEH-06`)
- **Net rank movement**: -5 degraded queries on net balance.

### Critical Failure Case Studies:

1. **`DEV-CUT-10` (Abbreviated Banglish) — Dropped Out of Top-5**:
   - **Query**: *"rokto konovabei thamtasena 10 min hoise a&e jabo?"*
   - **Gold Chunk**: `DOC-NHS-006-HYB-002` (direct pressure and bleeding control).
   - **Baseline Rank**: **Rank 4** (Score: `0.0106`).
   - **Experimental Rank**: **Rank 6** (Score: `0.0028`, dropped out of Top-5).
   - **Mechanism**: Prepending `Section: What to do if the wound is bleeding a lot` diluted the specific bleeding cessation tokens against general wound care overview `DOC-NHS-006-HYB-000` (`Section: Cuts and grazes`), allowing `HYB-000` to take Rank 4 and push `HYB-002` out to Rank 6.

2. **`DEV-CUT-08` (English) — Target Test Case from Gate 5.16**:
   - **Query**: *"When to go to A&E for a cut with non-stop bleeding?"*
   - **Gold Chunk**: `DOC-NHS-006-HYB-002`
   - **Baseline Rank**: **Rank 10**
   - **Experimental Rank**: **Rank 10 (Unchanged)**
   - **Mechanism**: `DOC-NHS-006-HYB-005` has the heading `Immediate action required: Call 999 or go to A&E if:`, which matches the user query *"When to go to A&E"* with even higher cross-encoder token similarity (`0.9526`), keeping `HYB-002` at Rank 10. Heading awareness did not rescue `DEV-CUT-08`.

3. **`DEV-AST-03` (Standard Banglish) — Severe Rank Demotion**:
   - **Query**: *"asthma hole ki ki shomossha hoy bujhte parbo kivabe?"*
   - **Gold Chunk**: `DOC-NHS-004-HYB-001` (Symptoms of asthma).
   - **Baseline Rank**: **Rank 1** (Score: `0.0426`).
   - **Experimental Rank**: **Rank 3** (Score: `0.0245`).
   - **Mechanism**: Inhaler treatment chunk `DOC-NHS-004-HYB-003` (`Section: Use your asthma reliever inhaler if you have one:`) outranked the symptom chunk due to strong English verb alignment in the heading.

---

## 7. Latency Evaluation

| Representation | Total Inference Time (600 pairs on CPU) | Latency per Query | Relative Latency Overhead |
| :--- | :---: | :---: | :---: |
| **Control Baseline** | 514.03 seconds | 12.85 seconds | Baseline (0.00%) |
| **Experimental Heading-Aware** | 562.87 seconds | 14.07 seconds | **+9.50% (+48.84s)** |

*Observation*: Prepending section headings adds ~15–25 tokens per pair, resulting in a **9.50% increase in cross-encoder computational latency** without delivering retrieval accuracy gains.

---

## 8. Interpretation, Limitations & Scientific Conclusions

### [VERIFIED FACT]
1. Prepending structural section headings (`Section: {heading}\nContent: {text}`) to `bge-reranker-v2-m3` passage inputs **degraded primary Chunk Recall@5 from 87.50% to 85.00% (-2.50%)** and **MRR from 0.6150 to 0.5839 (-0.0311)** on DEV.
2. In Standard Banglish queries, MRR declined significantly by **-20.8% (0.4867 \(\rightarrow\) 0.3855)**.
3. In 70% of DEV queries (28/40), heading awareness altered rank positions, resulting in **9 degraded queries vs only 4 improved queries**.
4. Heading awareness **failed to improve or rescue the primary target failure case `DEV-CUT-08`** (which remained at Rank 10).

### [ROOT CAUSE ANALYSIS]
Cross-encoders compute fine-grained all-to-all cross-attention across all tokens in query and passage. Prepending `Section: ...` introduces high-salience structural tokens that:
1. **Amplify Keyword Distraction**: Headings like *"Use your asthma reliever inhaler"* or *"Immediate action required: Call 999"* draw excessive attention weights away from nuanced symptom phrases in transliterated Banglish queries.
2. **Exacerbate Intra-Document Competition**: When multiple sections have strong action headings (e.g. *Treatment* vs *Infection* vs *Emergency*), the cross-encoder gives top ranks to the most dramatically titled section rather than the specific factual answer chunk.

---

## 9. Final Scientific Classification & Status

### Final Status: **`HEADING_AWARE_RERANKER_REJECTED`**

The hypothesis that prepending structural section headings to cross-encoder passage representations reduces same-document section confusion is **empirically disproven and rejected**.

The frozen Gate 5.14 / 5.15 retrieval configuration:
- **Chunking**: `HYBRID_600`
- **Dense Retriever**: `intfloat/multilingual-e5-small` (Top-15)
- **Cross-Encoder**: `BAAI/bge-reranker-v2-m3` on raw chunk text (`{chunk_text}`)
- **Debiasing Rule**: 0.85x on `-HYB-000` overview chunks
- **Delivered Context**: Top-5

remains the active, superior development baseline.

---
**ABSOLUTE STOP CONDITION REACHED**: Gate 5.17 is complete. No candidate modifications were pushed to holdout, no production code was altered, and no LLMs were invoked. Awaiting independent review.
