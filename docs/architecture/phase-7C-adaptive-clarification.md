# Phase 7C Architecture — Adaptive Clarification & Conversation Quality

## 1. System Overview
Phase 7C upgrades the conversational clarification engine of the Dr. Md. Momenul Islam Clinical Health Intelligence platform from deterministic sequential question flows to an **Adaptive, Utility-Driven Clarification Planner**.

Rather than asking static clarification questions, the Phase 7C planner evaluates candidate clarification dimensions in real-time, computing an explicit **Question Utility Score** based on current user context, missing retrieval facets, corpus relevance, safety routing, and past turn history.

```
                      ┌─────────────────────────────────────────┐
                      │          User Message (Turn t)          │
                      └────────────────────┬────────────────────┘
                                           │
                                           ▼
                      ┌─────────────────────────────────────────┐
                      │    Query Understanding & Red-Flags      │
                      └────────┬───────────────────────┬────────┘
                               │ (Emergency)           │ (General / Underspecified)
                               ▼                       ▼
                     ┌─────────────────────┐ ┌──────────────────────────────────────┐
                     │ Emergency Override  │ │  Structured Context State Updater    │
                     │ (Policy: OVERRIDE)  │ │  - Specific Anatomical Site          │
                     │ (Stop: EMERGENCY)   │ │  - Precipitating Event / Mechanism   │
                     └─────────────────────┘ │  - Associated Sensations             │
                                             │  - Stated Duration & Demographics    │
                                             │  - Track asked_questions             │
                                             └──────────────────┬───────────────────┘
                                                                │
                                                                ▼
                                             ┌──────────────────────────────────────┐
                                             │    Candidate B Dual-Anchor Retrieval │
                                             │    (Bi-encoder + Cross-Encoder)      │
                                             └──────────────────┬───────────────────┘
                                                                │
                                                                ▼
                                             ┌──────────────────────────────────────┐
                                             │     Evidence Sufficiency Assessor    │
                                             └────────┬──────────────┬──────────────┘
                                                      │              │
                                    (Sufficient Match)│              │(Insufficient / Vague)
                                                      ▼              ▼
                                    ┌───────────────────┐  ┌─────────────────────────┐
                                    │  Grounded Answer  │  │  Adaptive Planner       │
                                    │  (Action: ANSWER) │  │  (Action: CLARIFY)      │
                                    │  (Policy: SHOW)   │  │  - Compute Utility(Q)   │
                                    │  (Stop: SUFFICIENT│  │  - Rank Candidates      │
                                    └───────────────────┘  │  - Check Early Stops    │
                                                           └─────────────┬───────────┘
                                                                         │ (Turn > 3 or
                                                                         │  Unsupported)
                                                                         ▼
                                                           ┌─────────────────────────┐
                                                           │   Honest Abstention     │
                                                           │   (Action: ABSTAIN)     │
                                                           │   (Policy: SUPPRESS)    │
                                                           └─────────────────────────┘
```

---

## 2. Core Safety Boundaries & Invariants

### 2.1 Non-Diagnostic Invariance
- The structured context state (`ConversationContextState`) tracks **strictly observable clinical facts** explicitly communicated by the user (symptom, body location, sub-location, precipitating trauma/event, associated sensations, user-stated duration, user-stated age/severity).
- **Prohibited Inferences:** The system is barred from asserting disease diagnoses, predicting disease probabilities, generating risk scores, suggesting prescription medications, or triaging autonomous clinical acuity.
- **Observable Quick-Selects:** Quick-select options represent user-observable anatomical sites or events (e.g. `[পায়ের পাতা]`, `[গোড়ালি]`, `[আঘাতের পরে]`), never diagnostic labels (e.g. `[Sciatica]`, `[Gout]`).

### 2.2 Hard Clarification Turn Limit & Early Stopping
- `MAX_CLARIFICATION_TURNS = 3`.
- The planner enforces four explicit stopping rules:
  1. **Rule A (Sufficient Evidence):** When retrieved evidence rerank score meets sufficiency threshold (>= 0.65).
  2. **Rule B (Unsupported Topic):** When user specifies an out-of-corpus mechanism or unanswerable topic (e.g. fracture/sprain), the system stops clarifying immediately and abstains.
  3. **Rule C (Emergency Red Flag):** When red flags appear, clarification is bypassed immediately for the emergency directive.
  4. **Rule D (Turn Limit):** When `turn_count >= 3`, clarification halts and the system produces an honest abstention.

### 2.3 Retrieval & Normalization Freeze
- Candidate B retrieval hyperparameters remain strictly frozen:
  - Bi-encoder: `intfloat/multilingual-e5-small`
  - Cross-encoder: `BAAI/bge-reranker-v2-m3`
  - Depth: Dense K=15, Final Rerank Top-5
  - Anchors: Dual topical + lexical anchors (lambda=0.10, alpha=0.03, overview debiasing 0.85).
  - Active Corpus: 119 chunks across 14 verified NHS documents (`DOC-NHS-004` through `DOC-NHS-017`).

---

## 3. Question-Utility Model Formulation

The utility of a candidate question $Q$ targeting missing clinical field $F$ is calculated via:

$$\text{Utility}(Q) = G_{\text{retrieval}}(Q) + G_{\text{safety}}(Q) + R_{\text{ambiguity}}(Q) + C_{\text{corpus}}(Q) - P_{\text{redundant}}(Q) - P_{\text{unnecessary}}(Q)$$

### Component Definitions & Calibration:

1. **Retrieval Information Gain ($G_{\text{retrieval}} \in [0.0, 0.40]$):**
   - Anatomical Sub-Location: $+0.35$ (critical for differentiating foot pain, knee pain, calf pain).
   - Mechanism / Precipitating Event: $+0.30$ (distinguishes trauma vs non-trauma NHS guidance).
   - Associated Sensations: $+0.20$.
   - Patient Profile / Demographics: $+0.10$.

2. **Safety Gain ($G_{\text{safety}} \in [0.0, 0.30]$):**
   - High-risk symptom contexts (e.g. burn mechanism, red-flag exclusion): $+0.25$.
   - Standard symptoms: $+0.10$.

3. **Ambiguity Reduction ($R_{\text{ambiguity}} \in [0.0, 0.30]$):**
   - Sub-location when broad body part is present: $+0.25$.
   - Duration / progression: $+0.15$.

4. **Corpus Relevance ($C_{\text{corpus}} \in [-0.50, +0.20]$):**
   - Topic strongly covered in active corpus: $+0.15$.
   - Topic out-of-corpus: $-0.50$ (suppresses questions on unanswerable topics).

5. **Redundancy Penalty ($P_{\text{redundant}} \in \{0.0, 1.0\}$):**
   - If field already populated or question dimension $\in \text{asked\_questions}$: $-1.00$.

6. **Unnecessary Question Penalty ($P_{\text{unnecessary}} \in [0.0, 0.60]$):**
   - If existing evidence rerank score $\ge 0.65$: $-0.60$.
   - If existing evidence rerank score $\ge 0.55$: $-0.30$.

---

## 4. Structured Context State Extensions

The Pydantic model `ConversationContextState` is extended with the following Phase 7C fields:

| Field | Type | Description |
| :--- | :--- | :--- |
| `asked_questions` | `List[str]` | Set of question dimension keys asked in previous turns (e.g., `["sub_location", "mechanism"]`) |
| `missing_high_value_fields` | `List[str]` | Dynamically identified missing information fields with positive utility |
| `candidate_question_scores` | `List[CandidateScore]` | Audit trail of evaluated candidate questions and scores |
| `stopping_reason` | `Optional[str]` | Machine-readable explanation for stopping clarification (`SUFFICIENT_EVIDENCE`, `UNSUPPORTED_TOPIC`, `EMERGENCY_OVERRIDE`, `MAX_TURNS_EXCEEDED`) |
| `utility_score` | `Optional[float]` | The computed utility score of the selected clarification question |
| `selection_rationale` | `Optional[str]` | Human-readable explanation of why this question was selected over alternatives |

---

## 5. Multilingual & Script Support
All generated clarification questions and quick-select options support:
- English (`en`)
- Bengali Standard Script (`bn`)
- Banglish / Romanized Bengali (`banglish`)

Regex entity extractors and normalizers extract free-text responses and quick-select clicks uniformly across all three representations without loss of context.
