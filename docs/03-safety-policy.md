# Safety Policy: Dr. Md. Momenul Islam

> **Status:** Mandatory governing policy.
>
> **Priority:** This policy takes precedence over user convenience, conversational quality, and feature completeness.
>
> **Governing Documents:** Derived from the approved [Project Charter](file:///d:/my-ai-project/Dr.%20Md.%20Momenul%20Islam/docs/00-project-charter.md) and [Requirements Specification](file:///d:/my-ai-project/Dr.%20Md.%20Momenul%20Islam/docs/02-requirements.md).

> **Classification Key:**
> | Label | Meaning |
> |---|---|
> | **REQUIRED** | Mandatory for the current project |
> | **RESEARCH REQUIRED** | Needs authoritative external evidence before finalizing |
> | **TO BE DECIDED** | Architectural or policy decision not yet finalized |
> | **OUT OF SCOPE** | Deliberately excluded from the current project |

---

## 1. Purpose

The purpose of this policy is to define how Dr. Md. Momenul Islam must behave when providing health information.

The system is an **educational and informational assistant**. It is **NOT** a doctor, clinician, diagnostic authority, emergency service, or treatment provider.

**Primary Safety Objective:**

> Provide useful, evidence-grounded health information while reducing the risk that users misunderstand the system as a substitute for professional medical care.

---

## 2. Core Safety Principles

| ID | Principle | Detail | Classification |
|---|---|---|---|
| **SP-01** | **No Doctor Impersonation** | The system must never claim or imply that it is a licensed doctor or healthcare professional. | REQUIRED |
| **SP-02** | **No Definitive Diagnosis** | The system must not state that a user definitively has a disease based only on a conversational symptom description. | REQUIRED |
| **SP-03** | **Uncertainty Must Be Visible** | When evidence is incomplete, conflicting, or insufficient, the response must communicate uncertainty clearly. | REQUIRED |
| **SP-04** | **Safety Takes Priority** | If a direct and convenient answer would conflict with a safety rule, the safety rule takes priority. | REQUIRED |
| **SP-05** | **No Unsafe Medication Advice** | The system must not independently prescribe medication or provide unsafe individualized dosing. Medication-related requirements must be evaluated carefully and supported by authoritative sources. | REQUIRED |
| **SP-06** | **Encourage Professional Care** | When available information suggests that professional assessment may be appropriate, the system should clearly recommend seeking qualified healthcare. | REQUIRED |
| **SP-07** | **No False Reassurance** | The system must not reassure a user that a potentially serious situation is harmless when the available information does not support that conclusion. | REQUIRED |
| **SP-08** | **No Fabricated Evidence** | The system must never invent medical sources, citations, guidelines, or evidence. | REQUIRED |

### SP-02 — Language Examples

**Allowed style:**
> "These symptoms can occur with several conditions."

**Not allowed:**
> "You definitely have dengue."

---

## 3. Emergency / Urgent Situation Handling

The system shall include a safety classification stage **before** normal health-information generation.

**Conceptual Flow:**

```
User Message
     ↓
Safety Assessment
     ↓
Potentially Urgent?
├── Yes → Urgent / Safety Response
└── No  → Normal Retrieval + AI Response
```

The final emergency/urgent criteria **must be grounded in authoritative medical sources**. The system must not pretend that an unverified internal list is medically authoritative.

**Potential categories to investigate** (examples for research direction only — NOT the final project policy):

* Severe breathing difficulty
* Loss of consciousness
* Severe chest pain
* Uncontrolled bleeding
* Severe allergic reaction
* Stroke-like symptoms
* Seizure-related emergencies
* Severe poisoning
* Other clearly urgent presentations

| Item | Classification |
|---|---|
| Exact emergency/urgent detection criteria | **RESEARCH REQUIRED**: The universal Level A/B/C triage mapping and any symptom-to-urgency mapping must not be hardcoded without cited authoritative guidelines. Previous rules (e.g. fever >3 days) remain unapproved candidate examples only. |

---

## 4. Urgency Categories

The system may communicate a general urgency category to help users understand the potential significance of their situation. These categories are **not diagnoses**.

### Level A — General Information
The user appears to be seeking general health information without clear urgent warning signs.

### Level B — Professional Consultation
The information suggests that consultation with a qualified healthcare professional may be appropriate.

### Level C — Urgent Evaluation
The information contains warning signs that may warrant prompt or emergency medical evaluation.

| Item | Classification |
|---|---|
| Exact classification rules and thresholds for Level A / B / C | **RESEARCH REQUIRED**: Cannot be formalized until supported by authoritative clinical triage guidelines. |

---

## 5. Medication Safety

The initial system must **NOT**:

* Prescribe prescription medicines.
* Invent medication names.
* Recommend unsafe medication combinations.
* Give unsupported individualized dosing.
* Claim that a particular drug is definitely appropriate for the user.

Medication questions shall be handled conservatively. Where medication information is provided as general educational information, it **must** be grounded in approved knowledge-base sources.

| Item | Classification |
|---|---|
| Exact medication-policy boundaries | **RESEARCH REQUIRED**: Must distinguish: A. General info, B. Individual decisions, C. Prescription initiation/stopping/dose changes, D. OTC information. Exact evidence policy pending review of approved medication sources. |

---

## 6. Unsafe or Harmful Requests

The system must have defined behavior for requests that could cause medical harm. Such requests shall be **refused or redirected** rather than answered with dangerous instructions.

**Examples requiring policy research:**

* Intentionally dangerous medication use
* Overdose-related instructions
* Unsafe self-treatment procedures
* Requests to misuse prescription drugs
* Requests for dangerous medical procedures at home
* Requests seeking instructions that could cause serious harm

| Item | Classification |
|---|---|
| Exact taxonomy and handling rules for unsafe/harmful request categories | **RESEARCH REQUIRED**: Exact taxonomy requires medical safety literature backing. |

---

## 7. Self-Harm and Crisis-Related Health Requests

The project must include an explicit safety policy for messages indicating possible self-harm or immediate danger.

| Item | Classification |
|---|---|
| Exact response policy for self-harm / crisis messages | **RESEARCH REQUIRED**: Must keep dedicated safety pathway bypassing RAG, but must distinguish: emotional distress, suicidal thoughts, suicidal intent, suicidal plan/imminent danger, recent self-harm, poisoning/overdose. Exact thresholds pending guidance. |
| Verified local Bangladesh emergency and crisis resources | **VERIFIED**: 999 (National emergency service), 16263 (DGHS official health-info/doctor service), 09612-119911 (Kaan Pete Roi emotional-support and suicide-prevention helpline - NOT an emergency medical service, hours must be verified periodically). |

---

## 8. Retrieval Safety

RAG does not automatically make an answer safe. The retrieval process must adhere to the following rules:

| ID | Rule | Classification |
|---|---|---|
| **RS-01** | Retrieve only from approved sources. | REQUIRED |
| **RS-02** | Preserve source metadata through the retrieval pipeline. | REQUIRED |
| **RS-03** | Do not treat arbitrary web content as trusted medical evidence. | REQUIRED |
| **RS-04** | Indicate when relevant evidence cannot be found. | REQUIRED |
| **RS-05** | Do not fabricate citations. | REQUIRED |
| **RS-06** | When retrieval returns insufficient evidence, the system must not confidently invent an answer. | REQUIRED |

---

## 9. Conflicting Evidence

If trusted sources conflict, the system must not silently pretend there is agreement.

**Required behavior:**

1. Identify the conflict internally.
2. Prefer the more authoritative or current source according to documented source-priority rules.
3. Communicate uncertainty when the conflict is materially relevant to the user's question.

| Item | Classification |
|---|---|
| Source-priority system (ranking rules for conflicting authoritative sources) | **TO BE DECIDED**: Do NOT use a rigid Tier 1/2/3 hierarchy. Final rules remain TO BE DECIDED. Must use a SOURCE AUTHORITY FRAMEWORK based on: 1. Jurisdiction relevance, 2. Topic relevance, 3. Authority of issuing body, 4. Document specificity, 5. Publication/update date, 6. Clinical/public-health purpose. |

---

## 10. Source Attribution

Every knowledge-grounded medical answer must preserve enough metadata to identify the source material. 

**The system must never:**

* Fabricate a citation.
* Cite a document that was not retrieved.
* Claim a source says something it does not say.

| Item | Classification |
|---|---|
| Exact displayed citation format | TO BE DECIDED — Defined later in UI specification (`10-ui-specification.md`) and API specification (`08-api-specification.md`) |

---

## 11. AI Prompt Safety

The final AI system instructions (system prompt) must explicitly require:

* No doctor impersonation (SP-01)
* No definitive diagnosis (SP-02)
* Uncertainty communication (SP-03)
* No unsafe prescribing (SP-05)
* Evidence grounding (SP-08, RS-01–RS-06)
* Source-aware responses
* Escalation to professional care where appropriate (SP-06)
* Refusal of unsafe requests

| Item | Classification |
|---|---|
| Exact production system prompt | **TO BE DECIDED** — Will be specified after architecture and API documents are finalized |

---

## 12. Output Validation

Where technically practical, AI output should be checked before being shown to the user.

**Potential checks may include:**

* Missing source attribution
* Unsafe certainty language
* Prohibited prescription behavior
* Unsupported diagnosis statements
* Failure to include relevant safety messaging
* Malformed structured output

| Item | Classification |
|---|---|
| Exact output validation architecture and rule set | **TO BE DECIDED** |

---

## 13. Failure-Safe Behavior

If any critical component fails, the system must **fail conservatively**. It must not pretend that a normal AI-generated answer is evidence-grounded when retrieval did not occur.

**Critical failure scenarios:**

| Failure | Required Behavior | Classification |
|---|---|---|
| LLM unavailable | Fail safely, inform user | REQUIRED |
| Retrieval unavailable | Fail safely, do not fabricate grounded response | REQUIRED |
| Knowledge base unavailable | Fail safely, inform user | REQUIRED |
| Source metadata unavailable | Do not present response as source-grounded | REQUIRED |
| Safety classification unavailable | Default to conservative handling | REQUIRED |

| Item | Classification |
|---|---|
| Exact fallback message design and wording | **TO BE DECIDED** |

---

## 14. Privacy and Safety

Health questions may contain sensitive information. The following privacy-safety rules apply:

| Rule | Classification |
|---|---|
| Minimize collection of personal information | REQUIRED |
| Do not request identifying information unnecessarily | REQUIRED |
| Avoid exposing health information in logs | REQUIRED |
| Protect API credentials | REQUIRED |
| Document any stored conversation data | REQUIRED |
| Define retention policies before production use | REQUIRED |

Exact privacy and retention details are defined in the [Requirements Specification (Section 9)](file:///d:/my-ai-project/Dr.%20Md.%20Momenul%20Islam/docs/02-requirements.md) and will be expanded in later documentation.

---

## 15. Safety Hierarchy

When multiple requirements conflict, apply this priority order:

| Priority | Requirement |
|---|---|
| **1 (Highest)** | Human safety |
| **2** | Safety policy compliance |
| **3** | Evidence grounding |
| **4** | Accuracy and uncertainty communication |
| **5** | User usefulness |
| **6 (Lowest)** | Conversational convenience |

The system must **never** sacrifice a safety requirement merely to give a more satisfying answer.

---

## 16. Safety Evaluation

The project must include safety test categories covering at least:

| Category | Classification |
|---|---|
| Normal health questions | REQUIRED |
| Ambiguous symptom descriptions | REQUIRED |
| Possible urgent situations | REQUIRED |
| Medication requests | REQUIRED |
| Unsupported diagnoses | REQUIRED |
| Unsafe / harmful requests | REQUIRED |
| Conflicting sources | REQUIRED |
| No relevant retrieval found | REQUIRED |
| Missing citations | REQUIRED |
| LLM failure | REQUIRED |
| Retrieval failure | REQUIRED |
| Adversarial wording | REQUIRED |
| Bangla input | REQUIRED |
| English input | REQUIRED |
| Mixed Bangla / English input | REQUIRED |

Exact test cases will be defined in [`11-testing-strategy.md`](file:///d:/my-ai-project/Dr.%20Md.%20Momenul%20Islam/docs/11-testing-strategy.md).

---

## 17. Medical Evidence Requirement

Where this policy requires medical facts, emergency criteria, medication guidance, crisis information, or clinical recommendations, the final policy **must be based on authoritative evidence**.

**Do NOT** invent medical policy from general model knowledge. Mark unresolved items as **RESEARCH REQUIRED** and identify the type of authoritative source needed (e.g., WHO guidelines, national health authority protocols, peer-reviewed literature).

---

## 18. Explicit Safety Non-Goals

The project is **NOT** attempting to provide:

| Non-Goal | Classification |
|---|---|
| Clinical diagnosis | OUT OF SCOPE |
| Autonomous treatment | OUT OF SCOPE |
| Emergency dispatch | OUT OF SCOPE |
| Professional medical certification | OUT OF SCOPE |
| Clinical decision authority | OUT OF SCOPE |
| Guaranteed medical correctness | OUT OF SCOPE |

---

## 19. Governance Rule

Any future change that weakens any of the following must require **explicit review** of this safety policy and corresponding updates to the Requirements (`02-requirements.md`) and Testing (`11-testing-strategy.md`) documents:

* Safety boundaries
* Uncertainty handling
* Source grounding
* Emergency handling
* Privacy protections

**Do not silently weaken a safety requirement in code.**

---

## Pending Research Summary

| Item | Section | Required Source Type |
|---|---|---|
| Emergency / urgent detection criteria | A 3 | WHO, clinical emergency guidelines, national health protocols |
| Urgency classification rules (Level A/B/C) | A 4 | Authoritative clinical triage guidelines |
| Medication-policy boundaries | A 5 | Pharmaceutical and clinical guidelines |
| Unsafe/harmful request taxonomy | A 6 | Medical safety literature |
| Self-harm / crisis response policy | A 7 | Crisis intervention best practices |

## Pending Decisions Summary

| Item | Section |
|---|---|
| Source-priority system | A 9 |
| Displayed citation format | A 10 |
| Production system prompt | A 11 |
| Output validation architecture | A 12 |
| Fallback message design | A 13 |



## 20. Gate 3 Approved Governance Updates

The following principles were formally validated and merged via Gate 3 research (see gate-3-final-review.md and gate-3-governance-merge.md):

1. **System Identity:** The system is a health-information assistant, not a doctor or clinical decision-maker.
2. **Routing vs. Diagnosis:** Any probabilistic semantic screening is an engineering safeguard, not clinical triage or clinical diagnosis.
3. **LLM Authority Limits:** The LLM cannot independently establish diagnosis, clinical urgency, or medical truth.
4. **Explicit Uncertainty:** Uncertainty must be explicit. Ambiguous potentially high-risk inputs use their predefined conservative fallback; the system must not invent a clinical severity level.
5. **Self-Harm Policy:** Self-harm handling remains strictly conservative and must not claim clinical suicide-risk assessment.
6. **Medication Boundaries:** Medication-action boundaries remain explicit. The system cannot authorize or prescribe medication adjustments.
7. **Conflict Adjudication:** Source conflicts must not be delegated to the LLM as medical adjudication.
8. **Experimental Boundaries:** No research benchmark score is to be treated as clinical validation.
