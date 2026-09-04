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
[COMPLETED] Phase 8A: Production Backend Packaging (Linux amd64 Docker, PyTorch Native, Model Caching)
[COMPLETED] Phase 8B: Zero-Cost Backend Deployment via Tailscale Funnel + Vercel Integration
[COMPLETED] Phase 8C: Runtime Performance Optimization (Native amd64 build, 20–34s query latency)
[COMPLETED] Phase 8D: Frontend UI/UX Redesign (Calm Clinical Minimalism, Progressive Disclosure)
[COMPLETED] Phase 8E: Documentation Synchronization & Authoritative State Baseline (docs/13)
[FUTURE]    Phase 9A: LLM-Assisted Conversational Generation (when generation_enabled is revisited)
[FUTURE]    Phase 9B: Multi-Turn Grounded Generation Evaluation
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
| **Phase 8A–8C** | Zero-Cost ($0) Production Deployment | Built native `linux/amd64` Docker image with pre-cached models; provisioned Tailscale Funnel public HTTPS URL (`https://momenul.taile15170.ts.net`); connected live Vercel frontend (`https://drmomenul.vercel.app`); latencies 20–34s. | **VERIFIED** |
| **Phase 8D–8E** | UI/UX Redesign & Doc Sync | Redesigned frontend to "Calm Clinical Minimalism" with progressive disclosure; synchronized all governing specifications in `docs/13-current-implementation-state.md`. | **VERIFIED** |

---

### B. FUTURE MILESTONES

#### Phase 9A: LLM-Assisted Conversational Generation
- Controlled LLM rewriting of clarification questions and grounded answers within strictly bounded evidence contexts using `BaseLLMProvider` (when protocol permits).

#### Phase 9B: Multi-Turn Grounded Generation Evaluation
- Evaluation of end-to-end multi-turn generation against locked gold citations and anti-hallucination metrics.

#### Later Horizons:
1. **Broader Trusted-Source Ingestion:** Ingest vetted clinical guidance from Bangladesh national authorities (DGHS, IEDCR).
2. **Foundation Model Comparison:** Systematic evaluation across open-weight and proprietary models.
3. **Banglish Vocabulary Expansion:** Evaluated as a separately versioned candidate (Candidate B configuration remains frozen).
4. **Privacy & Telemetry:** Implement privacy-preserving telemetry, audit logging, and rate limiting.
5. **Clinical Governance:** Multidisciplinary clinical safety review and formal clinical validation protocols.

---

## 3. Current Operational Status & Known Open Issues

- **Deployment Status:** Frontend is deployed at `https://drmomenul.vercel.app`. Backend is operational in production Docker (`drmomenul-api-test`, `linux/amd64`) exposed via Tailscale Funnel (`https://momenul.taile15170.ts.net`) with zero monthly hosting cost.
- **Authoritative System State:** Fully detailed in [`docs/13-current-implementation-state.md`](./13-current-implementation-state.md).
- **Known Open Product/UX Issue:** Phase 7C reduced irrelevant evidence exposure from 40% to 16% on its development benchmark. Unrelated candidate suppression policy is active in the frontend.
- **Banglish Invariance:** The validated Candidate B configuration remains frozen. Any future vocabulary expansion will be treated as an isolated research candidate.

---

## 4. Explicit Non-Goals & Scope Boundaries

The following capabilities remain strictly **OUT OF SCOPE**:
- Autonomous medical diagnosis or diagnostic labeling ("you have X").
- Automated prescription generation or drug dosage modification.
- Clinician replacement or automated medical triage.
- Arbitrary ungrounded web search.
- Medical record (EHR) modification or hospital billing interfaces.
