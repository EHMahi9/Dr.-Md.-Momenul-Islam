# User Personas: Dr. Md. Momenul Islam

> **Governing Documents:** This document is derived from the approved [Project Charter](./00-project-charter.md), [Problem Statement](./01-problem-statement.md), [Requirements Specification](./02-requirements.md), and [Safety Policy](./03-safety-policy.md). For current system state, see [Current Implementation State](./13-current-implementation-state.md).
>
> **Purpose:** Define realistic users and stakeholders for the system to guide design, safety, and evaluation decisions.

---

## Persona Design Principles

All personas in this document follow these principles:

1. Personas describe **user needs and behavior**, not technical implementation.
2. Avoid unsupported demographic assumptions or statistics.
3. Avoid medical stereotypes.
4. Do not imply that any persona lacks access to healthcare unless evidence supports that claim.
5. Distinguish **primary users** from **secondary stakeholders**.
6. Explicitly identify **safety risks** where users may misunderstand AI output.

---

## Primary User Personas

---

### Persona 1 — General Health Information Seeker

| Field | Detail |
|---|---|
| **Role** | Primary User |
| **Description** | A general user in Bangladesh who wants to understand a health question before deciding whether professional medical care is necessary. |

**Typical Characteristics:**
* May have limited medical knowledge.
* May use a smartphone as the primary digital device.
* May search for health information using search engines, social media, or AI tools.
* May prefer Bangla, English, or a combination depending on the topic.
* May have difficulty interpreting technical medical terminology.

**Goals:**
* Understand what their symptoms or health concern might mean in general terms.
* Learn important warning signs.
* Understand when professional medical evaluation may be appropriate.
* Find trustworthy information without reading many disconnected sources.
* Receive understandable explanations.

**Pain Points:**
* Conflicting information from different online sources.
* Difficulty understanding medical terminology.
* Unverified social-media health advice.
* Difficulty determining which sources are trustworthy.
* Fear caused by reading worst-case medical information online.
* False reassurance from overly simplistic information.

**Safety Considerations:**
This persona may interpret confident AI output as professional medical advice. The interface must therefore communicate limitations and uncertainty clearly (SP-03, SP-07, FR-06).

**Relevant Requirements:**
FR-01, FR-02, FR-04, FR-05, FR-06, FR-07, FR-08, FR-09, FR-10

---

### Persona 2 — Bangla-First User

| Field | Detail |
|---|---|
| **Role** | Primary User |
| **Description** | A user who is more comfortable asking health questions in Bangla than in English. |

**Goals:**
* Ask questions naturally in Bangla.
* Understand medical information in clear Bangla.
* Avoid having to translate technical medical content manually.
* Receive source references that can be verified.

**Pain Points:**
* English-heavy medical information online.
* Technical medical vocabulary that lacks clear Bangla equivalents.
* Poor-quality Bangla health content.
* Risk of mistranslation altering medical meaning.

**Safety Considerations:**
Translation must not alter the medical meaning of important warning signs, uncertainty language, or safety instructions. The exact language-processing architecture is **TO BE DECIDED** (see FR-03).

**Relevant Requirements:**
FR-03, FR-06, FR-09, UI-05

---

### Persona 3 — English-First / Bilingual User

| Field | Detail |
|---|---|
| **Role** | Primary User |
| **Description** | A user who is comfortable using English medical terminology or switching naturally between Bangla and English. |

**Goals:**
* Ask detailed health questions using known medical terms.
* Receive evidence-grounded information with clear source attribution.
* Switch between Bangla and English naturally within the interface.

**Pain Points:**
* Fragmented health information across multiple sources.
* Difficulty comparing reliability of different sources.
* General-purpose AI answers that lack clear medical evidence grounding.

**Safety Considerations:**
Familiarity with English medical terms may lead this persona to expect a higher level of clinical precision than the system is designed to provide. The system must still clearly communicate its limitations (SP-01, SP-02, FR-06).

**Relevant Requirements:**
FR-01, FR-03, FR-04, FR-09

---

## Secondary User Personas

---

### Persona 4 — Caregiver / Family Member

| Field | Detail |
|---|---|
| **Role** | Secondary User |
| **Description** | A person seeking health information on behalf of another family member (e.g., a parent asking about a child, an adult child asking about a parent, a spouse asking about a partner). |

**Goals:**
* Understand general health information relevant to the family member's situation.
* Recognize warning signs that may apply to the person they are caring for.
* Understand when professional care may be appropriate.
* Communicate relevant information clearly to the family member or healthcare provider.

**Pain Points:**
* Uncertainty about the severity of another person's symptoms.
* Difficulty describing symptoms observed in someone else.
* Emotional stress when seeking health information for a loved one.

**Safety Considerations:**
* The system must not assume that the person asking the question is the patient.
* The response must avoid implying that the AI has examined the person in question.
* Urgency guidance (FR-08) is particularly important for this persona, as caregivers may need to make time-sensitive decisions about seeking professional care.

**Relevant Requirements:**
FR-02, FR-06, FR-07, FR-08, SR-06, SR-07

---

### Persona 5 — Student / Research User

| Field | Detail |
|---|---|
| **Role** | Secondary User |
| **Description** | A student, researcher, or technology learner using the system to explore how AI-assisted, evidence-grounded health information systems work. |

**Goals:**
* Understand the project's evidence-grounding and RAG approach.
* Inspect cited sources and evaluate their relevance.
* Learn about the system's limitations and safety architecture.
* Evaluate system responses for quality and safety.

**Pain Points:**
* Lack of transparency in how AI systems generate health information.
* Difficulty distinguishing AI-generated content from evidence-grounded content.

**Safety Considerations:**
Research or evaluation access must not weaken the safety constraints applied to normal users. The system should behave identically regardless of the user's intent (SP-04, SP-08).

**Relevant Requirements:**
FR-09, AI-03, SRC-01, SRC-02

---

## Non-User Stakeholder Personas

---

### Persona 6 — Healthcare Professional Reviewer

| Field | Detail |
|---|---|
| **Role** | Non-User Stakeholder (Reviewer) |
| **Description** | A qualified healthcare professional who may review the system's output, safety policy, evaluation methodology, or knowledge sources. This persona is a reviewer/stakeholder, not necessarily an active application user. |

**Goals:**
* Evaluate whether the medical sources used are appropriate and authoritative.
* Identify unsafe system behavior or incorrect medical information.
* Review safety boundaries and urgency classification logic.
* Suggest improvements to medical content and safety handling.

**Important Boundary:**
The project must **not** claim that a healthcare professional has validated the system unless such validation has actually occurred and is documented.

**Relevant Requirements:**
SR-03, SR-08, SRC-02, NFR-09

---

### Persona 7 — Project Developer / Maintainer

| Field | Detail |
|---|---|
| **Role** | Non-User Stakeholder (Builder) |
| **Description** | The software developer responsible for building, testing, documenting, and maintaining the application. |

**Goals:**
* Understand system behavior and architecture.
* Maintain and update the knowledge base.
* Keep safety policies consistent with implementation.
* Run tests and evaluation suites.
* Add features without violating safety requirements.

**Responsibilities:**
* Follow project documentation and governance rules.
* Protect API keys and secrets (PR-03).
* Maintain source metadata through the pipeline (SRC-04).
* Keep safety requirements traceable across code and documentation.
* Review any changes that affect safety policy (Safety Policy §19).

**Relevant Requirements:**
NFR-05, NFR-06, KB-01, KB-02, KB-03, KB-04, KB-05, KB-06, PR-03

---

## Accessibility / Context Considerations

The following considerations apply across all user personas and should inform interface and interaction design:

* Bangla and English language preferences.
* Mobile-first usage patterns.
* Different levels of digital literacy.
* Difficulty understanding medical terminology.
* Potentially stressful health situations affecting user patience and comprehension.
* Need for clear, visible source attribution.
* Need for clear urgency guidance.

Exact accessibility standards and UI requirements will be defined in [`10-ui-specification.md`](./10-ui-specification.md).

---

## Persona-to-Requirement Traceability Matrix

| Persona | Role | Relevant Requirements |
|---|---|---|
| General Health Information Seeker | Primary User | FR-01, FR-02, FR-04, FR-05, FR-06, FR-07, FR-08, FR-09, FR-10 |
| Bangla-First User | Primary User | FR-03, FR-06, FR-09, UI-05 |
| English-First / Bilingual User | Primary User | FR-01, FR-03, FR-04, FR-09 |
| Caregiver / Family Member | Secondary User | FR-02, FR-06, FR-07, FR-08, SR-06, SR-07 |
| Student / Research User | Secondary User | FR-09, AI-03, SRC-01, SRC-02 |
| Healthcare Professional Reviewer | Non-User Stakeholder | SR-03, SR-08, SRC-02, NFR-09 |
| Project Developer / Maintainer | Non-User Stakeholder | NFR-05, NFR-06, KB-01–KB-06, PR-03 |

> All requirement IDs have been verified against [`02-requirements.md`](./02-requirements.md).
