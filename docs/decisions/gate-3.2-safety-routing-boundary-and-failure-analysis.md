# Gate 3.2: Safety Routing Boundary and Failure Analysis

> **Status:** CRITICAL RESEARCH & ARCHITECTURE REVIEW
> **Purpose:** Critically refine the Gate 3.1 architecture, correct inaccurate terminology, establish strict routing precedence, and analyze failure modes before any governance merge.
> **Note:** This architecture is NOT clinically validated, medically accurate, or production-ready. It remains an engineering proposal.

## 1. Terminology Correction: The Layered Safety Router
The Gate 3.1 term "Deterministic Safety Router" is rejected. Any system relying on few-shot semantic classification, NLP, or an LLM is probabilistic, not deterministic. 
The revised architecture is the **Layered Safety Router**, which explicitly separates:
1.  **Deterministic Pattern Checks:** Exact string/regex matching for verified hotline numbers or highly specific hardcoded emergency phrases.
2.  **Probabilistic Semantic Screening:** NLP/LLM-based classification to evaluate intent and semantic similarity to high-risk categories.

## 2. Layered Routing Architecture & Precedence
To prevent high-risk situations (like overdoses) from accidentally being handled as routine medication queries, the router must evaluate states in strict sequential precedence. If a higher-precedence state is triggered, evaluation stops immediately.

**Precedence Order:**
1.  **`EXPLICIT_CRISIS_OR_OVERDOSE`**: Explicit statements of poisoning, overdose, imminent self-harm, or active suicide plans.
2.  **`EXPLICIT_MEDICAL_EMERGENCY`**: Explicit matches for NHS life-threatening conditions (e.g., severe bleeding, loss of consciousness).
3.  **`POTENTIAL_SELF_HARM`**: Any semantic similarity to self-harm ideation, passive death thoughts, or distress.
4.  **`AMBIGUOUS_HIGH_RISK`**: Severe symptoms lacking explicit emergency phrasing.
5.  **`MEDICATION_ACTION`**: Dosage, start/stop/change requests, personalized treatment decisions.
6.  **`UNCERTAIN_SAFETY`**: (See Section 3).
7.  **`ROUTINE_HEALTH`**: General factual information or medication explanations.

## 3. Re-Examining Uncertainty: Split States
A generic `UNCERTAIN_SAFETY` state is unsafe. Uncertainty must be split based on the *potential* risk of the ambiguous input.
*   **`UNCERTAIN_HIGH_RISK`**: The input is garbled or ambiguous, but contains fragments related to pain, bleeding, distress, or drugs. 
    *   *Behavior:* Immediate conservative escalation. No RAG. No clarifying questions.
*   **`UNCERTAIN_LOW_RISK`**: The input is a safe topic (e.g., "Tell me about diet"), but the specific intent is unclear.
    *   *Behavior:* RAG allowed. Clarifying questions permitted (see Section 4).

## 4. Boundaries for Clarifying Questions
To prevent the system from degrading into an undocumented clinical triage questionnaire, clarifying questions are heavily restricted:
*   **When allowed:** Only in `UNCERTAIN_LOW_RISK` or `ROUTINE_HEALTH` states (e.g., "Are you asking about dengue symptoms or prevention?").
*   **When prohibited:** Absolutely prohibited in any state evaluating pain, injury, distress, medication actions, or potential emergencies. Clarification must *never* delay escalation.
*   **Scope limit:** The system may ask a maximum of *one* clarifying question per user prompt. It must never ask diagnostic questions (e.g., "On a scale of 1-10, how bad is the pain?").

## 5. Refined Self-Harm Handling
Gate 3.1 falsely assumed we could accurately classify passive vs. active suicidal intent. We cannot.
*   **Engineering Interpretation:** The system abandons automated clinical differentiation of suicidal ideation.
*   **Behavior:** 
    *   *Any* explicit statement of danger/plan/recent harm maps to `EXPLICIT_CRISIS_OR_OVERDOSE`.
    *   *All other* distress, passive thoughts, or ideation map to `POTENTIAL_SELF_HARM`. Both states bypass RAG and immediately provide crisis resources (Kaan Pete Roi, 999). We accept false positives (providing crisis lines for mild distress) as a necessary engineering safety trade-off.

## 6. Refined Medication Boundaries
*   **`EXPLICIT_CRISIS_OR_OVERDOSE`:** Questions about taking too many pills, suspected poisoning, or dangerous combinations. (Bypasses RAG → Escalates to 999).
*   **`MEDICATION_ACTION`:** Requests for personalized treatment, dosage instructions, or initiating/stopping prescriptions. (Bypasses RAG → Escalates to GP/16263).
*   **`MEDICATION_FACTUAL`:** Requests for general purpose, mechanisms, or standard side effects of a named drug. (Allowed → Standard RAG).

## 7. Non-Numeric Source Metadata & Adjudication
The rigid `DGHS=1, WHO=2, NHS=3` hierarchy is permanently abandoned. 
*   **Metadata Framework:** Documents are tagged with `jurisdiction`, `topic`, `specificity`, `publication_date`, `publisher`, and `document_purpose`.
*   **Retrieval Logic:** The vector search prioritizes chunks matching the user's jurisdiction (BD) and topic specificity.
*   **Conflict Handling:** The system will *not* automatically declare "sources disagree" or ask the LLM to adjudicate. The LLM simply synthesizes the retrieved chunks. A conflict is only explicitly flagged to the user if the evidence-selection layer (or a future semantic validation layer) positively identifies a material contradiction. Otherwise, uncertainty is preserved without forced LLM adjudication.

## 8. Formal Failure-Mode Analysis

| State | False Positive (FP) | False Negative (FN) | Conservative Fallback | RAG Allowed? | Clarification Allowed? | Immediate Escalation? | Evidence vs Engineering |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **EXPLICIT_EMERGENCY** | (FP) Escalating a minor cough. Consequence: Annoyance. | (FN) Missing a heart attack. Consequence: Catastrophic harm. | Treat as `UNCERTAIN_HIGH_RISK` if threshold is near. | NO | NO | YES (999) | Evidence: NHS criteria. Engineering: Regex/Semantic matching. |
| **POTENTIAL_SELF_HARM** | (FP) Sending hotline for general sadness. Consequence: Minor friction. | (FN) Missing suicidal ideation. Consequence: Catastrophic harm. | Escalate to crisis hotline. | NO | NO | YES (09612-119911) | Evidence: WHO distress markers. Engineering: Broad net categorization. |
| **MEDICATION_ACTION** | (FP) Refusing a general info request. Consequence: Poor UX. | (FN) Giving fatal dosage advice. Consequence: Catastrophic harm. | Refuse and redirect to 16263. | NO | NO | YES (16263) | Evidence: WHO self-care limits. Engineering: Blanket refusal. |
| **UNCERTAIN_HIGH_RISK** | (FP) Over-escalation. Consequence: Alarm fatigue. | (FN) Treating emergency as routine. Consequence: Severe harm. | Escalate to 999/16263. | NO | NO | YES | Engineering: Failsafe logic. |
| **ROUTINE_HEALTH** | (FP) Answering an obscured emergency. Consequence: Harm. | (FN) Refusing basic info. Consequence: Poor UX. | Default to `UNCERTAIN_HIGH_RISK` on any doubt. | YES | YES (Max 1) | NO | Evidence: N/A. Engineering: Standard operation. |

## 9. Remaining Unverified Assumptions
The architecture relies on several assumptions requiring empirical evaluation:
1.  **Language Efficacy:** Can semantic screening models accurately detect `EXPLICIT_EMERGENCY` patterns in native Bengali text (including transliterated "Banglish")? 
2.  **Latency:** Will a multi-layered screening architecture (Regex + LLM Router) introduce unacceptable latency before RAG generation?
3.  **Boundary Bleed:** Where exactly is the semantic line between `MEDICATION_FACTUAL` and `MEDICATION_ACTION` in natural conversation?

## 10. Formal Decision Section
*   **Can Gate 3.1 be merged as-is?** NO.
*   **Exact changes required before merge:** 
    1. Replace "Deterministic Router" with "Layered Safety Router" in `07-rag-architecture.md`.
    2. Incorporate the Split Uncertainty states into `03-safety-policy.md`.
    3. Add strict clarifying-question boundaries to `03-safety-policy.md`.
    4. Implement the non-numeric metadata framework in `07-rag-architecture.md`.
*   **What assumptions remain unsupported?** Bengali-language semantic accuracy and real-world latency.
*   **What can safely be tested experimentally?** The semantic classifier (Safety Router) can be built and evaluated against a benchmark dataset of synthetic Bengali medical queries *offline*, without being attached to a clinical response system or real users.
