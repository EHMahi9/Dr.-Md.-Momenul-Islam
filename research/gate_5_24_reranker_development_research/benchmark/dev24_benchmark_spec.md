# DEV-24 Benchmark Specification

## 1. Overview
The **DEV-24 Benchmark** is a specialized development dataset constructed in Gate 5.24 to investigate fine-grained cross-encoder evidence-selection behavior and intra-document section competition.

- **File**: [`research/gate_5_24_reranker_development_research/benchmark/dev24_benchmark.json`](file:///d:/my-ai-project/Dr.%20Md.%20Momenul%20Islam/research/gate_5_24_reranker_development_research/benchmark/dev24_benchmark.json)
- **Benchmark SHA-256**: `4d28ccfc59be69e2e790fb89ad71fc47479e8d92889c61a069d0af238750e485`
- **Total Queries**: 40 supported queries (5 per document across all 8 documents)
- **Overlap**: **0 duplicate or near-duplicate queries** with the 150 previously used queries across Gates 5.8 to 5.23.

---

## 2. Design Objective: Intra-Document Section Discrimination
Unlike topic-level retrieval, queries in DEV-24 are authored to test whether the reranker can discriminate subtle, adjacent sections within the **same source document**:
- Diagnosis criteria vs. urgent treatment vs. emergency escalation (`DOC-NHS-004`)
- Topical burn soothing creams vs. healing time vs. ice contraindication (`DOC-NHS-005`)
- Stitches/glue clinical treatments vs. dressing changes vs. secondary bleeding pressure (`DOC-NHS-006`)
- Fluid choices vs. elderly hydration techniques vs. infant nappy count (`DOC-NHS-007`)
- Swimming pool viral quarantine vs. coffee-ground vomit vs. small fluid sips (`DOC-NHS-008`)
- Eye strain triggers vs. stroke/neurological emergencies vs. natural headache resolution (`DOC-NHS-009`)
- Photophobia emergency vs. 3-6 month fever thresholds vs. breastfeeding continuation (`DOC-NHS-010`)
- Pregnancy positioning vs. needleless trainer injector use vs. 999 ambulance phrasing (`DOC-NHS-011`)

---

## 3. Language & Split Breakdown
- **English**: 16 queries
- **Native Bangla**: 8 queries
- **Standard Banglish**: 8 queries
- **Abbreviated Banglish**: 8 queries
- **Total**: 40 queries
