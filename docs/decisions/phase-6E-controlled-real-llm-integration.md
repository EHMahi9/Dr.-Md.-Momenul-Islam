# Phase 6E Decision Record — Controlled Real LLM Integration & Smoke Validation

**Date:** 2026-08-29  
**Decision ID:** DECISION-6E-001  
**Status:** `REAL_LLM_INTEGRATED_SMOKE_VALIDATED`  
**Application Version:** `0.7.0-prototype`  
**Corpus State:** 119 active chunks across 14 NHS conditions (DOC-NHS-004 through DOC-NHS-017)  
**Retrieval Candidate:** Frozen Strategy 5 Dual-Anchor Reranker (SHA-256: `1cc216db046264d52bb05616e20123c71b77b56623b17a14c018d0e743ad86ae`)

---

## 1. Context & Motivation

Phase 6D established the software architecture and interfaces for grounded generation (`BaseGenerationService`, `BaseLLMProvider`, `PromptBuilder`, `OutputValidator`).

Phase 6E executed the **first controlled real-LLM integration** to evaluate whether real models can follow the 5-section prompt contract, maintain factual grounding against the active 119-chunk NHS corpus, produce verifiable citations, and respond appropriately across English, native Bengali (বাংলা), and Banglish queries.

---

## 2. Status Classification & Maturity Boundaries

### A. VERIFIED (Deterministic & Tested)
- **Active Corpus Manifest (119 chunks):** SHA-256 `44d0602f730d6460e6fefa431bd5c09005b48ce92b47d02832532e5868d4aa58` (100% intact).
- **Gate 5.28 Locked Benchmark:** SHA-256 `464612e733aeb1496c1dcdc5674e01d9504bd4ccd1244190e487c6e957dcc722` (100% intact).
- **Frozen Strategy 5 Retrieval:** Multilingual-E5-small + BGE-reranker-v2-m3 candidate (`1cc216db...`).
- **OpenAI-Compatible Provider:** Successfully connects to live inference endpoint (`qwen3.6-35b-a3b`), handles timeouts, retries, and token accounting.
- **Output Validator:** Verified 8/8 smoke test responses, mapped 100% of citation tags to retrieved chunks, detected 0 fabricated citations.
- **Automated Test Suite:** 27/27 tests passing in Pytest (including provider offline mock tests).
- **Frontend Build:** TypeScript + Vite build clean (0 errors).

### B. OBSERVED (Empirical Smoke Observations — Not Benchmark Metrics)
- **Linguistic Quality:** Bengali responses preserved natural phrasing and accurate medical terminology.
- **Abstention Discipline:** Model explicitly abstained from answering when queries were outside the active 14 conditions.
- **Emergency Triage:** Emergency advice was successfully front-loaded for red-flag chest pain symptoms.

### C. NOT VALIDATED (Awaiting Formal Clinical Review)
- **Medical Safety:** Emergency guidance and first-aid recommendations are experimental engineering prototypes and must not be used for clinical decision-making.
- **Safety Classifier Thresholds:** Score tiers and intent categories are engineering heuristics.

### D. BLOCKED (Security Boundary)
- **Default Disabled Generation:** `GENERATION_ENABLED = False` is enforced in `config.py`. Public deployment of live generation remains blocked pending clinical validation.

---

## 3. Acceptance Criteria Checklist

- [x] Provider selection inspected and validated (`OpenAICompatibleProvider` via `LIBERTAI_API_KEY`)
- [x] Secrets managed exclusively through environment variables (zero hardcoded keys)
- [x] Generation remains disabled by default in application configuration
- [x] Provider abstraction layer implemented behind `BaseLLMProvider`
- [x] Grounded prompt contract assembled with 5 sections
- [x] 8 controlled smoke tests executed and recorded
- [x] Output validator executed on all real LLM outputs (100% pass rate)
- [x] Claim support audited (100% directly supported claims)
- [x] No-evidence and out-of-corpus behavior evaluated
- [x] Language behavior in Bengali and Banglish observed
- [x] Latency and token usage recorded
- [x] Frontend build succeeds with zero errors
- [x] Automated backend tests pass (27/27 in Pytest)
- [x] Research integrity verified (Gate 5.28 benchmark & corpus manifest hashes match)
- [x] No benchmark data or retrieval algorithms modified

---

## 4. Final Classification

```
REAL_LLM_INTEGRATED_SMOKE_VALIDATED
```

---

## 5. Stop Condition Notice

Phase 6E is complete. All 8 smoke validation queries executed with 100% citation validity and factual support. Generation remains disabled by default in the application configuration. We now **STOP and await independent review** before proceeding to any further generation evaluation gates.
