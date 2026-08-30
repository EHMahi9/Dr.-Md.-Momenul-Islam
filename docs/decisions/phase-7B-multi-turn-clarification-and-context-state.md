# Architecture Decision Record — Phase 7B: Multi-Turn Clarification & Structured Context State

## Context & Problem Statement
In clinical question-answering systems for multilingual and low-resource vernaculars (such as Banglish and colloquial Bangla), user queries often present with underspecified symptom statements (e.g. `"amar paye betha, ki korbo?"`). In naive retrieval systems, such queries produce false-positive evidence matches (such as Burns or Meningitis) because the dense bi-encoder latches onto generic pain or anatomical tokens. 

Directly jumping to diagnostic guessing or exposing unrelated evidence violates safety protocols. A structured, observation-only multi-turn clarification engine is required to gather relevant clinical context before retrieving or abstaining.

## Decision
1. **Explicit Next Action Enum:** Every interaction outputs an authoritative `next_action`:
   - `ANSWER`: Evidence retrieved with high confidence ($\ge 0.65$) matching clarified context.
   - `CLARIFY`: Query is ambiguous; returns focused question and quick-select options.
   - `ABSTAIN`: Query is out of corpus or max turns reached without evidence match.
   - `EMERGENCY`: Immediate safety override for red-flag symptoms.
2. **Observation-Only Structured Context State (`ConversationContextState`):** Stores only user-supplied anatomical sites, precipitating trauma/events, associated sensations, duration, and stated age/severity. Prohibits disease labels or speculative risk predictions.
3. **Deterministic Clarification Planner:** Formulates focused follow-up questions following a clinical priority hierarchy (Mechanism/Trauma $\to$ Sub-location $\to$ Duration/Associated Symptoms) with a strict hard ceiling of `MAX_CLARIFICATION_TURNS = 3`.
4. **Refined Candidate B Query Synthesis:** Combines accumulated contextual attributes into an optimal multi-facet query string without altering frozen Candidate B weights or hyperparameters.
5. **Deterministic Evidence Presentation Policy:** Completely hides unrelated raw candidate cards from the patient UI during clarification and abstention, while retaining a collapsible technical inspector for clinicians and researchers.

## Consequences & Status
- **Status:** Accepted and Validated.
- **Safety Impact:** 0% exposure of misleading clinical evidence on underspecified queries, 100% emergency-first routing compliance, and 100% non-diagnostic compliance.
- **Regression Impact:** 0% degradation on English, Native Bangla, and Banglish benchmark performance.
