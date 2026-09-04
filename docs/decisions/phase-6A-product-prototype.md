# Decision Record: Phase 6A — Dr. Md. Momenul Islam Product Prototype

**Gate Reference:** PHASE 6A  
**Date:** 2026-08-28  
**Status:** `PRODUCT_PROTOTYPE_COMPLETE_AND_VERIFIED`  
**Classification:** APPLICATION BUILD COMPLETE — LLM GENERATION STRICTLY DISABLED  

---

## 1. Executive Summary & Objective

In parallel with the independent retrieval research track (Gate 5.26), Phase 6A successfully constructed and verified the complete **Dr. Md. Momenul Islam** local application prototype.

### Core Architectural Decisions:
1. **Strict Research / Build Decoupling**: The backend application layer communicates with the retrieval pipeline solely through an abstracted interface (`BaseRetrievalService`). This guarantees that future changes to retrieval models or corpus expansions in research do not require modifications to the API or frontend contracts.
2. **Current Frozen Candidate Integration**: The retrieval service implements **Strategy 5 (`STRATEGY_5_DUAL_TOPICAL_LEXICAL_ANCHOR`)**, utilizing Track A normalization, `multilingual-e5-small` dense candidates, `bge-reranker-v2-m3` cross-encoder reranking, and dual topical-lexical fusion.
3. **Generation Layer Strictly Disabled**: To uphold strict clinical safety during prototype development, `BaseGenerationService` returns research-mode responses with full retrieved evidence passages and zero synthetic hallucination.

---

## 2. Component Deliverables Summary

| Component | Technology Stack | Key Features | Verification Status |
|---|---|---|---|
| **Backend API** | Python 3.10+, FastAPI, Pydantic v2 | `/health`, `/retrieve`, `/chat` endpoints | ✅ All 7 pytest tests passing |
| **Retrieval Engine** | `sentence-transformers`, `numpy` | Strategy 5 with 68 NHS chunks | ✅ Verified on EN, BN, Banglish |
| **Database Schema** | SQLAlchemy 2.0 (PostgreSQL/SQLite) | `sources`, `chunks`, `query_logs` | ✅ Schema compiled |
| **Frontend UI** | React 18, TypeScript, Tailwind CSS, Vite | Multi-lingual chat, Top-5 evidence viewer, provenance attribution | ✅ Built with 0 TS errors (`npm run build`) |
| **Architecture Docs** | Markdown / GitHub Flavored | Data flow, API contracts, boundaries | ✅ [`application-architecture.md`](../architecture/application-architecture.md) |

---

## 3. API Contract Verification

### 1. `GET /api/v1/health`
```json
{
  "status": "healthy",
  "app_name": "Dr. Md. Momenul Islam — Clinical Health Intelligence",
  "version": "0.6.0-prototype",
  "environment": "research_development",
  "retrieval_strategy": "STRATEGY_5_DUAL_TOPICAL_LEXICAL_ANCHOR",
  "corpus_chunks_loaded": 68,
  "generation_enabled": false
}
```

### 2. `POST /api/v1/retrieve`
- Input: `{"query": "hand burn first aid with cold water", "top_k": 5}`
- Output: Returns normalized query, strategy name, and array of Top-5 evidence passages with chunk IDs, scores, and canonical NHS URLs.

### 3. `POST /api/v1/chat`
- Input: `{"message": "হাত পুড়ে গেলে কী করব?"}`
- Output:
  ```json
  {
    "status": "research_prototype",
    "generation_enabled": false,
    "disclaimer": "Research Prototype — Not for Medical Decision-Making. LLM generation is currently disabled.",
    "user_query": "হাত পুড়ে গেলে কী করব?",
    "evidence_count": 5,
    "evidence": [...],
    "synthetic_answer": "[RESEARCH PROTOTYPE MODE: LLM generation is currently disabled by research protocol. The authoritative NHS evidence passages retrieved below represent the grounding context for this query.]"
  }
  ```

---

## 4. Absolute Boundary Compliance
- **LLM Calls:** 0 external LLM or generation API calls executed.
- **Holdout Data:** No locked holdout benchmarks modified or evaluated.
- **Production Readiness:** Prototype explicitly marked as research-mode only.
