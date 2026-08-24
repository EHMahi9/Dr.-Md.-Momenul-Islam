# Gate 5.8 — Preflight Corpus and Benchmark Audit

> **Status:** AUDIT_COMPLETE_PROCEED_TO_BENCHMARK_GENERATION

---

## 1. Purpose of Preflight Audit

Before executing Gate 5.8 empirical retrieval validation, this preflight audit independently inspects the corrected corpus artifacts from Gate 4F.2, verifies the mathematical distinctness of the new 8-document corpus from the historical 3-document benchmark, evaluates potential sources of benchmark leakage, and defines the frozen partition methodology for source-level holdout evaluation.

---

## 2. Exact Files Representing the Corrected Corpus

The Gate 5.8 evaluation operates exclusively on the verified and normalized artifacts generated in Gate 4F.2:

1. **Corrected Ingestion Manifest**:
   - Path: `research/gate_4f_semantic_chunking/corrected_ingestion/ingestion_manifest_v2.json`
   - SHA-256: `dedcd9edfad3106e875b42730c5ca214d1495b2f1c5893bab6669fb68bb076a7`
   - Total Documents: 8 (`DOC-NHS-004` through `DOC-NHS-011`)
2. **Corrected Structural Chunks Manifest (Candidate A V2)**:
   - Path: `research/gate_4f_semantic_chunking/outputs/candidate_a_heading_v2/provenance_manifest.json`
   - SHA-256: `75a7b114b8c171ce345ebbfe6cdea6e92e5969563faaf5aaa0a874562b195a1d`
   - Total Chunks: **91 chunks**
3. **Baseline Fixed-Character Chunks Manifest (For Controlled Comparison)**:
   - Path: `research/gate_4f_semantic_chunking/outputs/baseline_fixed/provenance_manifest.json`
   - SHA-256: `8fd5232df4ca88139b364642aeae358ea125c935b144da22ef2173460d5f93fc`
   - Total Chunks: **63 chunks**

---

## 3. Corpus Distinctness & Historical Independence

### Historical Corpus (Gate 5 / 5.1 / 5.3 / 5.4 / 5.5 / 5.6 / 5.7):
- `DOC-NHS-001`: Heatstroke
- `DOC-NHS-002`: Adult CPR
- `DOC-NHS-003`: Child Choking
*(Total: 3 source documents, 80 valid queries, 23 hard negatives in the 103-query benchmark).*

### Expanded Holdout Corpus (Gate 5.8):
- `DOC-NHS-004`: Asthma
- `DOC-NHS-005`: Burns and scalds
- `DOC-NHS-006`: Cuts and grazes
- `DOC-NHS-007`: Dehydration
- `DOC-NHS-008`: Diarrhoea and vomiting
- `DOC-NHS-009`: Headaches
- `DOC-NHS-010`: High temperature (fever) in children
- `DOC-NHS-011`: Anaphylaxis

### Distinctness Audit Findings:
- **Source ID Overlap**: **0%** (Intersection: \(\emptyset\)).
- **Topic Overlap**: **0%** (All 8 topics are medical domains completely absent from the original 3 documents).
- **Query Overlap**: None of the original 103 benchmark queries map to or target any of the 8 new documents.

---

## 4. Benchmark Leakage & Generalization Analysis

### Leakage Risks Identified in Prior Gates:
1. **Semantic Clustering**: In the 103-query benchmark, 80 queries mapped to only 3 source documents, causing dense retrieval to appear artificially strong because candidate targets were clustered.
2. **Template Leakage**: Writing queries using identical sentence patterns (e.g. repeated translation templates) artificially inflates zero-shot claims.
3. **Threshold Tuning Leakage**: Gate 5.6 exposed that tuning confidence thresholds on the whole dataset caused catastrophic failure on held-out data.

### Mitigation in Gate 5.8 Benchmark Design:
1. **Source-Level Holdout Split**:
   - The 8 documents are partitioned into two strictly isolated subsets:
     - **Development / Calibration Set (4 Sources)**:
       - `DOC-NHS-004` (Asthma)
       - `DOC-NHS-005` (Burns and scalds)
       - `DOC-NHS-006` (Cuts and grazes)
       - `DOC-NHS-007` (Dehydration)
     - **Locked Holdout Test Set (4 Sources — Strictly Unseen)**:
       - `DOC-NHS-008` (Diarrhoea and vomiting)
       - `DOC-NHS-009` (Headaches)
       - `DOC-NHS-010` (High temperature in children)
       - `DOC-NHS-011` (Anaphylaxis)
2. **Multi-Linguistic Diversity**:
   - Benchmark authoring explicitly includes 6 distinct query distributions:
     - Native Bangla (বাংলা লিপি)
     - Standard English
     - Standard Banglish (phonetic Latin transliteration)
     - Colloquial / Abbreviated Banglish (informal clinical slang, typos, colloquialisms)
     - Hard Negatives (symptom queries that share medical keywords but have NO ground truth support in the corpus)
     - Out-of-Corpus Queries (unrelated medical conditions like rabies, malaria, dental abscess)
3. **Test Set Freezing**:
   - The complete benchmark JSON will be saved, SHA-256 hashed, and locked before executing any retrieval or calibration code.

---

## 5. VERIFIED EVIDENCE vs ENGINEERING INTERPRETATION vs UNKNOWN

### VERIFIED_EVIDENCE
- Physical files for the 8 corrected documents and 91 Candidate A V2 chunks exist and match recorded SHA-256 hashes.
- Zero source ID or document text overlap exists between the 8 new documents and the original 3 NHS documents.
- Real model inference dependencies (`torch 2.11.0+cpu`, `sentence-transformers 6.0.0`, `transformers 5.15.1`) are operational.

### ENGINEERING_INTERPRETATION
- Evaluating the model on 4 entirely unseen medical documents (`DOC-NHS-008` to `DOC-NHS-011`) provides a true empirical measure of source-level holdout generalization.
- Comparing Candidate A V2 (91 chunks) against Baseline Fixed (63 chunks) under identical queries will isolate the pure retrieval impact of structural boundary chunking.

### UNKNOWN
- Whether dense embeddings (`intfloat/multilingual-e5-small`) perform better on shorter structural chunks (mean 408 chars) or larger sliding-window chunks (mean 762 chars).
- Whether cross-encoder reranking (`BAAI/bge-reranker-v2-m3`) exhibits reranking degradation or "CPR-style" bias on the new medical domains.

---

## 6. Preflight Conclusion

The preflight audit confirms that all prerequisite corpus artifacts are verified, isolated, and distinct. The project is authorized to proceed to benchmark authoring, freezing, and empirical retrieval evaluation.

---
**ABSOLUTE BOUNDARY**: Preflight audit complete. No embeddings or retrieval metrics were simulated. Proceeding to benchmark generation.
