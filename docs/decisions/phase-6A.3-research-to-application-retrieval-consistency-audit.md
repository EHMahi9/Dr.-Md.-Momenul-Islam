# Decision Record: Phase 6A.3 — Research-to-Application Retrieval Consistency Audit

**Gate Reference:** PHASE 6A.3  
**Date:** 2026-08-28  
**Status:** `APPLICATION_RETRIEVAL_MATCHES_FROZEN_STRATEGY`  
**Classification:** RETRIEVAL CONSISTENCY & SCORE SEMANTICS AUDIT COMPLETE  

---

## 1. Executive Summary & Objective

Phase 6A.3 conducted an end-to-end consistency audit comparing the live application backend implementation against the frozen research candidate: **`STRATEGY_5_DUAL_TOPICAL_LEXICAL_ANCHOR`** (selected in Gate 5.24.1).

### Core Audit Findings:
1. **100% Parameter & Logic Parity**: The application service layer (`FrozenDualAnchorRetrievalService`) matches every parameter, model name, candidate depth, multiplier, and fusion formula in the frozen Strategy 5 configuration.
2. **Score Semantics Fully Traced**: The score displayed in the UI (e.g. `Rerank: 1.0547`) is the **Dual-Anchor Fused Score**, computed as $\text{CrossEncoderScore} + (0.10 \times \text{DenseCosine}) + (0.03 \times \text{LexicalOverlap})$.
3. **Live HTTP Smoke Tests Passed**: 3 multi-lingual queries (English, Native Bangla, and Banglish) executed against the live running server returned HTTP 200, valid Top-5 evidence passages, and enforced `generation_enabled = false`.

---

## 2. Full Application Path Trace

```text
1. Client POST /api/v1/chat (or /api/v1/retrieve)
   └─> backend/app/api/endpoints.py (chat_endpoint)
2. Service Dependency Injection
   └─> backend/app/services/retrieval_service.py (get_retrieval_service)
3. Step 1: Unicode-Safe Query Normalization
   └─> normalize_query_track_a(query) [9 concept regex dictionaries]
4. Step 2: Bi-Encoder Dense Candidate Generation (Top-15)
   └─> intfloat/multilingual-e5-small (query prefix: "query: ") -> cosine dot product -> Top-15
5. Step 3: Cross-Encoder Neural Reranking
   └─> BAAI/bge-reranker-v2-m3 -> raw pairwise logit predictions
6. Step 4: Overview Debiasing
   └─> 0.85x score multiplier applied strictly to chunks ending in "-HYB-000"
7. Step 5: Dual-Anchor Semantic-Lexical Fusion
   └─> final_score = rerank_score + (0.10 * dense_cosine) + (0.03 * token_overlap)
8. Step 6: Top-5 Context Assembly
   └─> Top-5 sorted evidence chunks returned with NHS provenance metadata
9. Step 7: Generation Layer (Safety Enforced)
   └─> backend/app/services/generation_service.py (DisabledGenerationService: generation_enabled = false)
10. UI Rendering
   └─> frontend/src/components/EvidenceCard.tsx + Header banner disclaimer
```

---

## 3. Parameter Comparison Matrix

| Component / Parameter | Frozen Strategy 5 Candidate | Application Backend (`config.py` / `retrieval_service.py`) | Audit Status |
|---|---|---|---|
| **Dense Bi-Encoder Model** | `intfloat/multilingual-e5-small` | `intfloat/multilingual-e5-small` | ✅ **PERFECT MATCH** |
| **Dense Candidate Depth ($K$)** | `15` | `15` | ✅ **PERFECT MATCH** |
| **Cross-Encoder Model** | `BAAI/bge-reranker-v2-m3` | `BAAI/bge-reranker-v2-m3` | ✅ **PERFECT MATCH** |
| **Overview Debiasing Multiplier** | `0.85x` (on `-HYB-000`) | `0.85x` (on `-HYB-000`) | ✅ **PERFECT MATCH** |
| **Dense Fusion Weight ($\lambda$)** | `0.10` | `0.10` | ✅ **PERFECT MATCH** |
| **Lexical Overlap Weight ($\alpha$)** | `0.03` | `0.03` | ✅ **PERFECT MATCH** |
| **Normalization Dictionaries** | Track A (9 Concept Dictionaries) | Track A (9 Regex Rules) | ✅ **PERFECT MATCH** |
| **Final Context Top-$K$** | `5` | `5` | ✅ **PERFECT MATCH** |

---

## 4. Score Semantics Audit (Tracing the `1.0547` Value)

The UI displays the fused retrieval score in the evidence metadata strip. For the English query *"How to treat a minor burn with cool running water?"*, the top chunk (`DOC-NHS-005-HYB-001`) receives a score of **`1.0547`**.

### Mathematical Decomposition:
1. **Raw Cross-Encoder Score** ($\text{BGE-v2-m3}$): $\approx 0.9575$
2. **Dense Cosine Contribution** ($\lambda \times \text{E5\_cosine} = 0.10 \times 0.8820$): $+0.0882$
3. **Lexical Overlap Contribution** ($\alpha \times \text{Overlap} = 0.03 \times 0.3000$): $+0.0090$
4. **Fused Dual-Anchor Score**: $0.9575 + 0.0882 + 0.0090 = \mathbf{1.0547}$

> [!NOTE]
> **Interpretation:**
> The fused score is a composite ranking utility metric, not an uncalibrated probability. Scores exceeding $1.00$ are mathematically expected for high-confidence passages with simultaneous cross-encoder, dense embedding, and lexical overlap alignment.

---

## 5. Live HTTP Smoke Test Results & Clinical Relevance Breakdown

All 3 smoke-test queries executed successfully at the runtime/protocol level, but displayed distinct clinical retrieval outcomes:

| Query ID | Language | Query Text | HTTP Status | Top-1 Chunk ID & Source | Fused Score | Runtime Verdict | Clinical Relevance Verdict |
|---|---|---|---|---|---|---|---|
| `SMOKE-EN-01` | English | *"How to treat a minor burn with cool running water?"* | `200 OK` | `DOC-NHS-005-HYB-001` (Burns and scalds) | **1.0547** | ✅ **PASS** | ✅ **RELEVANT** (Exact clinical match) |
| `SMOKE-BN-01` | Native Bangla | *"বাচ্চার জ্বর হলে কখন ডাক্তার দেখাতে হবে?"* | `200 OK` | `DOC-NHS-004-HYB-002` (Asthma) | **0.2902** | ✅ **PASS** | ⚠️ **MISDIRECTION** (Pediatric Distraction Defect) |
| `SMOKE-BG-01` | Banglish | *"tetanus injection kobe lagbe kata hole?"* | `200 OK` | `DOC-NHS-006-HYB-006` (Cuts and grazes) | **0.0968** | ✅ **PASS** | ✅ **RELEVANT** (Plausible cuts/tetanus match) |

*Generation Enforcement Check:* `generation_enabled = false` in 100% of responses.

### Critical Diagnostic: Why did the Native Bangla Fever Query land on Asthma?
1. **Query Semantics:** *"বাচ্চার জ্বর হলে কখন ডাক্তার দেখাতে হবে?"* translates to *"When should I see a doctor if my child has a fever?"*.
2. **Pediatric GP Urgency Latching:** `DOC-NHS-004-HYB-002` contains repeated non-urgent triage guidance: *"See a GP if: you or your child have asthma symptoms... you or your child have asthma and treatments are not helping..."*.
3. **Root Cause:** The neural cross-encoder and dense embedding heavily weighted the *"See a GP if you or your child"* triage pattern in `DOC-NHS-004-HYB-002` over `DOC-NHS-010` (Fever in children).
4. **Key Finding:** This proves that while **implementation logic matches Strategy 5 100%**, Strategy 5 remains an unvalidated development candidate exhibiting known cross-lingual triage distraction failure modes.

---

## 6. Corpus Lifecycle & Separation Architecture

The application currently displays:
> **Corpus: 68 Chunks (NHS)**

This is **by design and architectural intention**:
- **Current Active App Corpus:** Bound strictly to the **68-chunk baseline research corpus** (`DOC-NHS-004` to `DOC-NHS-011`).
- **Gate 5.27 Ingested Corpus:** Contains **51 new chunks** across 6 new NHS documents (`DOC-NHS-012` to `DOC-NHS-017`), residing strictly in `research/gate_5_27_ingestion/`.
- **Isolation Policy:** New documents will **NOT** be activated in the product backend until they undergo formal benchmark creation (Gate 5.28) and single-shot frozen validation (Gate 5.29).

---

## 7. Final Classification

1. **Implementation & Parameter Match:** ✅ **`APPLICATION_RETRIEVAL_MATCHES_FROZEN_STRATEGY` (PASS)**
2. **Runtime Integration:** ✅ **`RUNTIME_HTTP_INTEGRATION_PASS`**
3. **Retrieval Relevance:** ⚠️ **`RETRIEVAL_RELEVANCE_PARTIAL (1/3 MISDIRECTION ON NATIVE BANGLA)`**

