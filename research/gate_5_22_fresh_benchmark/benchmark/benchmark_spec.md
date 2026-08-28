# Gate 5.22 — Fresh Independent Benchmark Specification

## 1. Overview & Objectives

This document provides the formal specification of the **Fresh Independent Benchmark** constructed in Gate 5.22.

The goal of this benchmark is to provide a clean, uncompromised, and scientifically valid evaluation set for the frozen Gate 5.21 retrieval candidate (`STRATEGY_2_TRACK_A_NORM_ONLY`, SHA-256: `07f031da533d47666fb5abd242f8db47b90dc584a92c0b3f399abaaf51c02736`).

- **Frozen Benchmark File**: [`research/gate_5_22_fresh_benchmark/benchmark/fresh_locked_benchmark.json`](file:///d:/my-ai-project/Dr.%20Md.%20Momenul%20Islam/research/gate_5_22_fresh_benchmark/benchmark/fresh_locked_benchmark.json)
- **Benchmark SHA-256**: `a0267355615d9094fd9698ff0bbb5d9aa69311a9c822e1cd47ac12fc08573ef6`
- **Total Queries**: 50 (40 Supported + 5 Hard Negatives + 5 Out-of-Corpus)

---

## 2. Key Differences from Prior (Old TEST) Benchmark

| Dimension | Old TEST Benchmark (Gates 5.8-5.20) | Fresh Independent Benchmark (Gate 5.22) |
|---|---|---|
| **Evaluation History** | Evaluated 4 times (contaminated) | Pristine / Zero prior evaluations |
| **Document Scope** | 4 documents only (`DOC-NHS-008` to `011`) | All 8 corpus documents (`DOC-NHS-004` to `011`) |
| **Overview Gold Bias** | 14 / 40 queries mapped to `HYB-000` | **0 / 40 queries** map to `HYB-000` alone |
| **Average Gold Depth** | ~1.8 chunk index | **4.55 chunk index** |
| **Previously Untested Chunks** | N/A | **19 previously untested chunks** covered |
| **Unique Gold Chunks** | 15 / 68 chunks | **34 / 68 chunks** (50.0% corpus coverage) |

---

## 3. Query Taxonomy & Language Breakdown

### Language Distribution
- **English**: 21 queries (16 supported, 2 HN, 3 OOC)
- **Native Bangla**: 10 queries (8 supported, 1 HN, 1 OOC)
- **Standard Banglish**: 10 queries (8 supported, 1 HN, 1 OOC)
- **Abbreviated Banglish**: 9 queries (8 supported, 1 HN, 0 OOC)

### Supported Topic Distribution (5 queries per document across 8 documents = 40 queries)
1. `DOC-NHS-004` (Asthma): `FRESH-AST-01` to `FRESH-AST-05`
2. `DOC-NHS-005` (Burns and Scalds): `FRESH-BUR-01` to `FRESH-BUR-05`
3. `DOC-NHS-006` (Cuts and Grazes): `FRESH-CUT-01` to `FRESH-CUT-05`
4. `DOC-NHS-007` (Dehydration): `FRESH-DEH-01` to `FRESH-DEH-05`
5. `DOC-NHS-008` (Diarrhoea and Vomiting): `FRESH-DIA-01` to `FRESH-DIA-05`
6. `DOC-NHS-009` (Headaches): `FRESH-HEA-01` to `FRESH-HEA-05`
7. `DOC-NHS-010` (Fever in Children): `FRESH-FEV-01` to `FRESH-FEV-05`
8. `DOC-NHS-011` (Anaphylaxis): `FRESH-ANA-01` to `FRESH-ANA-05`

### Hard Negatives (5 queries)
- `FRESH-HN-01` (English): ORS dosage for infants (ORS mentioned in HYB-002, but specific infant dosage absent)
- `FRESH-HN-02` (Standard Banglish): Nebulizer use for childhood asthma (inhalers covered in HYB-008/009, nebulizer absent)
- `FRESH-HN-03` (Native Bangla): CT scan for head injury (headaches covered in DOC-NHS-009, head trauma/CT absent)
- `FRESH-HN-04` (Abbreviated Banglish): Direct aloe vera gel application on burn wound (after-sun spray mentioned in HYB-004, wound gel absent)
- `FRESH-HN-05` (English): Second-degree burn home treatment with blisters (general burn care present, degree-classification absent)

### Out-of-Corpus (5 queries)
- `FRESH-OOC-01` (English): Appendicitis symptoms and surgery
- `FRESH-OOC-02` (Native Bangla): Bone fracture plaster duration
- `FRESH-OOC-03` (Standard Banglish): Type 2 diabetes metformin dosage
- `FRESH-OOC-04` (Abbreviated Banglish): Insect removal from ear
- `FRESH-OOC-05` (English): CPR on an unconscious adult

---

## 4. Pre-Registered Evaluation Protocol

### 1. Mandatory Configuration Check
The evaluation runner must verify before running that the retrieval configuration matches SHA-256:
`07f031da533d47666fb5abd242f8db47b90dc584a92c0b3f399abaaf51c02736`

### 2. Execution Constraints
- Benchmark must be evaluated **EXACTLY ONCE** (single-shot holdout validation).
- No iterative tuning, parameter adjustment, or re-running on this benchmark is permitted.
- Raw outputs, reranker scores, dense ranks, and hit indicators must be preserved completely.

### 3. Metric Hierarchy
- **Primary Evidence Metric**: `Final Chunk Recall@5` (target: exact gold chunk presence in Top-5 reranked contexts).
- **Secondary Quality Metrics**: `Final Chunk Recall@1`, `Final Chunk Recall@3`, `Final Chunk MRR`.
- **First-Stage Diagnostics**: `Dense Candidate Recall@15`.
- **Unsupported Guardrail Diagnostics**: Top-1 reranker score distribution on Hard Negatives & Out-of-Corpus queries (no arbitrary rejection threshold claimed).
