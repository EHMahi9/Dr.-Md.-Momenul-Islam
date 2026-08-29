# Phase 6D Decision Record — Grounded Generation Architecture Design

**Date:** 2026-08-29  
**Decision ID:** DECISION-6D-001  
**Status:** `GROUNDED_GENERATION_ARCHITECTURE_DESIGNED`  
**Application Version:** `0.7.0-prototype`  
**Corpus State:** 119 active chunks across 14 NHS conditions (DOC-NHS-004 through DOC-NHS-017)  
**Retrieval Candidate:** Frozen Strategy 5 Dual-Anchor Reranker (SHA-256: `1cc216db046264d52bb05616e20123c71b77b56623b17a14c018d0e743ad86ae`)

---

## 1. Context & Motivation

Following the successful controlled promotion of six validated NHS sources in Phase 6C, the active application corpus expanded from 68 to 119 chunks. The retrieval pipeline (Strategy 5) and retrieval error handling (Phase 6B) are fully stable and verified.

The goal of Phase 6D was to design the end-to-end architecture and software abstractions for a future grounded LLM generation layer without enabling live generation, connecting an external model, adding API keys, or modifying retrieval algorithms or research benchmarks.

---

## 2. Status Classification & Maturity Boundaries

To maintain rigorous research integrity, all components of the generation subsystem are explicitly partitioned:

### A. VERIFIED (Tested & Operational)
- **Active NHS Corpus:** 119 chunks, 14 clinical sources, 100% hash-verified provenance under OGL v3.0.
- **Retrieval Engine:** Frozen Strategy 5 (E5 Small Dense Top-15 $\rightarrow$ BGE Cross-Encoder Reranker $\rightarrow$ 0.85x Overview Debiasing $\rightarrow$ Dual-Anchor Fusion).
- **Outcome Classification:** Deterministic 6-state heuristic outcome assignment based on fused score distributions.
- **FastAPI Endpoints:** `/health`, `/corpus`, `/retrieve`, and `/chat` with input validation and error masking.
- **Test Suite:** 24/24 unit and integration tests passing in Pytest.
- **Frontend Build:** TypeScript + Vite build passing with 0 errors.

### B. DESIGNED & CODE-SCAFFOLDED (Interface & Contracts Complete)
- **`BaseGenerationService` & `GroundedGenerationService`:** Primary service abstraction in `backend/app/services/generation_service.py`.
- **`BaseLLMProvider` & `DisabledLLMProvider`:** Vendor-agnostic provider layer in `backend/app/services/llm_provider.py`.
- **`PromptBuilder`:** 5-section structured prompt builder with safety guardrails in `backend/app/services/prompt_builder.py`.
- **`OutputValidator`:** Deterministic post-generation citation and safety red-flag validator in `backend/app/services/output_validator.py`.
- **`GenerationResult` & `CitationReference`:** Pydantic schemas in `backend/app/schemas/generation_models.py`.
- **Frontend Generation States:** State-aware rendering in `ChatMessageItem.tsx` and `types/index.ts`.

### C. NOT YET IMPLEMENTED (Deferred to Future Build Gates)
- **Live Provider Integrations:** Google Gemini API, OpenAI API, Anthropic API, or local Ollama connectors.
- **API Secret Keys:** No external API keys stored or loaded.
- **LLM-Based Evaluation Judges:** Semantic entailment or automated medical accuracy judges.

### D. NOT YET VALIDATED (Awaiting Formal Clinical Review)
- **Safety Routing Classifier:** The 8 safety states and emergency keywords are engineering heuristics requiring clinical evaluation.
- **Score-State Thresholds:** Retrieval score boundaries ($0.65, 0.35, 0.18, 0.10$) are engineering heuristics, NOT medically validated safety limits.

---

## 3. Grounded Prompt Contract Summary

The prompt architecture strictly partitions generation inputs into 5 distinct blocks:
1. **System Instructions:** Exclusive grounding in retrieved NHS text, no medical hallucination, no doctor persona, no direct prescribing, explicit acknowledgment of uncertainty.
2. **Safety & Triage Instructions:** Immediate front-loading of emergency advice for red-flag symptoms.
3. **Source Metadata:** Information on active corpus licensing and provenance.
4. **Retrieved Clinical Evidence:** Structured numbered excerpts (`[1]..[N]`) with Chunk ID and source URL.
5. **User Inquiry:** Normalized query text.

---

## 4. Citation Traceability Contract

The system enforces a strictly verifiable link:
$$\text{Claim in Answer} \longrightarrow \text{Citation Tag [i]} \longrightarrow \text{Retrieved Chunk ID} \longrightarrow \text{Parent Source ID} \longrightarrow \text{Official NHS URL}$$

Any citation tag in the generated text that references an index not present in the retrieved passages ($i < 1$ or $i > N$) is detected and flagged by the deterministic `OutputValidator` as a fabricated citation.

---

## 5. Security & Configuration Standards

- `GENERATION_ENABLED: bool = False` remains strictly enforced in `backend/app/core/config.py`.
- Model credentials must be supplied via environment variables (`LLM_API_KEY_ENV_VAR`), never hardcoded.
- Default timeouts (30s) and retry limits (2) are enforced.
- Raw chain-of-thought traces are never exposed in user-facing schemas.

---

## 6. Acceptance Criteria Checklist

- [x] Grounded generation architecture documented (`docs/architecture/phase-6D-grounded-generation.md`)
- [x] `GenerationService` interface defined (`backend/app/services/generation_service.py`)
- [x] `LLMProvider` interface defined (`backend/app/services/llm_provider.py`)
- [x] Evidence contract defined (`GroundingEvidence` in `generation_models.py`)
- [x] `GenerationResult` schema defined (`backend/app/schemas/generation_models.py`)
- [x] Citation contract defined (`CitationReference` in `generation_models.py`)
- [x] No-evidence behavior designed and mapped to state transitions
- [x] Safety routing states designed (`GenerationSafetyState`)
- [x] Post-generation validation architecture implemented (`backend/app/services/output_validator.py`)
- [x] Provider configuration designed in `backend/app/core/config.py`
- [x] Secret handling designed via runtime environment variable lookup
- [x] `generation_enabled` remains `False`
- [x] Existing retrieval application functions without modification
- [x] Existing and new tests pass (24/24 in Pytest)
- [x] Frontend builds cleanly (TypeScript & Vite build: 0 errors)
- [x] No external LLM was called
- [x] No research benchmark was modified or rerun
- [x] No retrieval algorithm or Strategy 5 parameters were changed

---

## 7. Final Classification

```
GROUNDED_GENERATION_ARCHITECTURE_DESIGNED
```

---

## 8. Stop Condition Notice

Phase 6D is complete. No external LLMs are connected, generation remains disabled, and all retrieval configurations remain frozen. We now **STOP and await independent review** before proceeding to any real LLM integration.
