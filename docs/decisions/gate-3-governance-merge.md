# Gate 3 Governance Merge Proposal

> **Status:** APPROVED FOR MERGE PREPARATION
> **Purpose:** Identify exact conclusions from Gate 3 research approved for integration into governing documents (`03-safety-policy.md` and `07-rag-architecture.md`). 
> **Important:** This document lists the *principles* to be merged. It does not select a final model, contain benchmark scores, or make clinical evidence claims.

## 1. Principles Approved for `docs/03-safety-policy.md`

The following principles are approved to update the Safety Policy, consistent with existing rules:

*   **LLM Role Limitation:** The LLM is not the clinical decision-maker. It is strictly a language processing engine.
*   **Safety vs. Diagnosis:** Safety routing is an engineering safeguard designed to appropriately route user queries. It is NOT a clinical diagnosis or medical triage system.
*   **Self-Harm Conservatism:** Handling of potential self-harm queries remains strictly conservative. The system must not claim to perform clinical suicide-risk assessment.
*   **Explicit Uncertainty:** Uncertainty in intent or medical severity must be made explicit in the routing state. Ambiguous potentially high-risk inputs must follow the predefined conservative fallback for their routing category. The system must not invent a clinical severity level from uncertainty.
*   **Bounded Medication:** Medication action requests must remain strictly bounded; the system cannot authorize or prescribe medication adjustments.
*   **Conflict Resolution:** Medical source conflicts must not be adjudicated by asking the LLM to determine medical truth.

## 2. Principles Approved for `docs/07-rag-architecture.md`

The following principles are approved to update the RAG Architecture:

*   **Pre-RAG Screening:** Safety screening must occur strictly *before* normal RAG retrieval and generation phases begin.
*   **Mandatory Determinism:** Deterministic high-confidence safety checks (e.g., regex/keyword rules for explicit crises) remain a mandatory first layer.
*   **Input Distributions:** Bangla and Romanized Bangla (Banglish) are materially different input distributions. The architecture must account for both without assuming native models will zero-shot transfer successfully to Banglish without structural support.
*   **Engineering Candidates:** MuRIL and a transliteration-pipeline approach remain active engineering candidates for the semantic screening layer. Neither is selected as the mandatory final architecture choice yet.
*   **Model Restrictions:** BanglaBERT-small remains research-only under the current project decision and will not be integrated into the production architecture.

## 3. Exclusions (Deliberately NOT Merged)

The following items are explicitly excluded from governance documents:

*   **Benchmark Scores:** No quantitative metrics (e.g., F1 scores, recall percentages) from Gates 3.3A-3.3E will be added to the safety policy. They are engineering research artifacts, not clinical evidence.
*   **Final Semantic Model Selection:** No final decision between MuRIL and the transliteration pipeline is made.
*   **Live Implementation Details:** No production code, API endpoints, or active ingestion configurations are merged yet.
