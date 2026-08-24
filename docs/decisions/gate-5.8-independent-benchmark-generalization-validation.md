# Gate 5.8 — Independent Benchmark Expansion & Retrieval Generalization Validation

> **Status:** BLOCKED
> **Reason:** INSUFFICIENT_INDEPENDENT_DOCUMENT_DIVERSITY

## 1. Gate Purpose
The purpose of this gate was to create a genuinely independent evaluation dataset strictly separated from the previous 103-query benchmark, in order to independently validate the provisional `E5 -> Top-3 -> bge-reranker-v2-m3` retrieval architecture. It aimed to measure true generalization without the severe semantic clustering and leakage observed in Gate 5.7.

## 2. Prior Evidence Status
All historical metrics generated from the current 103-query benchmark are explicitly classified as:
- **E5 + Top-3 Reranker Architecture**: `PROVISIONAL_EXPERIMENTAL_BASELINE`
- **Gate 5.7 Held-out Accuracy (85%-94%)**: `VALIDATED` (but acknowledged to be highly sensitive to semantic overlap).
- **Reranker CPR / Symptom Bias**: `VALIDATED` (empirically observed on the 3-document corpus).
- **Hard-Negative Absolute Score Thresholds**: `INVALIDATED` (score distributions overlap).
- **Gate 5 / 5.1 Metrics**: `SIMULATED` (invalidated).

## 3. Existing Benchmark Audit (Part 1)
Before attempting expansion, we audited the existing corpus and artifacts:
1. **Represented Documents**: Exactly 3 documents are used: `DOC-NHS-001` (Heat Exhaustion), `DOC-NHS-002` (CPR), and `DOC-NHS-003` (Child Choking).
2. **Represented Categories**: The benchmark effectively spans `abbr_banglish`, `std_banglish`, `native_bangla`, `mixed_banglish`, `factual`, `emergency`, and `hard_negative`.
3. **Semantic Clustering**: 80 valid queries map directly to just 3 chunks. Queries heavily repeat the same underlying intents (e.g., dozens of variants asking "how to do chest compressions").
4. **Near-Duplicates**: The dataset contains extensive near-duplicate paraphrases.
5. **Limitations**: Because the corpus is only 3 documents, the cross-encoder's observed "CPR Bias" (misclassifying abbreviated Banglish symptoms) may partially be an artifact of the corpus density, as CPR represents 33% of all valid medical knowledge in the current system.

## 4. Independent Data Availability & Expansion Blocker (Part 2)
To build a strictly separated locked test set, we require new, legally approved documents that do not overlap with the existing three NHS chunks. 
An audit of `docs/knowledge/source-catalog.json` revealed:
- **Total Catalogued Sources**: 14
- **Rights Unclear (DGHS/IEDCR)**: 5 documents
- **Approved for Non-Commercial Research Only (WHO)**: 6 documents
- **Approved for Production Reuse (NHS OGL v3.0)**: 3 documents (`DOC-NHS-001`, `DOC-NHS-002`, `DOC-NHS-003`).

**Finding**: There are **zero** remaining legally approved `APPROVED_FOR_PRODUCTION_REUSE` documents in the source catalog. 

Following strict project constraints: *"If the current legally approved production corpus contains only the existing NHS documents and there are no additional already-approved documents available, STOP and report: INSUFFICIENT_INDEPENDENT_DOCUMENT_DIVERSITY. Do NOT silently expand the corpus using WHO, DGHS, IEDCR, or any rights-unclear source."*

## 5. Methodological Limitations & Proposed Requirements
Because no independent documents are legally cleared for use, we cannot fulfill Phase 3 (Strict Dataset Separation) or Phase 4 (Query Diversity) without violating legal constraints. Therefore, the independent multi-split generalization test cannot proceed.

**Benchmark-Expansion Requirements**:
To unblock this evaluation, the project must:
1. Formally discover, review, and approve additional NHS (OGL v3.0) documents for the `source-catalog.json`.
2. Target diverse new intents (e.g., Asthma, Diabetes, Fevers, Wound Care) to dilute the dense CPR/Choking semantic clusters.
3. Ingest these new documents using the Gate 4C prototype.
4. Draft new corresponding calibration, validation, and locked test queries.

## 6. Final Architecture Status
- **Final Status**: `BLOCKED` (Pending document discovery and legal clearance).
- **Current Architecture Status**: `PROVISIONAL_EXPERIMENTAL_BASELINE` remains unchanged. The `intfloat/multilingual-e5-small` → `BAAI/bge-reranker-v2-m3` architecture cannot be further validated for generalization until new approved data is ingested.

## Final Stop Point
Evaluation is blocked. No LLM generation, production integration, or safety-router architecture will be modified. All retrieval metrics remain experimental.
