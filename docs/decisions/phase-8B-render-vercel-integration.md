# Architectural Decision Record (ADR-008B) — Render Backend Deployment & Vercel Integration

**Status:** APPROVED & ACTIVE  
**Date:** August 2026  
**Deciders:** Core Engineering Team  
**Consulted:** Clinical NLP & ML Engineering  

---

## 1. Context and Problem Statement

The clinical intelligence prototype requires deployment to a reliable cloud environment to enable end-to-end integration between the production React SPA hosted on Vercel (`https://drmomenul.vercel.app`) and the containerized FastAPI backend on Render (`https://drmomenul-api.onrender.com`). The deployment must maintain strict cryptographic parity with frozen candidate B, prevent out-of-memory crashes from large neural rerankers, and preserve zero-leakage security protocols.

---

## 2. Decision Outcomes

### Decision 1: Existing Service Reconfiguration (`drmomenul-api`)
- **Decision:** Reconfigure the existing `drmomenul-api` Render service rather than provisioning duplicate services.
- **Rationale:** Preserves the stable URL endpoint (`https://drmomenul-api.onrender.com`), avoids DNS churn, and prevents orphaned infrastructure.

### Decision 2: Docker Runtime with CPU PyTorch Strategy
- **Decision:** Use `backend/Dockerfile` with Debian-slim and CPU-only PyTorch wheels.
- **Rationale:** Minimizes container footprint (< 1.8 GB) while supporting both `intfloat/multilingual-e5-small` and `BAAI/bge-reranker-v2-m3` without requiring expensive GPU compute instances.

### Decision 3: Single Worker Process Constraint
- **Decision:** Enforce `--workers 1` in Uvicorn startup.
- **Rationale:** Spawning multiple worker processes duplicates model weights in RAM (each worker = ~1.6 GB), which causes immediate OOM crashes on 2 GB / 4 GB instance tiers.

### Decision 4: Singapore Region Selection (`singapore`)
- **Decision:** Deploy the Render Web Service to the Singapore region (`singapore`).
- **Rationale:** Minimizes round-trip network latency for primary target users in Bangladesh and South Asia (~40-70 ms RTT vs ~220 ms RTT to Oregon/US-West).

### Decision 5: Separation of Deployed vs. Production-Ready
- **Decision:** Explicitly classify this state as **BACKEND DEPLOYED & INTEGRATED**, maintaining the clinical distinction that generation remains disabled (`GENERATION_ENABLED=false`) and irrelevant evidence exposure (16% on development benchmark) is a documented open UX issue, not a clinical sign-off.

---

## 3. Rollback Procedure

If the Render deployment encounters unexpected operational failure:
1. **Render Dashboard Rollback:** Navigate to `drmomenul-api` → **Deploys** → Select previous known good commit → **Rollback to this deploy**.
2. **Vercel Fallback:** If the backend is temporarily offline, Vercel can revert `VITE_API_BASE_URL` or serve static maintenance states.
3. **Corpus & Configuration Safety:** No corpus files or candidate freeze hashes are modified during rollback.
