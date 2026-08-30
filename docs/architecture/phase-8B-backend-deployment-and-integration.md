# Architecture Specification — Phase 8B: Backend Deployment & Vercel ↔ Render Integration

**Status:** IN PROGRESS (Deployment & Integration Active)  
**Version:** Phase 8B  
**Date:** August 2026  
**Scope:** Production Deployment, Multi-Cloud Topology, Service Networking, CORS & Environment Governance

---

## 1. System Topology & Service Architecture

The **Dr. Md. Momenul Islam Clinical Health Intelligence** system is deployed across a decoupled multi-cloud architecture:

```
+-------------------------------------------------------------------------+
|                              USER BROWSER                               |
|                  (Desktop / Mobile Client in BD / Global)               |
+-------------------------------------------------------------------------+
                                    |
                                    | HTTPS (HTML / CSS / TS Bundles)
                                    v
+-------------------------------------------------------------------------+
|                           VERCEL EDGE NETWORK                           |
|                      https://drmomenul.vercel.app                       |
|                                                                         |
|  - Framework: React 18 + Vite (SPA)                                     |
|  - Bundled Assets: ~183 kB JS, ~21.5 kB CSS                             |
|  - Routing: Static Single Page Application                              |
|  - Env Config: VITE_API_BASE_URL -> https://drmomenul-api.onrender.com  |
+-------------------------------------------------------------------------+
                                    |
                                    | HTTPS CORS Preflight & JSON REST APIs
                                    | (/api/v1/health, /api/v1/chat, /api/v1/query/understand)
                                    v
+-------------------------------------------------------------------------+
|                      RENDER CLUSTER (Singapore: sin)                    |
|                   https://drmomenul-api.onrender.com                    |
|                                                                         |
|  +-------------------------------------------------------------------+  |
|  |                     DOCKER CONTAINER RUNTIME                      |  |
|  |  - Base: python:3.10-slim (Debian)                                |  |
|  |  - Web Server: Uvicorn ASGI (0.0.0.0:${PORT:-10000})              |  |
|  |  - Concurrency: Exactly 1 worker process                          |  |
|  |  - RAM Sizing: 2 GB (Standard Plan) / 4 GB (Pro Recommended)      |  |
|  |  - Compute: 1 vCPU (CPU-optimized PyTorch execution)             |  |
|  +-------------------------------------------------------------------+  |
|                                    |                                    |
|         +--------------------------+--------------------------+         |
|         |                                                     |         |
|         v                                                     v         |
|  +------------------------------+     +-------------------------------+ |
|  |   Candidate B Bi-Encoder     |     |   Candidate B Cross-Encoder   | |
|  | intfloat/multilingual-e5-    |     |    BAAI/bge-reranker-v2-m3    | |
|  |           small              |     |     (570M Params, ~1.15 GB)   | |
|  |   (118M Params, ~470 MB)     |     +-------------------------------+ |
|  +------------------------------+                     |                 |
|                 |                                     |                 |
|                 v                                     v                 |
|  +--------------------------------------------------------------------+ |
|  |                 119-CHUNK PACKAGED CORPUS INDEX                    | |
|  |           14 NHS Medical Guidelines (DOC-NHS-004..017)             | |
|  |     /app/app/data/promoted_corpus_manifest.json (166 kB)           | |
|  |       SHA-256: 44D0602F730D6460E6FEFA431BD5C09005B48CE92B47D028   | |
|  +--------------------------------------------------------------------+ |
+-------------------------------------------------------------------------+
```

---

## 2. Invariant & Cryptographic Integrity Commitments

The deployed container enforces identical cryptographic hashes and configurations verified across Phase 6J, 7A, 7B, 7C, and 8A:

| Component | Authoritative Value / Hash | Invariant Purpose |
| :--- | :--- | :--- |
| **Active Candidate** | `CANDIDATE_B_CONTEXT_AWARE_DISAMBIGUATION` | Context-aware query expansion & multi-turn disambiguation |
| **Candidate B Hash** | `92224DC6CB0F81C92B8A2869AC562D6CC63B291E36D373F6FE22B524F594EC8A` | Locked candidate freeze |
| **Parent Strategy** | `STRATEGY_5_DUAL_TOPICAL_LEXICAL_ANCHOR` | Base lexical/dense dual-anchor ranking |
| **Parent Strategy Hash** | `1cc216db046264d52bb05616e20123c71b77b56623b17a14c018d0e743ad86ae` | Base strategy freeze |
| **Corpus Manifest Hash** | `44D0602F730D6460E6FEFA431BD5C09005B48CE92B47D02832532E5868D4AA58` | 119 promoted chunks (14 NHS sources) |
| **Generation Status** | `GENERATION_ENABLED=false` | Research prototype mode (LLM disabled) |
| **Retrieval Hyperparameters** | $K=15$, Top-$5$, $\lambda=0.10$, $lpha=0.03$, Overview Debiasing $=0.85$ | Deterministic ranking parameters |

---

## 3. Container Configuration & Lifespan

### 3.1 Docker Build Strategy
- **Base Image:** `python:3.10-slim`.
- **PyTorch Optimization:** CPU wheels installed via `--extra-index-url https://download.pytorch.org/whl/cpu` to avoid downloading 3+ GB of CUDA runtime dependencies.
- **Corpus Bundling:** Packaged directly into the container filesystem at `/app/app/data/promoted_corpus_manifest.json`, ensuring the container operates autonomously without external volume mounts.
- **Concurrency Guard:** Single process execution (`uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}`). Uvicorn worker count must never exceed 1 on a 2 GB instance, as each worker spawns duplicate SentenceTransformer and CrossEncoder model tensors.

### 3.2 Pre-Warming Lifespan Flow
- Uvicorn startup triggers FastAPI lifespan event (`@asynccontextmanager`).
- `get_retrieval_service()` loads `multilingual-e5-small` bi-encoder into memory (~470 MB).
- `get_retrieval_service()` loads `bge-reranker-v2-m3` cross-encoder into memory (~1.15 GB).
- All 119 chunks are loaded from `/app/app/data/promoted_corpus_manifest.json` and dense tensor embeddings are pre-computed in RAM (~10 MB).
- Lifespan yields and the ASGI server binds to `0.0.0.0:${PORT}` to start accepting traffic.

---

## 4. Cross-Origin Resource Sharing (CORS) Security Flow

To prevent unauthorized cross-origin requests while enabling the production frontend and local development workflows, CORS is configured via dynamic environment variable resolution:

- **Allowed Origins:**
  - `https://drmomenul.vercel.app` (Production Web UI)
  - `http://localhost:5173` (Vite local dev)
  - `http://127.0.0.1:5173` (Vite loopback)
- **Preflight Verification:**
  - Method: `OPTIONS`
  - Required Headers: `Origin: https://drmomenul.vercel.app`, `Access-Control-Request-Method: POST`
  - Response: `Access-Control-Allow-Origin: https://drmomenul.vercel.app`, `Access-Control-Allow-Credentials: true`
- **Wildcard Policy:** Wildcard (`*`) origins are strictly prohibited in production when credentials are used.

---

## 5. Cold-Start vs. Warm-Request Latency Profile

| Metric | Target / Expected Range | Architectural Explanation |
| :--- | :--- | :--- |
| **Container Cold Start** | 25 – 45 seconds | Container initialization, CPU PyTorch load, E5 + BGE model instantiation, 119-chunk pre-encoding |
| **Health Check (Warm)** | < 15 ms | In-memory configuration return, zero model inference |
| **Single-Turn Retrieval (Warm)** | 180 – 350 ms | Bi-encoder dense query encoding + cosine similarity + BGE cross-encoder re-ranking of top 15 candidates |
| **Multi-Turn Clarification (Warm)** | 220 – 420 ms | Query understanding + context state update + refined query synthesis + BGE re-ranking |
| **Emergency Red-Flag Query** | < 25 ms | Fast-path regex & keyword emergency rule intercept before dense/reranker inference |
