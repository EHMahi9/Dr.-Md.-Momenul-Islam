# Grounded Generation Architecture Specification (Phase 6D)

**Project:** Dr. Md. Momenul Islam — Bangladesh-Focused Multilingual Clinical Evidence Retrieval / Health Intelligence Prototype  
**Phase:** 6D — Grounded Generation Architecture Design  
**Date:** 2026-08-29  
**Current Generation Status:** `generation_enabled = false` (LLM Generation Strictly Disabled by Research Protocol)

---

## 1. Executive Summary & Verification Matrix

This document defines the comprehensive architecture for a future grounded Large Language Model (LLM) generation layer. The architecture enforces strict factual grounding against the active 119-chunk NHS clinical corpus, explicit citation traceability, deterministic post-generation validation, and multi-tier safety routing.

### Status Classification Matrix

| Component / Layer | Status | Description |
| :--- | :--- | :--- |
| **Corpus & Retrieval Engine** | `VERIFIED` | 119 active NHS chunks across 14 conditions, frozen Strategy 5 Dual-Anchor Reranker (hash `1cc216db...`). |
| **GenerationService Abstraction** | `DESIGNED & IMPLEMENTED (DISABLED)` | `BaseGenerationService` & `GroundedGenerationService` interface with `generate_answer`, `assess_safety`, and policy mapping. |
| **LLM Provider Abstraction** | `DESIGNED & IMPLEMENTED (DISABLED)` | `BaseLLMProvider` interface with `DisabledLLMProvider` active; `MockLLMProvider` for offline unit testing. |
| **Grounded Prompt Contract** | `DESIGNED` | Structured 5-section prompt schema separating user query, evidence, metadata, system constraints, and emergency triage rules. |
| **Citation & Traceability Schema** | `DESIGNED` | Full `claim → chunk_id → parent_source_id → NHS URL` mapping model with excerpt verification. |
| **Post-Generation Output Validator** | `DESIGNED & IMPLEMENTED` | Deterministic verification of citation indices, detection of fabricated citations, and safety red-flag pattern scanning. |
| **Safety Routing State Machine** | `DESIGNED (AWAITING CLINICAL VALIDATION)` | 8-state heuristic safety classifier distinguishing emergencies, self-harm, diagnosis requests, and medication dosages. |
| **Real Model Integration (Gemini/OpenAI/Ollama)** | `NOT YET IMPLEMENTED` | No live model API connected; no API credentials configured. |
| **LLM Judge / Semantic Consistency** | `NOT YET IMPLEMENTED` | Advanced semantic entailment judges deferred to future evaluation gates. |
| **Clinical Safety Validation** | `NOT YET VALIDATED` | Heuristic thresholds and safety rules are engineering prototypes requiring formal clinical evaluation. |

---

## 2. End-to-End Architectural Pipeline

```
                                  [ User Query ]
                                         │
                                         ▼
                            [ 1. Input Validation ]
                                 (Length ≤ 1000,
                              non-empty, non-whitespace)
                                         │
                                         ▼
                          [ 2. Query Normalization ]
                            (Track A Procedural Map:
                           English / Bangla / Banglish)
                                         │
                                         ▼
                             [ 3. Frozen Retrieval ]
                           (Strategy 5: E5 Dense Top-15
                            + BGE Reranker + Overview
                             Debiasing + Dual Anchor)
                                         │
                                         ▼
                    [ 4. Evidence Sufficiency Assessment ]
                       (Heuristic Score-State Mapping:
                      SUPPORTED / LOW_CONF / MISMATCH /
                                UNSUPPORTED)
                                         │
                                         ▼
                        [ 5. Safety & Intent Routing ]
                      (Classify: SAFE_INFORMATIONAL /
                       EMERGENCY / SELF_HARM / etc.)
                                         │
                                         ▼
                     [ 6. Grounded Prompt Construction ]
                        (Assemble 5-Section Contract:
                       System + Safety + Metadata +
                            Evidence + User Query)
                                         │
                                         ▼
                            [ 7. LLM Provider Layer ]
                     ┌───────────────────────────────────────┐
                     │ ⚠️ CURRENT STATUS: DISABLED           │
                     │ - Returns GenerationStatus.DISABLED   │
                     │ - No outbound network/API call made   │
                     │ - Provider interface ready for future │
                     └───────────────────────────────────────┘
                                         │
                                         ▼
                     [ 8. Post-Generation Output Validation ]
                       (Deterministic: Citation Tag Bounds,
                        Fabrication Detection, Proscribed
                            Phrasing Pattern Scan)
                                         │
                                         ▼
                     [ 9. Citation & Evidence Attachment ]
                        (Build Verified CitationReference
                          Objects with Source Links)
                                         │
                                         ▼
                              [ 10. Final Response ]
                       (Structured GenerationResult inside
                          FastAPI ChatResponse Payload)
```

---

## 3. Grounded Prompt Contract

The grounded prompt builder (`backend/app/services/prompt_builder.py`) constructs a structured, tamper-resistant payload partitioned into 5 explicit sections:

```
=== SECTION A: SYSTEM INSTRUCTIONS ===
- Foundational persona: Evidence synthesis assistant for Dr. Md. Momenul Islam platform.
- Primary rule: Use retrieved NHS evidence as exclusive factual ground truth.
- Strict constraint: Never extrapolate, assume, or invent unstated clinical facts.
- Persona boundary: Do not act as personal doctor; never give definitive individual diagnoses.
- Prescribing rule: Never recommend specific drug dosages or unverified invasive home remedies.
- Insufficient evidence rule: State clearly when evidence is inadequate.

=== SECTION B: SAFETY & TRIAGE RULES ===
- Emergency priority: If red-flag symptoms (chest pain, stroke FAST, severe breathing difficulty, meningitis non-blanching rash, sepsis) are detected, front-load emergency emergency services guidance (Call 999 / hospital emergency).
- Educational disclaimer: Guidance is educational health information under Open Government Licence v3.0.

=== SECTION C: SOURCE METADATA ===
- Active Corpus: NHS 14 Conditions (119 indexed passages).
- Licensing: Open Government Licence v3.0 (NHS England).

=== SECTION D: RETRIEVED CLINICAL EVIDENCE ===
--- EVIDENCE EXCERPT [1] ---
Chunk ID: DOC-NHS-005-HYB-001
Source: Burns and scalds (DOC-NHS-005)
URL: https://www.nhs.uk/conditions/burns-and-scalds/
Content: <Exact verbatim passage text>

--- EVIDENCE EXCERPT [2] ---
...

=== SECTION E: USER INQUIRY ===
User Question: <Normalized / Raw Query>

=== RESPONSE INSTRUCTIONS ===
Synthesize an answer using ONLY excerpts [1]..[N]. Append [1], [2] to every supported claim.
```

---

## 4. Citation and Traceability Contract

To prevent ungrounded assertions or hallucinated sources, the citation architecture guarantees a verifiable 4-stage link:

$$\text{Generated Answer Claim} \xrightarrow{\text{Citation Tag [i]}} \text{Retrieved Chunk ID} \xrightarrow{\text{Provenance}} \text{Parent Source ID} \xrightarrow{\text{OGL v3.0}} \text{Official NHS URL}$$

### Data Contract (`CitationReference`):
- `citation_index`: Integer identifier (e.g. `1`).
- `chunk_id`: Verifiable chunk ID from active corpus (e.g., `DOC-NHS-005-HYB-001`).
- `parent_source_id`: Canonical document identifier (e.g., `DOC-NHS-005`).
- `source_title`: Verified document title (e.g., `Burns and scalds`).
- `source_url`: Official NHS condition URL (`https://www.nhs.uk/conditions/burns-and-scalds/`).
- `excerpt_snippet`: Exact verbatim excerpt (≤150 chars) from the chunk supporting the claim.

**Inviolable Rule:** The system will reject or flag any citation referencing an index not present in the retrieved evidence list ($i < 1$ or $i > N$).

---

## 5. Output Schema & Information Security

The output contract is encapsulated in `GenerationResult` (`backend/app/schemas/generation_models.py`):

```python
class GenerationResult(BaseModel):
    answer: str
    citations: List[CitationReference]
    evidence_ids: List[str]
    confidence_state: RetrievalOutcomeState
    safety_state: GenerationSafetyState
    generation_status: GenerationStatus
    refusal_reason: Optional[str]
    disclaimer: str
    provider_name: str
    model_name: str
    token_usage: Optional[TokenUsageMetadata]
    validation_result: Optional[PostValidationResult]
```

### Security & Privacy Protections:
- **No Hidden Chain-of-Thought:** Internal model reasoning / CoT traces are never returned to clients or logged in production payloads.
- **Explicit Disclaimers:** Every response attaches mandatory clinical prototype disclaimers.
- **Masked Errors:** External provider failures return sanitized error messages with zero API key or host leakage.

---

## 6. Retrieval Outcome & Evidence Sufficiency State Transitions

> [!NOTE]
> **Engineering Heuristic Notice:**  
> The retrieval confidence tiers ($0.65, 0.35, 0.18, 0.10$) are engineering heuristics derived from Strategy 5 score distributions on the development and validation benchmarks. They are **NOT** medically validated safety boundaries.

| Retrieval Outcome State | Fused Score Heuristic | Generation Policy (When Enabled) | Policy Behavior in Phase 6D (Disabled) |
| :--- | :--- | :--- | :--- |
| `SUPPORTED_RETRIEVAL` | $\ge 0.65$ | Allow generation with standard grounding & citations. | Return `DISABLED` notice + Top-5 evidence. |
| `LOW_CONFIDENCE_RETRIEVAL` | $0.35 \le s < 0.65$ | Allow generation with explicit uncertainty warning. | Return `DISABLED` notice + Top-5 evidence. |
| `POSSIBLE_MISMATCH` | $0.18 \le s < 0.35$ | Refuse generation (`REFUSED_INSUFFICIENT_EVIDENCE`); return raw passages with caution notice. | Return `DISABLED` notice + Top-5 evidence. |
| `UNSUPPORTED_BY_ACTIVE_CORPUS` | $0.10 \le s < 0.18$ | Refuse generation (`REFUSED_INSUFFICIENT_EVIDENCE`); inform user question is outside 14 covered conditions. | Return `DISABLED` notice + Out-of-corpus assessment. |
| `NO_RELEVANT_EVIDENCE` | $< 0.10$ | Refuse generation (`REFUSED_INSUFFICIENT_EVIDENCE`); recommend consulting clinical professional. | Return `DISABLED` notice + No evidence message. |
| `INVALID_QUERY` | N/A | Refuse generation; return HTTP 400 Bad Request. | Return HTTP 400 Bad Request. |

---

## 7. Safety Routing State Machine (Design Specification)

The safety classifier evaluates queries across 8 categorical states:

1. `SAFE_INFORMATIONAL`: Standard first-aid and self-management queries matching active corpus conditions.
2. `POSSIBLE_EMERGENCY`: Queries exhibiting acute red-flag symptoms (severe chest pain, stroke FAST signs, severe difficulty breathing, non-blanching purpuric rash, sepsis indicators). Front-loads emergency contact advice.
3. `HIGH_RISK_MEDICAL`: Queries involving high-vulnerability demographics (infants under 3 months with fever, pregnancy complications).
4. `DIAGNOSIS_SEEKING`: Queries asking "Do I have disease X?" Deflects individual diagnosis and emphasizes clinical consultation.
5. `MEDICATION_OR_TREATMENT_REQUEST`: Queries asking for specific drug dosages or prescription guidance. Deflects prescription requests.
6. `SELF_HARM_OR_CRISIS`: Queries mentioning self-harm or suicide. Immediately halts medical retrieval and provides crisis helpline information.
7. `UNSUPPORTED_TOPIC`: Queries outside the 14 active conditions.
8. `SAFETY_REVIEW_REQUIRED`: Unclassified or conflicting multi-intent inquiries.

---

## 8. Provider Abstraction & Secret Management

### Provider Interface (`BaseLLMProvider`):
- Clean interface: `complete(LLMRequest) -> LLMResponse`
- Decoupled from concrete vendors (Gemini, OpenAI, Anthropic, Ollama).
- Standardized `TokenUsageMetadata` and latency tracking.

### Security Rules:
1. **Zero Hardcoded Secrets:** Model API keys are loaded exclusively at runtime from environment variables (`LLM_API_KEY_ENV_VAR = "LLM_API_KEY"`).
2. **Default Disabled:** `GENERATION_ENABLED = False` is enforced in `AppSettings`.
3. **Timeout & Retries:** Strict limits (`timeout = 30s`, `max_retries = 2`) to prevent thread hangs.

---

## 9. Frontend Generation States

The frontend (`ChatMessageItem.tsx` and `types/index.ts`) supports 6 distinct generation states:

- `DISABLED`: Clean amber Research Mode Notice explaining generation is locked by protocol.
- `GENERATING`: Animated pulsing indicator during active inference.
- `COMPLETED`: Grounded response with interactive inline `CitationLink` components and disclaimer.
- `REFUSED_SAFETY`: High-priority rose safety banner explaining emergency or risk guardrail.
- `REFUSED_INSUFFICIENT_EVIDENCE`: Informative amber notice stating evidence is inadequate.
- `FAILED`: Clear error message with retry option.
