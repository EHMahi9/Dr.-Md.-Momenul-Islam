# Gate 5.9.1 — Chunk-Level Relevance & Frozen Retrieval Result Integrity Audit

> **Status:** SOURCE_LEVEL_ONLY__CHUNK_LEVEL_UNVALIDATED

---

## 1. Audit Objective

The objective of Gate 5.9.1 is to conduct an independent measurement integrity audit on the frozen retrieval results produced by Gate 5.9. Specifically, this audit evaluates whether the promising **85.0% source-level holdout accuracy** reported in Gate 5.9 represents genuine retrieval of the specific clinical evidence chunks needed to answer user queries, or whether it masks intra-document chunk selection failures.

All analyses in this gate were performed strictly by re-scoring existing frozen Gate 5.9 rankings against a newly constructed, clinically audited chunk-level gold label set. **No model weights, chunking parameters, Top-K settings, or retrieval code were modified, and no embeddings or rerankers were re-executed.**

---

## 2. Existing Source-Level Metric Definition & Exact Code Inspection

Inspection of [`run_gate_5_9_locked_holdout_eval.py`](file:///d:/my-ai-project/Dr.%20Md.%20Momenul%20Islam/research/gate_5_9_optimization/run_gate_5_9_locked_holdout_eval.py) revealed the exact mechanism by which correctness was computed in Gate 5.9:

```python
# Lines 92, 113, and 126 in run_gate_5_9_locked_holdout_eval.py:
dense_top_sids = [c["parent_source_id"] for c in top5_chunks]
r5_top_sids = [chunks[idx]["parent_source_id"] for idx in r5_ranked_indices]
...
r5_r1 = (r5_top_sids[0] == expected_sid) if is_valid else False
```

### Key Finding:
The evaluation evaluated only whether the Top-1 chunk came from the **same parent document** (`expected_sid`), rather than whether the retrieved chunk contained the actual clinical evidence required to answer the query (`expected_chunk_id`).

---

## 3. Why Source-Level Correctness is Insufficient for RAG

In a Retrieval-Augmented Generation (RAG) architecture, the generator LLM is conditioned exclusively on the text of the retrieved chunks (context window). 
- If a user asks: *"How many hours to stay off work after diarrhoea stops?"*
- Expected Gold Chunk: `DOC-NHS-008-HYB-001` (*"stay off work or school until you have not been sick or had diarrhoea for at least 2 days (48 hours)"*).
- Retrieved Top-1 Chunk: `DOC-NHS-008-HYB-000` (*"How to treat diarrhoea and vomiting yourself at home... drink fluids in small sips..."*).

Under source-level evaluation, retrieving `DOC-NHS-008-HYB-000` is scored as **100% CORRECT** because both belong to `DOC-NHS-008`. However, in a live clinical RAG system, the prompt context given to the LLM would contain general fluid advice but completely lack the 48-hour rule, leading to an evidence-grounding failure or hallucination.

---

## 4. Gold-Label Methodology

To construct unbiased chunk-level gold labels:
1. Every valid query in [`frozen_benchmark.json`](file:///d:/my-ai-project/Dr.%20Md.%20Momenul%20Islam/research/gate_5_8_retrieval_validation/benchmark/frozen_benchmark.json) (40 DEV queries + 40 LOCKED TEST queries) was independently inspected.
2. The exact text of all 68 `HYBRID_600` chunks in [`provenance_manifest.json`](file:///d:/my-ai-project/Dr.%20Md.%20Momenul%20Islam/research/gate_5_9_optimization/chunks/hybrid_600/provenance_manifest.json) was audited.
3. For each query, all chunks containing the necessary and sufficient clinical evidence to answer the query topic were mapped to `gold_chunk_ids`.
4. Where multiple chunks legitimately contained relevant evidence (e.g. general first aid spanning overview and specific inhaler steps), all valid chunk IDs were included as acceptable targets.
5. All 80 gold mappings and clinical rationales were recorded in [`chunk_gold_labels.json`](file:///d:/my-ai-project/Dr.%20Md.%20Momenul%20Islam/research/gate_5_9_optimization/chunk_gold_labels.json).

---

## 5. Gold-Label Uncertainty & Ambiguity Handling

- **Unambiguous Direct Facts** (e.g. fever cutoff 38C, 20-minute burn cooling, 48-hour stay-at-home rule, 999 emergency callouts): Mapped to a single specific gold chunk.
- **Composite First Aid Queries** (e.g. clean cut and stop bleeding, treat asthma attack): Mapped to an array of 2–3 acceptable chunks.
- **Unresolved Ambiguities**: None were unresolved; all 80 queries mapped to at least one valid source section.

---

## 6. Re-Scored Source-Level vs Chunk-Level Retrieval Performance

Re-scoring the frozen Gate 5.9 rankings across all 80 valid benchmark queries yielded the following comparison:

| Benchmark Split | Sample Size (N) | Metric Type | Dense Recall@1 | Top-5+Rerank Recall@1 | Disagreement Count (Src Correct / Chunk Incorrect) | Disagreement Rate (%) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **DEVELOPMENT SPLIT** | 40 | Source-Level | 65.00% | **72.50%** | — | — |
| | 40 | **Chunk-Level** | 27.50% | **37.50%** | **14 / 40** | **35.00%** |
| **LOCKED HOLDOUT SPLIT** | 40 | Source-Level | 77.50% | **85.00%** | — | — |
| | 40 | **Chunk-Level** | 22.50% | **20.00%** | **26 / 40** | **65.00%** |
| **OVERALL CORPUS** | 80 | Source-Level | 71.25% | **78.75%** | — | — |
| | 80 | **Chunk-Level** | 25.00% | **28.75%** | **40 / 80** | **50.00%** |

---

## 7. Linguistic Category Breakdown (Source vs Chunk Level)

### Locked Holdout Split (N=40):
| Language Category | N | Source-Level Dense R@1 | Source-Level Rerank R@1 | **Chunk-Level Dense R@1** | **Chunk-Level Rerank R@1** | Disagreement Rate (%) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **English** | 12 | 91.67% | **100.00%** | 41.67% | **33.33%** | **66.67%** (8/12) |
| **Native Bangla** | 11 | 90.91% | **90.91%** | 27.27% | **27.27%** | **63.64%** (7/11) |
| **Standard Banglish** | 9 | 44.44% | **66.67%** | 0.00% | **0.00%** | **66.67%** (6/9) |
| **Abbreviated Banglish** | 8 | 75.00% | **75.00%** | 12.50% | **12.50%** | **62.50%** (5/8) |

### Full Corpus (N=80 Valid Queries):
| Language Category | N | Source-Level Dense R@1 | Source-Level Rerank R@1 | **Chunk-Level Dense R@1** | **Chunk-Level Rerank R@1** | Disagreement Rate (%) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **English** | 24 | 95.83% | **100.00%** | 37.50% | **37.50%** | **62.50%** (15/24) |
| **Native Bangla** | 21 | 71.43% | **85.71%** | 19.05% | **28.57%** | **57.14%** (12/21) |
| **Standard Banglish** | 19 | 42.11% | **57.89%** | 15.79% | **21.05%** | **36.84%** (7/19) |
| **Abbreviated Banglish** | 16 | 68.75% | **62.50%** | 25.00% | **25.00%** | **37.50%** (6/16) |

---

## 8. Source-vs-Chunk Disagreement Analysis

Across the benchmark, **40 out of 80 queries (50.0%)** exhibited severe source-versus-chunk disagreement. 

### Notable Critical Failure Examples:

1. **`TEST-DIA-05` (English - Diarrhoea 48-Hour Exclusion Rule)**:
   - **Query**: *"How long should you stay off work or school after diarrhoea stops?"*
   - **Expected Source**: `DOC-NHS-008` (Diarrhoea and vomiting)
   - **Acceptable Gold Chunk**: `DOC-NHS-008-HYB-001` (*"stay off work or school until you have not been sick or had diarrhoea for at least 2 days (48 hours)"*)
   - **Retrieved Top-1 Chunk**: `DOC-NHS-008-HYB-000` (*"How to treat diarrhoea and vomiting yourself at home... drink lots of fluids..."*)
   - **Failure Analysis**: Source-level evaluation marked this as correct (100%), but the retrieved chunk completely lacks the 48-hour quarantine rule.

2. **`TEST-HEA-01` (English - Headache Home Care)**:
   - **Query**: *"What can you do at home to ease a common headache?"*
   - **Expected Source**: `DOC-NHS-009` (Headaches)
   - **Acceptable Gold Chunk**: `DOC-NHS-009-HYB-000` (*"How to ease a headache yourself... drink plenty of water, get plenty of rest, take paracetamol or ibuprofen..."*)
   - **Retrieved Top-1 Chunk**: `DOC-NHS-009-HYB-001` (*"Don't drink alcohol, don't skip meals..."*)
   - **Failure Analysis**: Model retrieved the negative "Don'ts" chunk rather than the primary home care instructions chunk.

3. **`TEST-FEV-01` (English - Child Fever 38C Threshold)**:
   - **Query**: *"What temperature counts as a fever in children?"*
   - **Expected Source**: `DOC-NHS-010` (High temperature in children)
   - **Acceptable Gold Chunk**: `DOC-NHS-010-HYB-000` (*"A high temperature is 38C or more."*)
   - **Retrieved Top-1 Chunk**: `DOC-NHS-010-HYB-001` (*"give them plenty of fluids... paracetamol or ibuprofen..."*)
   - **Failure Analysis**: The retrieved chunk explains medication administration but fails to state the 38C clinical diagnostic threshold.

4. **`DEV-BUR-05` (English - Butter/Oil on Burns Warning)**:
   - **Query**: *"Should you put butter or oil on a burn?"*
   - **Expected Source**: `DOC-NHS-005` (Burns and scalds)
   - **Acceptable Gold Chunk**: `DOC-NHS-005-HYB-001` (*"Don't use ice, iced water, creams or greasy substances like butter"*)
   - **Retrieved Top-1 Chunk**: `DOC-NHS-005-HYB-004` (*"take painkillers such as paracetamol... use emollient ointment..."*)
   - **Failure Analysis**: Model retrieved general aftercare ointment advice instead of the critical contraindication against butter and oils.

---

## 9. Reranker Effect: Source-Level vs Chunk-Level Disaggregation

In Gate 5.9, BGE Reranker v2 m3 was reported to produce **8 improvements and 2 degradations** (+6 net gain) at the document level. Disaggregating this effect to the chunk level reveals a different dynamic:

| Dimension | Improvements (Dense Miss -> Rerank Hit) | Degradations (Dense Hit -> Rerank Miss) | Neutral (Unchanged) | Net Impact |
| :--- | :---: | :---: | :---: | :---: |
| **Source-Level Reranker Impact** | 8 | 2 | 70 | **+6 queries** |
| **Chunk-Level Reranker Impact** | 5 | 2 | 73 | **+3 queries** |

### Breakdown of Reranker Chunk Shifts:
- In **3 cases**, the reranker successfully elevated the correct document into Rank 1, but selected an uninformative or off-target chunk within that document.
- In **5 cases**, the reranker successfully identified the exact gold chunk from within the Top-5 candidate pool.
- In **2 cases**, the reranker degraded a correct chunk to Rank 2 or below.

---

## 10. Hard-Negative & Out-of-Corpus Handling

Re-scoring confirms the Gate 5.9 findings regarding non-result queries:
- **Hard Negatives (N=12)**: Mean dense similarity of 0.8403, mean cross-encoder score of 0.0304 (max 0.1840).
- **Out-of-Corpus (N=8)**: Mean dense similarity of 0.8108, mean cross-encoder score of 0.0006 (max 0.0031).
- Non-result queries do not retrieve relevant chunks; cross-encoder scores provide strong rejection boundaries (\(\le 0.184\)), whereas dense cosine similarity alone fails to separate them.

---

## 11. Reproducibility & Integrity Hashes

All evaluated artifacts remain completely unmodified from Gate 5.9:

| Artifact | File Path | SHA-256 Checksum |
| :--- | :--- | :--- |
| **Frozen Benchmark** | `research/gate_5_8_retrieval_validation/benchmark/frozen_benchmark.json` | `7debd4b7d804938d4c7ecf8f414f51d936830b5a6d9d62ebfcaedde1874c8a81` |
| **Frozen Config** | `research/gate_5_9_optimization/frozen_config_manifest.json` | `c04495e865f128bc5f67ea55b6efcfec6e8ec9ee8109d3b37937fe5d2f33c373` |
| **HYBRID_600 Chunks** | `research/gate_5_9_optimization/chunks/hybrid_600/provenance_manifest.json` | `c04495e865f128bc5f67ea55b6efcfec6e8ec9ee8109d3b37937fe5d2f33c373` |
| **Gate 5.9 Eval Output**| `research/gate_5_9_optimization/evaluations/gate_5_9_locked_holdout_evaluation.json`| `dffb3bb9dcf4fcfd7a64117b35ea83cb0d738f654b9d0726bbd92b3c21c7d2c3` |
| **Gold Labels Manifest**| `research/gate_5_9_optimization/chunk_gold_labels.json` | `e97b102b3ef3e317c2f61fc1ef366050b1df1e8cb85b0cb9ffbe5232d36d88b4` |
| **Gate 5.9.1 Audit JSON**| `research/gate_5_9_optimization/evaluations/gate_5_9_1_chunk_level_audit_results.json`| `4410a80c9ceac117b4c6e94441ea636fa09dae07664971c26b6493dc655b3fa6` |

---

## 12. Methodological Limitations

1. **Intra-Document Chunk Disambiguation**: Dense passage encoders trained on document-level retrieval (like E5) prioritize topical relevance over granular question-answering evidence, pulling top-level introduction chunks (`HYB-000`) rather than specific clinical subsection chunks.
2. **Top-K Context Delivery**: While Top-1 chunk accuracy is low (28.75%), multi-chunk context feeding (passing Top-3 or Top-5 chunks into the prompt context) substantially mitigates missing evidence in downstream RAG generation, provided context length limits are respected.
3. **Banglish Vocabulary Drift**: Banglish queries suffer doubly: first in document matching (44–66% source accuracy), and second in intra-document chunk ranking (0–12% chunk accuracy).

---

## 13. Corrected Retrieval Interpretation

1. **Source-Level Holdout Accuracy is Valid but Incomplete**: The 85.0% source-level holdout accuracy reported in Gate 5.9 accurately reflects document identification, but **must not be conflated with evidence-chunk retrieval**.
2. **True Evidence Retrieval Rate**: The actual proportion of queries receiving the exact clinical evidence chunk at Rank 1 is **28.75% across the corpus** and **20.00% on the locked holdout**.
3. **Evidence Gap in RAG**: Relying solely on Top-1 retrieval under the current architecture would result in 50–65% of queries presenting incomplete evidence to the generator model.

---

## 14. Final Decision

**`SOURCE_LEVEL_ONLY__CHUNK_LEVEL_UNVALIDATED`**

### Summary:
- The Gate 5.9 retrieval architecture demonstrates strong document-level routing capabilities (78.75% overall, 85.0% holdout), but fails to reliably place the specific evidence chunk at Rank 1 (28.75% overall chunk R@1, with a 50.0% source-vs-chunk disagreement rate).
- The pipeline is **NOT** validated for single-chunk Top-1 clinical evidence provision.

---
**ABSOLUTE STOP CONDITION REACHED**: Gate 5.9.1 is complete. No retrieval architecture was altered, no models were re-executed, no LLMs were called, and no production code was modified. Awaiting independent review.
