# Phase 7A Decision Record: Candidate B Production Promotion & Clarification Foundation

**Project:** Dr. Md. Momenul Islam Health Intelligence  
**Author:** Google DeepMind / Antigravity Engineering  
**Date:** 2026-08-29  
**Decision Status:** APPROVED & EXECUTED  
**Related Milestones:** Phase 6K (Single-Shot Validation), Phase 6J (Benchmark Freeze), Phase 6I (Candidate B Freeze)  

---

## 1. Context & Motivation

Following the successful single-shot cryptographic validation in Phase 6K, Candidate B (Context-Aware Compound Disambiguation) was certified as the development winner over Strategy 5 Control (+2.78pp Recall@5, 0% English regression, 0% Native Bangla regression, 0/4 OOC false positives).

Phase 7A was executed across two logically independent tracks:
- **Track A:** Promotion of Candidate B into active production runtime.
- **Track B:** Implementation of the Query Understanding, Evidence-Sufficiency, and Conversational Clarification Architecture foundation.

---

## 2. Track A Decisions: Candidate B Production Promotion

### 2.1 Candidate Lineage & Freeze Verification
- **Active Retrieval Candidate:** `CANDIDATE_B_CONTEXT_AWARE_DISAMBIGUATION`
- **Candidate B Freeze SHA-256:** `92224DC6CB0F81C92B8A2869AC562D6CC63B291E36D373F6FE22B524F594EC8A`
- **Parent Strategy 5 SHA-256:** `1cc216db046264d52bb05616e20123c71b77b56623b17a14c018d0e743ad86ae`
- **Active Corpus Manifest SHA-256:** `44D0602F730D6460E6FEFA431BD5C09005B48CE92B47D02832532E5868D4AA58` (119 Chunks / 14 NHS Sources)
- **Staged Research Chunks:** 0 (Fully promoted via Phase 6C)

### 2.2 Preserved Hyperparameters (Strict Zero-Drift Policy)
The following hyperparameters were preserved without modification:
- Bi-encoder: `intfloat/multilingual-e5-small` (CPU, query prefix `"query: "`, passage prefix `"passage: "`)
- Cross-encoder: `BAAI/bge-reranker-v2-m3` (CPU, batch size 8, max length 512)
- Dense Candidate Depth: $K = 15$
- Final Evidence Passages: $K = 5$
- Dense Fusion Weight: $\lambda = 0.10$
- Lexical Overlap Weight: $\alpha = 0.03$
- Overview Chunk Multiplier: $0.85$

---

## 3. Track B Decisions: Query Understanding & Evidence-Sufficiency Policy

### 3.1 Resolving the "No Evidence Found" Presentation Mismatch
Prior behavior for underspecified queries (such as *"amar paye betha, ki korbo?"*) displayed an abstention banner while simultaneously rendering ordinary Top-5 passages (e.g., Meningitis, Burns, Sepsis) as though they were supporting evidence.

**Adopted Policy:**
- When query intent is `UNDERSPECIFIED_AMBIGUOUS` or `UNSUPPORTED_ACTIVE_CORPUS`, or retrieval outcome is `NO_RELEVANT_EVIDENCE` or `UNSUPPORTED_BY_ACTIVE_CORPUS`, the UI policy is set to `SUPPRESS_UNRELATED_CARDS_SHOW_ABSTENTION`.
- Ordinary evidence cards are hidden from the primary user view.
- An interactive clarification card is rendered with structured quick-select options.
- Raw candidate passages remain accessible only via a collapsed *"Technical / Diagnostic Details"* accordion for clinical and engineering auditability.

### 3.2 4-Tier Intent & Safety Classification
Deterministic rule-based classification ensures:
1. `POTENTIALLY_EMERGENCY` $\implies$ Immediate bilingual red-flag alert with 999 routing.
2. `UNSUPPORTED_ACTIVE_CORPUS` $\implies$ Explicit out-of-scope abstention with professional consultation advice.
3. `UNDERSPECIFIED_AMBIGUOUS` $\implies$ Interactive clarification prompt to disambiguate trauma, cuts, burns, or sprains.
4. `CLEARLY_ANSWERABLE` $\implies$ Candidate B retrieval with standard evidence card presentation.

---

## 4. Verification & Validation Summary

| Test Suite / Benchmark | Target | Result | Status |
| :--- | :--- | :--- | :--- |
| **Track A Production Regression** | 8 test cases (lineage, corpus counts, generation disabled, multi-lingual retrieval) | 8/8 Passed (100%) | **PASS** |
| **Track B Query Understanding Unit Tests** | 6 test cases (underspecified, native Bangla, Banglish, OOC, emergency, headache) | 6/6 Passed (100%) | **PASS** |
| **Track B Development Benchmark ($N=20$)** | Intent, Sufficiency, Policy, and Emergency Classification | 20/20 Passed (100%) | **PASS** |
| **Frontend TypeScript Build** | `tsc && vite build` | 0 errors, clean bundle | **PASS** |

---

## 5. Explicit "NOT VALIDATED / SCOPE EXCLUSIONS"

In compliance with strict engineering governance, the following items are explicitly marked as **NOT VALIDATED / OUT OF SCOPE**:
1. Autonomous medical diagnosis or disease probability estimation.
2. Clinical triage scoring or emergency severity index calculation.
3. Automated medication prescription or dosage calculation.
4. LLM free-form generative medical advice beyond retrieved NHS evidence passages.
5. Ingestion of medical knowledge sources outside the 14 approved NHS first-aid conditions.
