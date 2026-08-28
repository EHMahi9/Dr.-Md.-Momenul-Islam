# Decision Record: Phase 6A.4 — Corpus & Configuration Lifecycle Management

**Gate Reference:** PHASE 6A.4  
**Date:** 2026-08-29  
**Status:** `CORPUS_LIFECYCLE_IMPLEMENTED`  
**Classification:** THREE-TIER CORPUS LIFECYCLE MODEL & MULTI-TIER ISOLATION IMPLEMENTED  

---

## 1. Executive Summary & Policy Formulation

Phase 6A.4 established and enforced an explicit, secure **Three-Tier Corpus Lifecycle Model** in both the backend application service layer and the frontend user interface.

### The Immutable Lifecycle Rule:
$$\text{Source} \to \text{Verified (Gate 5.26)} \to \text{Ingested (Gate 5.27)} \to \text{Benchmarked (Gate 5.28)} \to \text{Validated (Gate 5.29)} \to \text{Promoted to Active Corpus}$$

> [!IMPORTANT]
> **Corpus Promotion Boundary Enforcement:**
> Ingesting new research documents into `research/gate_5_27_ingestion/` does **NOT** automatically promote them to the active application retrieval corpus. The active retrieval engine remains strictly bound to the **68-chunk baseline corpus** until formal multi-lingual single-shot benchmark validation (Gate 5.29) is completed and approved.

---

## 2. Three-Tier Corpus Architecture

| Tier | Lifecycle State | Target Sources | Chunk Count | Storage Location | Application Retrieval Access |
|---|---|---|---|---|---|
| **Tier 1: Active Corpus** | `ACTIVE` | `DOC-NHS-004` to `DOC-NHS-011` (8 Conditions) | **68 Chunks** | `research/gate_5_9_optimization/chunks/hybrid_600/` | ✅ **LIVE** (Primary grounding) |
| **Tier 2: Staged Research** | `STAGED_RESEARCH` | `DOC-NHS-012` to `DOC-NHS-017` (6 Conditions) | **51 Chunks** | `research/gate_5_27_ingestion/` | ❌ **ISOLATED** (Research holdout only) |
| **Tier 3: Validated Corpus** | `NOT_ACTIVE` | None | **0 Chunks** | Pending Gate 5.29 validation | ❌ **NOT ACTIVE** |

---

## 3. Backend Implementation & Endpoints

### 1. `GET /api/v1/health`
Updated to return explicit corpus chunk breakdowns:
- `active_corpus_chunks`: `68`
- `staged_research_chunks`: `51`
- `candidate_hash`: `07f031da533d47666fb5abd242f8db47b90dc584a92c0b3f399abaaf51c02736`
- `generation_enabled`: `false`

### 2. `GET /api/v1/corpus`
Returns full structured metadata for all 3 lifecycle tiers:
- `active_corpus`: Document list, chunk count, description.
- `staged_research_corpus`: Document list (`DOC-NHS-012`..`017`), chunk count, description.
- `validated_corpus`: Promotion status (`NOT_ACTIVE`).
- `retrieval_candidate`: Model parameters, candidate depth, and frozen hash.

---

## 4. Frontend UI Lifecycle Visibility

The application [`Header.tsx`](file:///d:/my-ai-project/Dr.%20Md.%20Momenul%20Islam/frontend/src/components/Header.tsx) displays clear status badges:
- 🟢 `Active Corpus: 68 Chunks (NHS)`
- 🟡 `Staged Research: 51 Chunks (Locked)`
- 🔵 `Candidate: Strategy 5 (Dev)`
- 🔴 `Generation: Disabled`

---

## 5. Verification & Test Suite

- **Automated Tests:** `9 / 9` pytest unit tests passing in `backend/tests/test_api.py`.
- **Staged Corpus Isolation Test:** Verified that staged source IDs (`DOC-NHS-012` to `DOC-NHS-017`) have **0% intersection** with retrieved evidence chunks.
- **Frontend Build:** `tsc && vite build` built in 5.99s with 0 TypeScript errors.

---

## 6. Final Status

$$\mathbf{CORPUS\_LIFECYCLE\_IMPLEMENTED}$$
