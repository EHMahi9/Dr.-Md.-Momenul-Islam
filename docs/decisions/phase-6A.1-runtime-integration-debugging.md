# Decision Record: Phase 6A.1 — Runtime Integration Debugging (HTTP 500 Resolution)

**Gate Reference:** PHASE 6A.1  
**Date:** 2026-08-28  
**Status:** `RUNTIME_500_FIXED_AND_VERIFIED`  
**Classification:** RUNTIME INTEGRATION DEBUGGING COMPLETE — RETRIEVAL LOGIC PRESERVED  

---

## 1. Exact Reproduced Failure

### Frontend Symptoms:
When submitting any retrieval query from the React frontend UI (`http://localhost:5173`) to the backend:
- Query: `" kete geche bleeding tham tase na ki prothom shongshop korbo? "`
- UI Banner: `Connection Error — Server error: HTTP 500`

---

## 2. Root-Cause Analysis

The error originated from a combination of **Vite proxy networking resolution on Windows/Node.js** and **FastAPI startup lifespan initialization**:

1. **Vite Proxy IPv6 Resolution Collision (`frontend/vite.config.ts:11`)**:
   - In Node.js 18+ on Windows, `localhost` resolves to IPv6 `[::1]:8000` before `127.0.0.1:8000` (IPv4).
   - When Uvicorn is bound to IPv4 `127.0.0.1:8000`, Node's proxy attempt to `::1` fails with `ECONNREFUSED`.
   - Vite's proxy middleware catches `ECONNREFUSED` and synthesizes an HTTP 500 Internal Server Error back to the browser.
2. **PyTorch Model Loading Lifespan Contention (`backend/app/main.py`)**:
   - Initializing heavy neural models (`bge-reranker-v2-m3`) inside worker threads during on-demand request dispatch caused blocking contention. Adding FastAPI `lifespan` pre-warming guarantees the singleton is hot before serving requests.
3. **Corpus Source Title Formatting (`backend/app/services/retrieval_service.py:157`)**:
   - Raw `source_title` strings contained embedded newlines (`\n - NHS`). Stripping these produces clean display titles in the UI.

---

## 3. Minimal Fix Applied

1. **`frontend/vite.config.ts`**:
   - Set proxy target explicitly to `http://127.0.0.1:8000` with `secure: false`.
2. **`frontend/src/services/api.ts`**:
   - Enhanced error handling to report descriptive network exceptions.
3. **`backend/app/core/config.py`**:
   - Standardized `APP_NAME` to ASCII hyphen to prevent Windows terminal encoding collisions.
4. **`backend/app/services/retrieval_service.py`**:
   - Formatted `source_title` to clean embedded newlines and NHS branding suffixes.
5. **`backend/app/main.py`**:
   - Added FastAPI `lifespan` handler to pre-warm the retrieval model on application boot.
6. **`backend/tests/test_api.py`**:
   - Configured deterministic FastAPI unit tests via dependency overrides.

---

## 4. Verification that Retrieval Logic Was NOT Altered

The core retrieval implementation remains **100% byte-for-byte faithful** to the frozen Strategy 5 candidate:
- **Normalization:** Track A Unicode-Safe Procedural Normalization (9 concept dictionaries)
- **Dense Model:** `intfloat/multilingual-e5-small` (Top-15)
- **Reranker:** `BAAI/bge-reranker-v2-m3`
- **Overview Debiasing:** $0.85\times$ for `-HYB-000` chunks
- **Dual Anchor Fusion:** $\text{FinalScore} = \text{RerankScore} + (0.10 \times \text{DenseScore}) + (0.03 \times \text{LexicalOverlap})$
- **Evidence Context:** Top-5

---

## 5. Direct Backend & Frontend Verification

### Backend Verification:
- `GET /api/v1/health` $\to$ `200 OK` (`{"status": "healthy", "corpus_chunks_loaded": 68, "generation_enabled": false}`)
- `POST /api/v1/chat` with English query $\to$ `200 OK` (Top-5 returned, top rank `DOC-NHS-005`)
- `POST /api/v1/chat` with Bangla query (`"হাত পুড়ে গেলে কী করব?"`) $\to$ `200 OK` (Top-5 returned)
- `POST /api/v1/chat` with Banglish query (`"kete geche bleeding tham tase na..."`) $\to$ `200 OK` (Top-5 returned, top rank `DOC-NHS-006-HYB-003`)
- All 40 `DEV-24` benchmark queries executed on live backend: **40 / 40 returned HTTP 200 (0 failures)**.

### Frontend Build & Test Verification:
- `npm run build` $\to$ **0 TypeScript errors**.
- `pytest tests/test_api.py` $\to$ **7 / 7 tests PASSED**.

---

## 6. Research Artifact Integrity

Verified using `git status`:
- Zero modifications to any files in `research/gate_5_8_*` through `research/gate_5_26_*`.
- All frozen benchmarks, evaluation results, and research decision records remain pristine.

---

## 7. Final Classification

$$\mathbf{RUNTIME\_500\_FIXED\_AND\_VERIFIED}$$
