# Phase 6F Decision Record — Grounded Generation Evaluation & Evidence-Gating Validation

**Date:** 2026-08-29  
**Decision ID:** DECISION-6F-001  
**Status:** `GROUNDING_EVALUATION_COMPLETED`  
**Application Version:** `0.7.0-prototype`  
**Active Corpus:** 119 chunks across 14 NHS conditions (`DOC-NHS-004` through `DOC-NHS-017`)  
**Retrieval Candidate:** Frozen Strategy 5 Dual-Anchor Reranker (SHA-256: `1cc216db046264d52bb05616e20123c71b77b56623b17a14c018d0e743ad86ae`)  
**Evaluation Set:** `DEVELOPMENT_GROUNDING_EVAL_SET_48` (SHA-256: `c4603199028cb649617b59d2523bb1a64b92876ffcc899285a946e940257ee61`)

---

## 1. Context & Motivation

Following the controlled smoke validation of Phase 6E, Phase 6F conducted a comprehensive development-only evaluation of the complete retrieval $\to$ gating $\to$ prompt $\to$ generation $\to$ validation $\to$ citation pipeline across 48 human-authored test cases.

The principal decision in this phase was selecting the **Evidence-Gating Policy** governing when the application should allow LLM inference versus executing a deterministic engineering-layer refusal.

---

## 2. Policy Evaluation & Selection Record

We evaluated three candidate evidence-gating policies:

1. **Policy A (Ungated Generation):**  
   Always invokes LLM.  
   *Finding:* Suffers from hallucination vulnerability on out-of-corpus medical queries (e.g. EVAL-32 typhoid antibiotics) and incurs unnecessary token costs on ungroundable queries. **Rejected**.

2. **Policy B (Strict Gating — $\text{score} \ge 0.65$ only):**  
   Permits generation only for `SUPPORTED_RETRIEVAL`.  
   *Finding:* While 100% free of hallucinations, it over-prunes valid queries (blocking 56.25% of supported queries that have moderate/low scores due to transliteration). **Rejected as overly aggressive**.

3. **Policy C (Adaptive Gating — $\text{score} \ge 0.35$):**  
   Permits generation for `SUPPORTED_RETRIEVAL` ($\ge 0.65$) and `LOW_CONFIDENCE_RETRIEVAL` ($\ge 0.35$ with cautionary prompt constraint); blocks `POSSIBLE_MISMATCH` ($<0.35$), `UNSUPPORTED_BY_ACTIVE_CORPUS` ($<0.18$), and `NO_RELEVANT_EVIDENCE`.  
   *Finding:* Successfully eliminates out-of-corpus hallucinations while allowing safely grounded responses for moderate-confidence inquiries. **Selected as Default Architectural Policy**.

---

## 3. Status Classification & Boundaries

### A. VERIFIED (Tested & Enforced)
- **Zero Fabricated Citations:** 100.0% of citation tags parsed matched active evidence chunk IDs.
- **Citation Validity Rate:** 100.0% across all 48 test cases.
- **Corpus & Benchmark Hash Integrity:**
  - Active Corpus Manifest (`44d0602f...`) intact.
  - Gate 5.28 Locked Benchmark (`464612e7...`) intact and unexecuted.
  - Strategy 5 Frozen Candidate (`1cc216db...`) intact.
- **Automated Test Suite:** 32/32 tests passing offline in Pytest.
- **Frontend Build:** 0 TypeScript / Vite compilation errors.

### B. OBSERVED (Empirical Benchmark Behaviors)
- **Direct Claim Support Rate:** 79.17% (38/48 cases).
- **Partially Supported Rate:** 14.58% (7/48 cases).
- **Unsupported Claim Rate:** 6.25% (3/48 cases, eliminated under Policy C).
- **Average Inference Latency:** 2918.7 ms per response.

### C. NOT VALIDATED / CLINICAL REVIEW REQUIRED
- **Clinical Safety:** Emergency triage statements, first-aid instructions, and medical advice texts are experimental engineering artifacts and have not undergone formal clinical evaluation.
- **Safety Tiers & Score Boundaries:** Outcome thresholds ($0.65$, $0.35$, $0.18$, $0.10$) are engineering heuristics, not validated clinical cutoffs.

### D. BLOCKED (Security Boundary)
- **Default Disabled Generation:** `GENERATION_ENABLED = False` remains strictly enforced in `config.py`. Public deployment of live generation remains blocked pending clinical validation.

---

## 4. Acceptance Criteria Checklist

- [x] Repository audit completed across all 7 backend services and schemas
- [x] 48-case human-authored development evaluation set created and documented
- [x] Grounding labels and expected factual basis predefined before evaluation
- [x] 3 evidence-gating policies (Policy A, Policy B, Policy C) compared
- [x] Real LLM inference executed across all 48 benchmark cases
- [x] Output validator executed on all outputs (100% validity, 0 fabricated tags)
- [x] Grounding metrics calculated across all categories
- [x] Multilingual breakdown reported for ENG, BN, BGL, ABB
- [x] Safety-sensitive behaviors (emergency front-loading, remedy rejection) audited
- [x] Failure taxonomy classified for all cases
- [x] Policy C selected as recommended architectural policy
- [x] Offline unit tests added (32/32 passing in Pytest)
- [x] Frontend build clean (0 errors)
- [x] Research integrity verified (all SHA-256 hashes matched)
- [x] Zero API keys or secrets stored in repository or artifacts

---

## 5. Final Classification

```
GROUNDING_EVALUATION_COMPLETED
```

---

## 6. Stop Condition Notice

Phase 6F is complete. All 48 development evaluation cases have been evaluated across all 3 gating policies. All 32 automated tests pass offline. Generation remains default-disabled in application configuration. We now **STOP and await independent review**.
