# Decision Record: Phase 8A — Render Production Deployment Preparation

**Record ID:** ADR-008A-RENDER-DEPLOYMENT-READINESS  
**Date:** August 2026  
**Status:** APPROVED / READY_FOR_RENDER_DEPLOYMENT  
**Deciders:** Core Engineering Team  

---

## 1. Context and Problem Statement

The clinical intelligence system previously executed within a local research environment. The web frontend is hosted on Vercel (`https://drmomenul.vercel.app`). To prepare the backend for production hosting on Render without disrupting validated retrieval semantics, the application requires containerization, environment portability, CORS hardening, health probing, and memory-aware instance configuration.

Crucially, this phase is **DEPLOYMENT PREPARATION ONLY**:
- No live Render service is created in this phase.
- No live Vercel configuration is altered in this phase.
- No retrieval parameters or Candidate B configurations are modified.
- No research benchmarks are re-executed.

---

## 2. Decision Outcomes

### Decision 1: Container Runtime & Image Architecture
- **Decision:** Build a single container image using `python:3.10-slim` with CPU-only PyTorch (`torch --index-url https://download.pytorch.org/whl/cpu`).
- **Rationale:** Keeps container image lightweight (~1.8 GB) and prevents multi-gigabyte GPU driver dependencies while operating within CPU cloud tiers.

### Decision 2: Concurrency & Worker Model
- **Decision:** Run Uvicorn with a single worker (`--workers 1`).
- **Rationale:** The cross-encoder (`BAAI/bge-reranker-v2-m3`) requires ~1.15 GB RAM. Spawning multiple workers would duplicate model memory allocation, leading to immediate OOM terminations on Render standard instances.

### Decision 3: Packaged Corpus Manifest with Multi-Tier Fallback
- **Decision:** Package `promoted_corpus_manifest.json` directly into `backend/app/data/` inside the container image, while maintaining a 3-tier fallback in `backend/app/core/config.py`.
- **Rationale:** Ensures complete container autonomy without requiring external volume mounts, cloud object storage downloads at startup, or monorepo path assumptions.

### Decision 4: Environment-Driven CORS Configuration
- **Decision:** Parse `CORS_ORIGINS` dynamically from environment variables, defaulting to `https://drmomenul.vercel.app`, `http://localhost:5173`, and `http://127.0.0.1:5173`.
- **Rationale:** Enables strict origin validation in production while preserving local development workflows.

### Decision 5: Render Hardware Tier Selection
- **Decision:** Select **Standard Plan (2 GB RAM / 1 vCPU)** as the minimum operational baseline and recommend **Pro Plan (4 GB RAM / 2 vCPU)** for production stability.
- **Rationale:** Total system resident memory footprint is ~1.98 GB. The 512 MB Starter plan will fail with OOM errors.

---

## 3. Invariants & Guardrails Preserved

1. **Retrieval Candidate B:** `92224DC6CB0F81C92B8A2869AC562D6CC63B291E36D373F6FE22B524F594EC8A` (Strictly Unmodified).
2. **Parent Strategy 5:** `1cc216db046264d52bb05616e20123c71b77b56623b17a14c018d0e743ad86ae` (Strictly Unmodified).
3. **Active Corpus Manifest:** `44D0602F730D6460E6FEFA431BD5C09005B48CE92B47D02832532E5868D4AA58` (119 chunks, 14 NHS sources, Verified).
4. **Generation Guardrail:** LLM Generation remains `generation_enabled = False`.
5. **Known Open Product/UX Issue:** Irrelevant evidence suppression operates at 16% exposure rate on development benchmark (documented as open UX issue, not clinical safety validation).

---

## 4. Next Phase Triggers

Upon user approval of Phase 8A:
- **Phase 8B:** Provision Render Web Service using `render.yaml`, configure `VITE_API_BASE_URL` on Vercel, and perform live end-to-end smoke verification.
