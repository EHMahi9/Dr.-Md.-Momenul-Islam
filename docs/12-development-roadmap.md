# Development Roadmap: Dr. Md. Momenul Islam Health Assistant

> **Status:** Phase 7C Completed & Independently Verified  
> **Active Baseline:** Candidate B Context-Aware Disambiguation (119 Active NHS Chunks)  
> **Classification:** Research & Product Prototype [NOT CLINICALLY VALIDATED]

---

## 1. Roadmap Overview & Status Matrix

```
[COMPLETED] Phase 1–5: Foundation and retrieval research
[COMPLETED] Phase 6A–6K: Corpus expansion, retrieval validation, Candidate B selection and validation
[COMPLETED] Phase 7A: Query understanding, ambiguity detection, evidence sufficiency, emergency routing
[COMPLETED] Phase 7B: Multi-turn clarification and structured conversation state
[COMPLETED] Phase 7C: Adaptive clarification and question-utility planning
[NEXT]      Phase 8A: Production Backend Deployment Preparation (Linux, Render, CORS, Packaging)
[NEXT]      Phase 8B: Backend Deployment + Vercel ↔ Render Integration
[NEXT]      Phase 8C: Cloud Runtime / Performance Optimization
[FUTURE]    Phase 8D: LLM-Assisted Conversational Generation
[FUTURE]    Phase 8E: Multi-Turn Grounded Generation Evaluation
[LATER]     Broader Source Coverage, Bangladesh National Guidance, Privacy & Clinical Governance
```

---

## 2. Phase-by-Phase Roadmap Details

### A. COMPLETED PHASES [VERIFIED]

| Phase / Milestone | Milestone Description | Key Technical Outcomes | Verification Status |
| :--- | :--- | :--- | :--- |
| **Phase 1–5** | Foundation & Retrieval Research | Defined non-diagnostic safety policy, ingested NHS First Aid topics (68 chunks), benchmarked baseline retrieval. | **VERIFIED** |
| **Phase 6A–6K** | Corpus Expansion & Candidate B Freeze | Expanded corpus to **119 chunks** across 14 NHS sources (`DOC-NHS-004`..`017`), solved overview chunk bias with $0.85\times$ debiasing, and locked `CANDIDATE_B_CONTEXT_AWARE_DISAMBIGUATION` (Recall@5: 100%, MRR: 0.7862). | **VERIFIED** |
| **Phase 7A** | Query Understanding & Ambiguity Detection | Implemented slot extraction, broad anatomy ambiguity detection, red flag heuristics, and language preference (Auto / বাংলা / EN). | **VERIFIED** |
| **Phase 7B** | Structured Context & Multi-Turn Clarification | Implemented `ConversationContextState`, observable quick-select chips UI, and multi-turn state preservation. | **VERIFIED** |
| **Phase 7C** | Adaptive Clarification & Question-Utility Planning | Implemented 6-factor Question-Utility Model, 4 Early Stopping Rules, duplicate question suppression (0.00%), and 0.00% unnecessary clarification rate. | **VERIFIED** |

---

### B. NEXT MILESTONES (Phase 8 Production Deployment & Cloud Optimization)

#### Phase 8A: Production Backend Deployment Preparation
- **Linux / Cloud Environment Audit:** Verify PyTorch, HuggingFace transformers, and FastAPI execution on Linux cloud container targets.
- **Render Deployment Packaging:** Author production `Dockerfile`, startup entrypoints, and container health check routes.
- **Runtime Model Loading & Corpus Packaging:** Optimize loading of `intfloat/multilingual-e5-small` and `BAAI/bge-reranker-v2-m3` in memory-constrained cloud environments.
- **CORS & Environment Configuration:** Secure CORS headers to allow requests from `https://drmomenul.vercel.app`.
- **Frontend API Alignment:** Configure environment variables in frontend for remote backend endpoints.

#### Phase 8B: Backend Deployment + Vercel ↔ Render Integration
- **Render Service Provisioning:** Deploy FastAPI backend service to Render.
- **Vercel ↔ Render Live Integration:** Connect frontend (`https://drmomenul.vercel.app`) to live Render backend.
- **Live Smoke & End-to-End Testing:** Execute end-to-end multi-turn query and evidence retrieval verification across web endpoints.

#### Phase 8C: Cloud Runtime & Performance Optimization
- **Cold-Start Mitigation & Caching:** Implement embedding pre-warming and model memory footprint tuning.
- **Latency Profiling:** Measure end-to-end network and inference latency in cloud runtime.

---

### C. FUTURE MILESTONES

#### Phase 8D: LLM-Assisted Conversational Generation
- Controlled LLM rewriting of clarification questions and grounded answers within strictly bounded evidence contexts using `BaseLLMProvider`.

#### Phase 8E: Multi-Turn Grounded Generation Evaluation
- Evaluation of end-to-end multi-turn generation against locked gold citations and anti-hallucination metrics.

#### Later Horizons:
1. **Broader Trusted-Source Ingestion:** Ingest vetted clinical guidance from Bangladesh national authorities (DGHS, IEDCR).
2. **Foundation Model Comparison:** Systematic evaluation across open-weight (Llama 3, Gemma 2, Qwen 2.5) and proprietary API models.
3. **Banglish Vocabulary Expansion:** Further Banglish vocabulary expansion remains future research work and must be evaluated as a separately versioned candidate (Candidate B configuration remains frozen).
4. **Privacy & Telemetry:** Implement privacy-preserving telemetry, audit logging, and rate limiting.
5. **Clinical Governance:** Multidisciplinary clinical safety review and formal clinical validation protocols.

---

## 3. Current Operational Status & Known Open Issues

- **Deployment Status:** Frontend is deployed at `https://drmomenul.vercel.app`. Backend is currently a **local/research runtime** until Phase 8A/8B cloud deployment is complete.
- **Known Open Product/UX Issue:** Phase 7C reduced irrelevant evidence exposure from 40% to 16% on its development benchmark, but did not eliminate the issue completely. This is classified as a **KNOWN OPEN PRODUCT/UX ISSUE** under active development, not a clinical safety validation result.
- **Banglish Invariance:** The validated Candidate B configuration remains frozen. Any future vocabulary expansion will be treated as an isolated research candidate.

---

## 4. Explicit Non-Goals & Scope Boundaries

The following capabilities remain strictly **OUT OF SCOPE**:
- Autonomous medical diagnosis or diagnostic labeling ("you have X").
- Automated prescription generation or drug dosage modification.
- Clinician replacement or automated medical triage.
- Arbitrary ungrounded web search.
- Medical record (EHR) modification or hospital billing interfaces.
