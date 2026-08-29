# Decision Record: Phase 6B — Product Hardening & Retrieval Error Handling

**Phase Reference:** PHASE 6B  
**Date:** 2026-08-29  
**Status:** `PRODUCT_HARDENING_COMPLETE`  
**Classification:** PRODUCT ARCHITECTURE, ERROR HANDLING & UX HARDENING  

---

## 1. Executive Summary

Phase 6B transitions the validated retrieval engine (`STRATEGY_5_DUAL_TOPICAL_LEXICAL_ANCHOR`) into a resilient, transparent, and structured application foundation without altering the frozen research configuration.

### What Was Accomplished:
1. **Configuration Lineage Reconciled:** Clarified that `07f031da...` represented the pre-fusion Strategy 2 baseline, while `1cc216db...` is the authoritative cryptographic digest of Strategy 5 (`strategy_5_dev_candidate_configuration.json`).
2. **Retrieval Outcome State Machine Implemented:** Deterministic 6-tier classification (`SUPPORTED_RETRIEVAL`, `LOW_CONFIDENCE_RETRIEVAL`, `POSSIBLE_MISMATCH`, `UNSUPPORTED_BY_ACTIVE_CORPUS`, `NO_RELEVANT_EVIDENCE`, `INVALID_QUERY`).
3. **Backend Error Hardening:** Input length & whitespace validation, error masking (zero stack trace leakage), structured HTTP error responses, and server-side logging.
4. **Frontend UX Overhaul:** Clear visual outcome badges, patient-friendly clinical excerpt cards with collapsible research observability, prominent NHS provenance links, in-flight loading skeletons, and helpful error guidance.
5. **Multi-Tier Corpus Safety:** Maintained strict isolation of staged research documents (`DOC-NHS-012`..`017`) from active application retrieval.
6. **Automated Testing:** 14 automated backend unit/integration tests passing (100%), and clean TypeScript production build.

---

## 2. Evidence Status & Boundaries

| Category | Item | Status / Detail |
|---|---|---|
| **VERIFIED** | Strategy 5 Configuration Identity | `1cc216db046264d52bb05616e20123c71b77b56623b17a14c018d0e743ad86ae` |
| **VERIFIED** | Active Corpus Size | Exactly 68 chunks (`DOC-NHS-004` to `DOC-NHS-011`) |
| **VERIFIED** | Staged Corpus Isolation | Staged chunks have 0% presence in `/retrieve` and `/chat` |
| **VERIFIED** | Backend Tests | 14 / 14 pytest unit tests passing |
| **VERIFIED** | Frontend Build | `tsc && vite build` completed in 1m 21s with 0 errors |
| **VERIFIED** | Generation Status | Strictly disabled by protocol (`generation_enabled: false`) |
| **OBSERVED** | Outcome Classification | Correctly tags high-confidence vs ungrounded/low-scoring queries |
| **DESIGNED** | Pre-Generation Safety Gate | Structural boundary ready for future LLM integration |
| **NOT YET VALIDATED** | Clinical Safety | **NOT a medical device. Research prototype only.** |

---

## 3. Parametric Parity Guarantee (Zero Algorithm Drift)

> [!IMPORTANT]
> **Zero Changes to Strategy 5 Retrieval:**
> - Bi-Encoder: `intfloat/multilingual-e5-small` ($K=15$)
> - Cross-Encoder: `BAAI/bge-reranker-v2-m3`
> - Overview Debiasing: $0.85\times$ on `-HYB-000`
> - Dual-Anchor Fusion: $\text{FinalScore} = \text{Rerank} + 0.10 \times \text{Dense} + 0.03 \times \text{LexicalOverlap}$
> - Context Top-$K$: 5
> - Normalization: Track A Unicode-Safe Procedural Normalization (9 concept dictionaries)

---

## 4. Final Status

$$\mathbf{PRODUCT\_HARDENING\_COMPLETE}$$
