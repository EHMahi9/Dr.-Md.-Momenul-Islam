# Phase 7C Architecture Decision Record — Adaptive Clarification & Conversation Quality

## Context
In Phase 7B, the system introduced a deterministic multi-turn clarification engine that successfully resolved underspecified queries such as "amar paye betha". However, the baseline question selection used static heuristics rather than dynamic value-of-information estimation. Consequently:
1. Questions were sometimes asked even when retrieved evidence was already sufficient.
2. Clarification continued on out-of-corpus queries where no answer could ever be supported.
3. The system lacked an explicit mathematical utility model to explain question prioritization.

## Decision
We adopted an **Adaptive, Utility-Driven Clarification Planner** governed by:
1. **Mathematical Question-Utility Formulation:**
   $$\text{Utility}(Q) = G_{\text{retrieval}}(Q) + G_{\text{safety}}(Q) + R_{\text{ambiguity}}(Q) + C_{\text{corpus}}(Q) - P_{\text{redundant}}(Q) - P_{\text{unnecessary}}(Q)$$
2. **Four Deterministic Stopping Rules:**
   - Rule A: Stop immediately when top chunk rerank score $\ge 0.65$ (`SUFFICIENT_EVIDENCE`).
   - Rule B: Stop and abstain when topic is out-of-corpus (`UNSUPPORTED_TOPIC`).
   - Rule C: Bypass clarification when red flags occur (`EMERGENCY_OVERRIDE`).
   - Rule D: Halt at turn 3 (`MAX_TURNS_EXCEEDED`).
3. **Structured Context State Auditability:**
   Expose `asked_questions`, `candidate_question_scores`, `stopping_reason`, and `selection_rationale` directly in the API schema.
4. **Strict Invariant Maintenance:**
   - Zero autonomous disease diagnosis or disease probability scoring.
   - Strictly frozen Candidate B dual-anchor retrieval parameters.

## Consequences & Trade-offs
- **Positive:** Reduces average turns for well-specified and out-of-corpus queries. Eliminates duplicate questions across turns. Ensures complete auditability of clarification choices.
- **Trade-off:** Evaluation across 40 multi-turn scenarios requires cross-encoder inference for all candidate checks, necessitating efficient caching and non-blocking background evaluation.
