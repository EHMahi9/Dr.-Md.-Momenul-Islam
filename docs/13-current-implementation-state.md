# Dr. Md. Momenul Islam — Current Implementation & Deployment State

> **Status:** Production / Research Prototype (Verified Active)  
> **Document Version:** 1.0.0  
> **Date:** 2026-09-04  
> **Repository:** `E:\Dr. Md. Momenul Islam`  
> **Governing Documents:** Supersedes preliminary assumptions in `docs/00`–`12` while preserving all approved clinical safety and evaluation policies.

---

## 1. Executive Summary

This document specifies the verified, operational state of **Dr. Md. Momenul Islam — Clinical Health Intelligence** (Track A). The system provides evidence-grounded clinical information retrieval across English, Native Bangla (বাংলা), and Banglish queries, referencing official NHS England clinical guidance under Open Government Licence (OGL) v3.0.

All operations adhere to the strict **$0 hosting cost requirement**, running a high-performance bi-encoder + cross-encoder neural pipeline on local Docker hardware exposed via secure Tailscale Funnel to a globally distributed Vercel frontend.

---

## 2. Authoritative Deployment Topology

```
+-------------------------------------------------------------+
|                      USER BROWSER / CLIENT                  |
+-------------------------------------------------------------+
                              |
                              | HTTPS (TLS)
                              v
+-------------------------------------------------------------+
|                     VERCEL HOBBY ($0/mo)                    |
| URL: https://drmomenul.vercel.app                           |
| Stack: React 18.2 + Vite 5.4 + TypeScript 5.2 + Tailwind 3.4|
| UI Theme: Calm Clinical Minimalism (Teal & Warm Neutrals)   |
| Env: VITE_API_BASE_URL=https://momenul.taile15170.ts.net    |
+-------------------------------------------------------------+
                              |
                              | HTTPS (Public TLS Termination)
                              v
+-------------------------------------------------------------+
|                    TAILSCALE FUNNEL ($0/mo)                 |
| Endpoint: https://momenul.taile15170.ts.net                 |
| Routing: Reverse proxy to host port 8000 (127.0.0.1:8000)   |
+-------------------------------------------------------------+
                              |
                              | TCP Proxy
                              v
+-------------------------------------------------------------+
|                  HOST MACHINE (Windows 11 / WSL2)           |
| Hardware: 8 CPU Cores, 15.54 GiB RAM                        |
| Docker Engine: 29.7.2 (Linux/amd64 native)                  |
| Container: drmomenul-api-test (Port 8000)                   |
| Image: drmomenul-api:amd64 (2.03 GB, native PyTorch CPU)    |
| Stack: FastAPI 0.110 + Uvicorn + Python 3.10                |
+-------------------------------------------------------------+
```

### Hosting & Cost Architecture
- **Total Operational Cost:** **$0.00 / month**.
- **Render Standard / Paid Tiers:** Explicitly rejected due to memory requirement (~1.5 GB peak) exceeding Render Free tier (512 MB).
- **Public Accessibility:** Provided by Tailscale Funnel with automatic TLS certificate lifecycle management.
- **Reliability:** Containerized with Docker healthchecks, automatic restart capability, and persistent pre-warmed model caches.

---

## 3. Locked Architecture Parameters (Invariants)

The following parameters are formally locked and empirically validated:

| Parameter | Locked Value | Verification Status |
|---|---|---|
| **Retrieval Strategy** | `STRATEGY_5_DUAL_TOPICAL_LEXICAL_ANCHOR` | Verified (`/api/v1/health`) |
| **Active Candidate** | `CANDIDATE_B_CONTEXT_AWARE_DISAMBIGUATION` | Verified (`/api/v1/health`) |
| **Candidate B Hash** | `92224DC6CB0F81C92B8A2869AC562D6CC63B291E36D373F6FE22B524F594EC8A` | Verified |
| **Parent Strategy Hash** | `1cc216db046264d52bb05616e20123c71b77b56623b17a14c018d0e743ad86ae` | Verified |
| **Embedding Model** | `intfloat/multilingual-e5-small` (384 dims) | Pre-cached in image |
| **Reranker Model** | `BAAI/bge-reranker-v2-m3` (Cross-encoder) | Pre-cached in image |
| **Active Corpus Chunks** | **119** verified clinical passages | Verified |
| **Corpus Source** | 14 NHS Conditions (`DOC-NHS-004` to `DOC-NHS-017`) | OGL v3.0 |
| **Dense Retrieval Top-K** | `K_dense = 15` | Verified |
| **Final Reranked Top-K** | `K_final = 5` | Verified |
| **Interpolation Weights** | `lambda = 0.10` (Dense), `alpha = 0.03` (Lexical), `overview = 0.85` | Verified |
| **LLM Generation** | `generation_enabled = false` (Locked / Disabled) | Strict zero hallucination |
| **Frontend Base URL** | `https://momenul.taile15170.ts.net` | Configured on Vercel |

---

## 4. Retrieval Pipeline & Multi-Stage Processing

1. **Query Understanding & Normalization:** Language detection, symptom/location/duration slot extraction, red-flag triage, Unicode Bengali normalization.
2. **Dense Retrieval (Bi-Encoder):** `intfloat/multilingual-e5-small` with in-memory normalized NumPy cosine similarity across 119 chunks (Top-15 pool).
3. **Cross-Encoder Reranking (Candidate B):** `BAAI/bge-reranker-v2-m3` scoring with context-aware disambiguation and topic-lexical anchoring (Top-5 final passages).
4. **Confidence Assessment:** Evaluation of top score, score spread, and margins. Outcome states: `SUPPORTED_RETRIEVAL`, `LOW_CONFIDENCE_RETRIEVAL`, `POSSIBLE_MISMATCH`, `NO_RELEVANT_EVIDENCE`, `UNSUPPORTED_BY_ACTIVE_CORPUS`.
5. **Safety & Evidence Presentation:** Red-flag emergency override banner (bilingual), symptom clarification for ambiguous queries, clinical passage cards with OGL v3.0 license and NHS citations.

---

## 5. Verified API Endpoints

- `GET /api/v1/health`: Service health, active container ID, loaded models, corpus chunk count, candidate hashes, generation status.
- `POST /api/v1/chat`: Multi-turn clinical consultation pipeline supporting English, বাংলা, and Banglish.
- `GET /api/v1/corpus`: Active clinical corpus metadata and condition inventory.
- `POST /api/v1/query/understand`: Query understanding, slot extraction, and red-flag classification.
- `POST /api/v1/retrieve`: Standalone Strategy 5 dual-anchor retrieval with cross-encoder reranking.

---

## 6. Frontend UI/UX (Calm Clinical Minimalism)

- **Landing Experience:** Single obvious primary purpose: "Ask a health question" with sample queries.
- **Progressive Disclosure:** Engineering metrics (fused score, dense cosine, lexical overlap, hashes) concealed by default behind clean diagnostics toggles.
- **Safety Visual Hierarchy:** Red-flag alerts rendered with urgent bilingual advice and emergency helpline contacts.
- **Palette & Typography:** Deep teal primary accent (`#0f766e`), warm neutral surfaces (`#fafaf9`), clear font scaling, and generous whitespace.

---

## 7. Empirically Verified Performance

Measured on native `linux/amd64` Docker engine (Port 8000):
- **English Query** (*"What should I do for a minor burn?"*): **26.1s** (`SUPPORTED_RETRIEVAL`, top score: 0.6732)
- **Emergency Query** (*"severe chest pain and difficulty breathing"*): **20.5s** (`EMERGENCY_OVERRIDE`)
- **Native Bangla Query** (*"ছোটখাটো পোড়া হলে কী করা উচিত?"*): **34.5s**
- **Banglish Query** (*"kete gele prothome ki kora uchit?"*): **34.5s**

All production queries execute within the Vercel 75-second timeout window.
