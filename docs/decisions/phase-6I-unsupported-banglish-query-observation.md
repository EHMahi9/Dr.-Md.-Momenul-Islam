# Decision Record: Phase 6I — Unsupported Banglish Query Diagnostic Observation

**Date:** 2026-08-29  
**Status:** Diagnostic Audit Completed (No Code Changes)  
**Query Investigated:** `"amar peet e betha"`  
**Observed Behavior:** UI displayed *"No Supporting Evidence Found"* alongside Top-1 passage `DOC-NHS-005` (Burns and scalds).  
**Artifact Trace:** [`research/phase_6I_candidate_freeze/diagnostics/unsupported_banglish_peet_betha_trace.json`](file:///d:/my-ai-project/Dr.%20Md.%20Momenul%20Islam/research/phase_6I_candidate_freeze/diagnostics/unsupported_banglish_peet_betha_trace.json)  

---

## 1. Query Normalization Trace

### Token-Level Analysis (VERIFIED FACT)
- **Raw Input:** `"amar peet e betha"` (Bengali/Banglish intent: *"I have stomach/belly pain"* or *"I have back pain"*).
- **Track A Normalization:** Matched **0 rules**. Query passed through unchanged.
  - Reason: Track A includes `matha betha` (headache), but does not have a generic `betha` rule or any rule for `peet`/`pet`.
- **Candidate B Normalization:** Matched **0 rules**. Query passed through unchanged.
  - Reason: Candidate B compound rules include `buk + betha` (heartburn) and `mathar ekpashe + betha` (migraine), but have no compound rule for `peet` or general abdominal pain.
- **Normalized Query sent to Embedding Model:** `"amar peet e betha"`.

---

## 2. Retrieval & Reranking Trace

### Dense Candidate Pool (VERIFIED FACT)
`multilingual-e5-small` encoded `"query: amar peet e betha"` and returned 15 candidate passages. All dense similarity scores fell into a narrow baseline noise band between `0.7747` and `0.8068`.

### Cross-Encoder Reranking & Dual Anchor Blend (VERIFIED FACT)
`BAAI/bge-reranker-v2-m3` evaluated all 15 candidates against `"amar peet e betha"`:

| Rank | Chunk ID | Document / Topic | Raw Cross-Encoder | Dense Score | Dense Boost ($0.10 \times d$) | Token Overlap | Lexical Boost ($0.03 \times l$) | Final Fused Score |
| :---: | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **1** | `DOC-NHS-005-HYB-002` | Burns and scalds | `0.0000` | 0.7916 | +0.0792 | 0.2500 (matched `"e"`) | +0.0075 | **0.0867** |
| **2** | `DOC-NHS-006-HYB-005` | Cuts and grazes | `0.0000` | 0.7803 | +0.0780 | 0.2500 (matched `"e"`) | +0.0075 | **0.0856** |
| **3** | `DOC-NHS-009-HYB-003` | Headaches | `0.0000` | 0.7800 | +0.0780 | 0.2500 (matched `"e"`) | +0.0075 | **0.0855** |
| **4** | `DOC-NHS-007-HYB-004` | Dehydration | `0.0000` | 0.7786 | +0.0779 | 0.2500 (matched `"e"`) | +0.0075 | **0.0854** |
| **5** | `DOC-NHS-016-HYB-001` | Nosebleed | `0.0000` | 0.7752 | +0.0775 | 0.2500 (matched `"e"`) | +0.0075 | **0.0851** |

### Why Did Burns Become Top-1? (VERIFIED FACT)
1. The cross-encoder scored **every candidate at essentially zero** (`0.0000` to `0.0004`), correctly recognizing that none of the passages in the 14-condition corpus are semantically relevant to stomach pain.
2. Because neural relevance is zero, the fused scores represent **pure background residual noise** ($\lambda \times \text{dense} + \alpha \times \text{lexical}$).
3. `DOC-NHS-005-HYB-002` had a slightly higher random cosine density (`0.7916` vs `0.7800`) plus a spurious 1-character token match on `"e"` (e.g. from `"e.g."` or English text), yielding a fused score of `0.0867`.
4. **Conclusion:** Burns was not selected due to a clinical semantic hallucination; it emerged at position 1 purely as the highest arbitrary point in a sub-0.09 noise distribution.

---

## 3. Confidence Assessment & Abstention Trace

### Backend Classification Logic (VERIFIED FACT)
The confidence classifier [`classify_retrieval_outcome`](file:///d:/my-ai-project/Dr.%20Md.%20Momenul%20Islam/backend/app/services/retrieval_service.py#L66-L127) evaluated the top score `0.0867`:

- **Threshold ladder:**
  - $\text{Score} \ge 0.65 \implies \text{SUPPORTED\_RETRIEVAL}$ (HIGH)
  - $\text{Score} \ge 0.35 \implies \text{LOW\_CONFIDENCE\_RETRIEVAL}$ (MODERATE)
  - $\text{Score} \ge 0.18 \implies \text{POSSIBLE\_MISMATCH}$ (LOW)
  - $\text{Score} \ge 0.10 \implies \text{UNSUPPORTED\_BY\_ACTIVE\_CORPUS}$ (VERY\_LOW)
  - $\mathbf{\text{Score} < 0.10 \implies \text{NO\_RELEVANT\_EVIDENCE}}$ (NONE)
- **Computed Outcome:**
  - `state`: `NO_RELEVANT_EVIDENCE`
  - `confidence_level`: `NONE`
  - `top_score`: `0.0867`
  - `score_spread`: `0.0016`
  - `summary_reason`: *"No relevant clinical evidence found in the active knowledge base for this query."*

### Abstention Evaluation (VERIFIED FACT)
The backend abstention decision is **100% mathematically and semantically correct**. The cross-encoder rejected the passages, and the classifier correctly concluded that the active corpus contains no evidence for this query.

---

## 4. UI Semantic Audit & UX Safety Hazard

### Frontend Rendering Path (SAFETY/UX ISSUE)
In [`ChatMessageItem.tsx`](file:///d:/my-ai-project/Dr.%20Md.%20Momenul%20Islam/frontend/src/components/ChatMessageItem.tsx):

1. **Outcome Box (Lines 79-86, 186-190):** Correctly renders the grey badge:
   `[AlertCircle] No Supporting Evidence Found`
   `Assessment: No relevant clinical evidence found in the active knowledge base for this query.`
2. **Evidence Section (Lines 197-223):** However, immediately underneath, because `evidence.length = 5`, the UI unconditionally renders:
   `[Layers icon] Top-5 Grounding Evidence Passages`
   with expandable cards displaying:
   `Rank 1: Burns and scalds - NHS (Score: 0.0867)`
   `Text: "cool the burn with cool or lukewarm running water for 20 minutes..."`

### Clinical Hazard Analysis (SAFETY/UX ISSUE)
- To a lay patient asking in Banglish about **stomach pain** (`amar peet e betha`), presenting an expandable section labeled **"Grounding Evidence Passages"** that prominently features first aid for **Burns and Scalds** creates severe cognitive ambiguity.
- The user may overlook the small "No Supporting Evidence" pill and read the Burns passage as suggested treatment, or conclude the system is clinically erratic.
- **Root Cause:** The UI conflates **"Grounding Evidence"** (which requires high/moderate confidence) with **"Raw Nearest Retrieval Candidates"** (which are returned for debugging/audit purposes even on rejected queries).

---

## 5. Formal Safety Classification

Based on empirical traces, this event is classified as:

### **`CORRECT_ABSTENTION_WITH_MISLEADING_UI_EVIDENCE_FRAMING`**

- **Neural Cross-Encoder:** Correct rejection ($\text{Score} \approx 0.000$).
- **Classifier Gate:** Correct abstention (`NO_RELEVANT_EVIDENCE`, Confidence `NONE`).
- **Retrieval Engine:** Correctly identified that query is out-of-corpus / unmapped.
- **Frontend Presentation:** Defect in evidence framing. The UI displays rejected noise passages under an affirmative label ("Grounding Evidence Passages") instead of suppressing them or labeling them as "Nearest Unrelated Candidates (Rejected)".

---

## 6. Epistemic Classification

| Statement | Classification |
| :--- | :---: |
| Neither Track A nor Candidate B has normalization rules for isolated `peet` or `betha` | **VERIFIED FACT** |
| BGE cross-encoder scored all 15 candidates near 0.0000 | **VERIFIED FACT** |
| Top score 0.0867 is below the 0.10 threshold, yielding `NO_RELEVANT_EVIDENCE` | **VERIFIED FACT** |
| Burns became Top-1 due to baseline dense cosine noise and 1-character token match on `"e"` | **VERIFIED FACT** |
| The UI labels rejected sub-0.10 noise candidates as "Grounding Evidence Passages" | **VERIFIED FACT** |
| Lay health users could misinterpret the Burns evidence card as clinical advice | **SAFETY/UX ISSUE** |
| Normalizing `peet e betha` to abdominal pain will route to `DOC-NHS-007`/`008` (GI) | **HYPOTHESIS** |
| Adding UI conditional evidence hiding when outcome is `NO_RELEVANT_EVIDENCE` | **VALIDATION PLAN (FUTURE)** |

---

## 7. Safety & Freeze Boundary Adherence

As instructed by Phase 6I safety protocols:
- ❌ **NO normalization rules were added** for `peet` or `betha`.
- ❌ **NO changes were made to Candidate B** or its frozen configuration.
- ❌ **NO changes were made to Strategy 5 production code.**
- ❌ **NO threshold or reranker changes were made.**
- ❌ **NO locked benchmarks were executed.**
- ❌ **NO UI code was modified in this phase.**

This document constitutes an isolated empirical diagnosis only.
