# Architecture Specification: Phase 6B — Product Hardening & Retrieval Error Handling

**Phase Reference:** PHASE 6B  
**Date:** 2026-08-29  
**Status:** `IMPLEMENTED`  
**Classification:** PRODUCT ARCHITECTURE & RETRIEVAL ERROR HANDLING SPECIFICATION  

---

## 1. System Overview & Component Boundaries

Phase 6B transforms the research prototype into an architecturally robust, typed, and failure-tolerant retrieval product foundation.

```text
   +-------------------------------------------------------------------------+
   |                       REACT + TYPESCRIPT FRONTEND                       |
   |  • Header with Multi-Tier Status Badges (Active: 68, Staged: 51, Gen: Off)|
   |  • Multilingual Chat / Query Input (Enter handling, throttling)         |
   |  • Categorized Outcome Badges (🟢 Supported, 🟡 Low Conf, 🟠 Mismatch)  |
   |  • Readable Clinical Evidence Cards + Expandable Research Observability |
   |  • Explicit "Source: NHS (Active Corpus)" Provenance & Licensing        |
   |  • Structured Non-Clinical Error Banners (Offline, 400, 500, Retry)     |
   +-------------------------------------------------------------------------+
                                      │  HTTP / REST (Pydantic Typed Contracts)
                                      ▼
   +-------------------------------------------------------------------------+
   |                             FASTAPI BACKEND                             |
   |                                                                         |
   |  [/api/v1/health]        [/api/v1/corpus]          [/api/v1/retrieve]   |
   |  Status & Hashes         Lifecycle Tiers           Evidence Retrieval  |
   |                                                                         |
   |  [/api/v1/chat]                                                         |
   |  Structured Chat Endpoint (Retrieval-Only Research Prototype Mode)      |
   +-------------------------------------------------------------------------+
                                      │
               ┌──────────────────────┴──────────────────────┐
               ▼                                             ▼
   +---------------------------------------+   +-----------------------------+
   |         BASE RETRIEVAL SERVICE        |   |   BASE GENERATION SERVICE   |
   |  [FrozenDualAnchorRetrievalService]   |   | [DisabledGenerationService] |
   |  1. Input Length & Whitespace Validate|   |  - generation_enabled: false|
   |  2. Track A Normalization (9 dicts)   |   |  - Static Research Notice   |
   |  3. Dense Top-15 (multilingual-e5)    |   +-----------------------------+
   |  4. Cross-Encoder (bge-reranker-v2-m3)|                 │
   |  5. 0.85x Overview Debiasing          |                 ▼
   |  6. Dual Anchor Score Fusion          |   [FUTURE SAFETY GATE BOUNDARY]
   |     (score + 0.10*dense + 0.03*overlap|   (Terminates before LLM call)
   |  7. Deterministic Outcome Classifier  |
   +---------------------------------------+
                       │
                       ▼
   +-------------------------------------------------------------------------+
   |                       THREE-TIER CORPUS LIFECYCLE                       |
   |  1. ACTIVE CORPUS:          68 chunks (DOC-NHS-004..011) [LIVE]         |
   |  2. STAGED RESEARCH CORPUS: 51 chunks (DOC-NHS-012..017) [ISOLATED]     |
   |  3. VALIDATED CORPUS:       0 chunks (Pending Gate 5.29) [NOT ACTIVE]   |
   +-------------------------------------------------------------------------+
```

---

## 2. Deterministic Retrieval Outcome State Machine

To prevent treating all retrieval results as equally authoritative, Phase 6B establishes an explicit classification state machine:

| Outcome State | Confidence Tier | Fused Score Boundary | Clinical & Operational Meaning | Frontend Representation |
|---|---|---|---|---|
| **`SUPPORTED_RETRIEVAL`** | `HIGH` | $S_{\text{top}} \ge 0.65$ | Authoritative NHS evidence with strong semantic alignment retrieved. | 🟢 Green badge: *Evidence Found (High Confidence)* |
| **`LOW_CONFIDENCE_RETRIEVAL`** | `MODERATE` | $0.35 \le S_{\text{top}} < 0.65$ | Supporting evidence retrieved with moderate strength; review carefully. | 🟡 Yellow badge: *Evidence May Be Incomplete (Needs Caution)* |
| **`POSSIBLE_MISMATCH`** | `LOW` | $0.18 \le S_{\text{top}} < 0.35$ | Weak semantic match; likely general triage or a different condition. | 🟠 Orange badge: *Possible Topic Mismatch* |
| **`UNSUPPORTED_BY_ACTIVE_CORPUS`** | `VERY_LOW` | $0.10 \le S_{\text{top}} < 0.18$ | Question relates to conditions outside the 8 active NHS topics. | 🔴 Red badge: *Unsupported by Current Active Knowledge Base* |
| **`NO_RELEVANT_EVIDENCE`** | `NONE` | $S_{\text{top}} < 0.10$ | No relevant evidence found in the active corpus. | ⚪ Slate badge: *No Supporting Evidence Found* |
| **`INVALID_QUERY`** | `INVALID` | N/A | Empty, whitespace, or malformed input. | ⚠️ Client-side validation prompt |

---

## 3. Backend Response Contracts (Pydantic)

### `RetrievalResponse` Contract:
```json
{
  "status": "success",
  "outcome_state": "SUPPORTED_RETRIEVAL",
  "confidence_assessment": {
    "state": "SUPPORTED_RETRIEVAL",
    "confidence_level": "HIGH",
    "top_score": 0.8950,
    "score_spread": 0.1450,
    "summary_reason": "Authoritative clinical evidence with strong semantic alignment retrieved from active NHS corpus."
  },
  "strategy_used": "STRATEGY_5_DUAL_TOPICAL_LEXICAL_ANCHOR",
  "query_raw": "how to treat a minor burn with water",
  "query_normalized": "how to treat a minor burn with water (burns scalds cool running water first aid)",
  "evidence_count": 5,
  "evidence": [ ... ],
  "retrieval_metadata": {
    "strategy_name": "STRATEGY_5_DUAL_TOPICAL_LEXICAL_ANCHOR",
    "candidate_hash": "1cc216db046264d52bb05616e20123c71b77b56623b17a14c018d0e743ad86ae",
    "active_corpus_name": "BASELINE_NHS_8_CONDITIONS",
    "active_chunks_count": 68,
    "dense_k": 15,
    "final_top_k": 5
  }
}
```

---

## 4. Multi-Tier Corpus Isolation

- **Active Corpus (68 Chunks):** `research/gate_5_9_optimization/chunks/hybrid_600/provenance_manifest.json` (`DOC-NHS-004` to `DOC-NHS-011`).
- **Staged Research Corpus (51 Chunks):** `research/gate_5_27_ingestion/provenance_manifest.json` (`DOC-NHS-012` to `DOC-NHS-017`).
- **Isolation Guarantee:** The application retrieval service is hard-coded to initialize from `settings.CORPUS_MANIFEST_PATH`. Automated unit test `test_staged_corpus_isolation_in_retrieval` enforces that staged source IDs have **zero intersection** with active retrieval evidence.

---

## 5. Architectural Generation Safety Gate

```text
[User Query]
     │
     ▼
[Dual-Anchor Retrieval Engine]
     │
     ▼
[Deterministic Outcome Classifier]
     │
     ├── If Outcome < SUPPORTED_RETRIEVAL ──> [Return Grounding Evidence + Advisory Warning]
     │
     ▼ (Supported)
[Future Generation Gate: Strictly Disabled] ──> [Return Verbatim NHS Passages + Static Disclaimer]
```

Generation remains strictly disabled (`generation_enabled: false`). No external API keys or LLM libraries exist in the runtime path.
