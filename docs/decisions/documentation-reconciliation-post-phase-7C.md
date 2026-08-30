# Architecture Decision Record: Documentation Reconciliation Post-Phase 7C

**Status:** APPROVED  
**Date:** 2026-08-30  
**Context:** Reconciliation of project documentation following Phase 7C and correction of the living roadmap sequence for Phase 8.

---

## 1. Context & Motivation

Following the completion of Phase 7C, living project documentation required alignment to accurately reflect:
1. The validated Phase 7C adaptive clarification implementation.
2. The actual agreed execution order for Phase 8 (starting with Production Backend Deployment Preparation on Render rather than premature LLM phrasing).
3. The frozen status of Candidate B retrieval with respect to Banglish research.
4. The classification of residual irrelevant evidence exposure (16%) as a Known Open Product/UX Issue rather than a clinical validation claim.
5. The exact deployment state (Frontend deployed on Vercel; Backend currently local/research runtime).

---

## 2. Documents Inspected & Reconciled

| Document Path | Type | Action Taken | Rationale |
| :--- | :--- | :--- | :--- |
| `README.md` | Living Project Entrypoint | **UPDATED** | Reconciled Phase 8 roadmap (8A/8B/8C deployment first), Banglish frozen candidate status, open UX issue (16% irrelevant cards), and deployment boundaries. |
| `docs/architecture/application-architecture.md` | Living Architecture Spec | **UPDATED** | Synchronized with live Phase 7C conversational pipeline (Query Understanding $	o$ State $	o$ Adaptive Planner $	o$ Candidate B $	o$ Sufficiency Policy). |
| `docs/12-development-roadmap.md` | Living Roadmap Spec | **UPDATED** | Corrected Phase 8 roadmap sequence to prioritize production backend deployment (Phase 8A/8B/8C) before LLM generation (Phase 8D/8E). |
| `docs/architecture/phase-7C-adaptive-clarification.md` | Phase Architecture Doc | **PRESERVED** | Authored during Phase 7C; accurate technical spec. |
| `docs/decisions/phase-7C-adaptive-clarification.md` | Phase Decision Record | **PRESERVED** | Authored during Phase 7C; accurate decision record. |
| `docs/decisions/gate-*` & `docs/decisions/phase-6*` | Historical Decision Records | **INTENTIONALLY UNCHANGED** | Historical audit trail preserved as permanent immutable records. |

---

## 3. Reconciled Phase 8 Roadmap Sequence

The living roadmap reflects the following execution sequence:

```
COMPLETED:
  Phase 1–5: Foundation and retrieval research
  Phase 6A–6K: Corpus expansion, retrieval validation, Candidate B selection and validation
  Phase 7A: Query understanding, ambiguity detection, evidence sufficiency, emergency routing
  Phase 7B: Multi-turn clarification and structured conversation state
  Phase 7C: Adaptive clarification and question-utility planning

NEXT:
  Phase 8A: Production Backend Deployment Preparation (Linux, Render, CORS, Packaging)
  Phase 8B: Backend Deployment + Vercel ↔ Render Integration
  Phase 8C: Cloud Runtime / Performance Optimization

FUTURE:
  Phase 8D: LLM-Assisted Conversational Generation
  Phase 8E: Multi-Turn Grounded Generation Evaluation
  Later: Broader source coverage, Bangladesh guidance, privacy & clinical governance
```

---

## 4. Key Policy & Status Clarifications

1. **Banglish Development Status:**  
   Further Banglish vocabulary expansion remains future research work and must be evaluated as a separately versioned candidate. The validated Candidate B configuration remains strictly frozen.
2. **Known Open Product/UX Issue:**  
   Phase 7C reduced irrelevant evidence exposure from 40% to 16% on its development benchmark, but did not eliminate the issue. This is classified as a **KNOWN OPEN PRODUCT/UX ISSUE** under active development, not a clinical validation claim.
3. **Deployment Boundaries:**  
   - Frontend: `https://drmomenul.vercel.app` (Deployed Vercel SPA)
   - Backend: Local/research runtime (`http://localhost:8000`) until Phase 8A/8B deployment to Render is completed.
4. **Engineering vs Clinical Validation:**  
   All metrics represent engineering benchmark evaluations. The system is **NOT CLINICALLY VALIDATED**.

---

## 5. Verification of Invariants

- [x] No application source code modified (`backend/`, `frontend/`).
- [x] Candidate B retrieval parameters and weights remain strictly frozen.
- [x] Corpus chunks and SHA-256 hashes remain strictly untouched.
- [x] Benchmark datasets and evaluation results remain strictly untouched.
- [x] Historical Gate and Phase decision records left completely intact.
