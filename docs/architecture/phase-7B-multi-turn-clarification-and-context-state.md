# Phase 7B Architecture — Multi-Turn Clarification & Structured Context State

## 1. System Overview
Phase 7B introduces a **deterministic, non-diagnostic Conversational Clarification & Structured Context State Engine** into the Dr. Md. Momenul Islam Clinical Health Intelligence platform. The subsystem sits between initial turn-level Query Understanding and the validated Candidate B dual-anchor retrieval engine, enabling progressive disambiguation of underspecified patient queries.

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
                    └─────────────────────┘ │  - Precipitating Event / Mechanism   │
                                            │  - Associated Symptoms               │
                                            │  - Duration & Stated Attributes      │
                                            │  (Zero Inferred Diagnoses)           │
                                            └──────────────────┬───────────────────┘
                                                               │
                                                               ▼
                                            ┌──────────────────────────────────────┐
                                            │    Candidate B Refined Retrieval     │
                                            │    (Enriched multi-facet query)      │
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
                                   │  Grounded Answer  │  │  Clarification Planner  │
                                   │  (Action: ANSWER) │  │  (Action: CLARIFY)      │
                                   │  (Policy: SHOW)   │  │  (Policy: SUPPRESS)     │
                                   └───────────────────┘  │  Turn Count <= 3        │
                                                          └─────────────┬───────────┘
                                                                        │ (Turn > 3)
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
- **Prohibited Inferences:** The engine is barred from asserting disease diagnoses, predicting disease probabilities, generating risk scores, suggesting prescription medications, or triaging autonomous clinical acuity.

### 2.2 Hard Clarification Turn Limit
- `MAX_CLARIFICATION_TURNS = 3`.
- The system prevents infinite clarification loops. If a query remains ambiguous after 3 turns, the engine cleanly abstains (`Action: ABSTAIN`, `State: MAX_TURNS_EXCEEDED`).

### 2.3 Retrieval & Normalization Freeze
- Candidate B retrieval hyperparameters remain strictly frozen:
  - Bi-encoder: `intfloat/multilingual-e5-small`
  - Cross-encoder: `BAAI/bge-reranker-v2-m3`
  - Depth: Dense $K=15$, Final Rerank Top-5
  - Compound Disambiguation Rules: `RULE_B1` through `RULE_B7`
  - Corpus: 119 chunks across 14 validated NHS first-aid conditions

---

## 3. Data Contracts

### 3.1 Pydantic Model (`ConversationContextState`)
```python
class ConversationContextState(BaseModel):
    session_id: str = "default-session"
    turn_count: int = 0
    clarification_turn_count: int = 0
    max_clarification_turns: int = 3
    language_modality: str = "en"  # "en", "bn", "banglish"
    response_language_preference: str = "auto"
    symptom: Optional[str] = None
    body_location: Optional[str] = None
    specific_location: Optional[str] = None
    onset: Optional[str] = None
    duration: Optional[str] = None
    severity_stated: Optional[str] = None
    associated_symptoms: List[str] = Field(default_factory=list)
    precipitating_event: Optional[str] = None
    user_age_group: Optional[str] = None
    red_flags: List[str] = Field(default_factory=list)
    relevant_negatives: List[str] = Field(default_factory=list)
    clarification_state: ClarificationState = ClarificationState.NOT_NEEDED
    unanswered_fields: List[str] = Field(default_factory=list)
    next_action: ConversationAction = ConversationAction.ANSWER
    refined_retrieval_query: Optional[str] = None
```

### 3.2 Action Enums
- `ConversationAction`: `ANSWER`, `CLARIFY`, `ABSTAIN`, `EMERGENCY`
- `ClarificationState`: `NOT_NEEDED`, `IN_PROGRESS`, `RESOLVED`, `MAX_TURNS_EXCEEDED`, `UNSUPPORTED_TOPIC`
